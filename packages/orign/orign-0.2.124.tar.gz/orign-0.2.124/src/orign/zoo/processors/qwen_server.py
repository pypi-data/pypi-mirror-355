import fcntl
import json
import os
import shutil
import time
import uuid
from dataclasses import dataclass
from typing import Any, List, Optional

from chatmux.convert import oai_to_qwen
from chatmux.openai import (
    ChatRequest,
    ChatResponse,
    CompletionChoice,
    Logprobs,
    ResponseMessage,
)
from nebulous import (
    Bucket,
    ContainerConfig,
    Message,
    Processor,
    V1EnvVar,
    is_allowed,
    processor,
)
from nebulous.config import GlobalConfig as NebuGlobalConfig

from orign import Adapter

setup_script = """
apt update
apt install -y git
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
pip uninstall -y xformers
pip3 install -U xformers --index-url https://download.pytorch.org/whl/cu126
pip install trl peft transformers bitsandbytes sentencepiece accelerate tiktoken qwen-vl-utils chatmux orign
pip install -e git+https://github.com/pbarker/unsloth-zoo.git#egg=unsloth_zoo
pip install -e git+https://github.com/pbarker/unsloth.git#egg=unsloth
"""

BASE_MODEL_ID = os.getenv("BASE_MODEL_ID", "unsloth/Qwen2.5-VL-32B-Instruct")


# --- LRU Disk Cache Management (Copied and Adapted from unsloth_trainer.py) ---
LRU_METADATA_FILE = (
    "/nebulous/cache/lru_disk_cache_qwen_server.json"  # Server-specific metadata
)
ADAPTER_CACHE_DIR_BASE = "/nebulous/cache/adapters"  # Shared with trainer
SFT_RUNS_DIR_BASE = (
    "./sft_runs_server_placeholder"  # Placeholder, server doesn't manage these directly
)
LRU_LOCK_FILE_QWEN = (
    "/nebulous/cache/lru_disk_cache_qwen_server.lock"  # Server-specific lock file
)

DEFAULT_MAX_ADAPTER_STORAGE_MB = float(
    os.getenv("MAX_ADAPTER_STORAGE_MB", 10 * 1024)
)  # 10 GB
DEFAULT_MAX_SFTRUN_STORAGE_MB = float(
    os.getenv("MAX_SFTRUN_STORAGE_MB", 1 * 1024)
)  # 1 GB (low, as server shouldn't store these)

# Global variable to hold loaded metadata
_lru_disk_metadata = {"adapters": [], "sft_runs": []}

# Note on Race Conditions:
# If multiple processes (e.g., different server instances or a trainer and a server)
# share the same ADAPTER_CACHE_DIR_BASE and potentially the same LRU_METADATA_FILE,
# proper file locking (e.g., using fcntl or a library like flufl.lock) would be
# essential around _load_lru_metadata and _save_lru_metadata to prevent metadata corruption.
# Using a server-specific metadata file here avoids direct metadata clashes with the trainer
# but they will still compete for disk space in ADAPTER_CACHE_DIR_BASE.


def _acquire_lock(lock_file_path: str) -> Optional[int]:
    lock_fd = os.open(lock_file_path, os.O_RDWR | os.O_CREAT | os.O_TRUNC)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fd
    except BlockingIOError:
        os.close(lock_fd)
        return None


def _release_lock(lock_fd: Optional[int]):
    if lock_fd is not None:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def _get_dir_size_mb(path_str: str) -> float:
    """Calculates the total size of a directory in megabytes."""
    total_size_bytes = 0
    if not os.path.exists(path_str):
        return 0.0
    for dirpath, _, filenames in os.walk(path_str):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                try:
                    total_size_bytes += os.path.getsize(fp)
                except OSError:
                    pass  # Ignore if file is removed during scan
    return total_size_bytes / (1024 * 1024)


def _load_lru_metadata():
    """Loads LRU metadata from the JSON file, with file locking."""
    global _lru_disk_metadata

    lock_fd = _acquire_lock(LRU_LOCK_FILE_QWEN)
    if lock_fd is None:
        print(
            f"[METRIC] [LRU Disk Cache] Warning: Could not acquire lock for loading {LRU_METADATA_FILE}. Using in-memory or potentially stale data."
        )
        if not _lru_disk_metadata or (
            _lru_disk_metadata.get("adapters") == []
            and _lru_disk_metadata.get("sft_runs") == []
        ):
            print(
                "[METRIC] [LRU Disk Cache] No in-memory LRU data, and lock failed. Initializing fresh."
            )
            _lru_disk_metadata = {"adapters": [], "sft_runs": []}
        return

    try:
        os.makedirs(os.path.dirname(LRU_METADATA_FILE), exist_ok=True)
        if os.path.exists(LRU_METADATA_FILE):
            try:
                with open(LRU_METADATA_FILE, "r") as f:
                    content = f.read()
                    if content.strip():
                        _lru_disk_metadata = json.loads(content)
                    else:
                        _lru_disk_metadata = {
                            "adapters": [],
                            "sft_runs": [],
                        }  # Initialize if empty
                if "adapters" not in _lru_disk_metadata:
                    _lru_disk_metadata["adapters"] = []
                if "sft_runs" not in _lru_disk_metadata:
                    _lru_disk_metadata["sft_runs"] = []
                # print(f"[LRU Disk Cache] Metadata loaded from {LRU_METADATA_FILE}")
            except json.JSONDecodeError:
                print(
                    f"[METRIC] [LRU Disk Cache] Warning: Could not decode metadata from {LRU_METADATA_FILE}. Starting fresh."
                )
                _lru_disk_metadata = {"adapters": [], "sft_runs": []}
        else:
            # print(f"[LRU Disk Cache] Metadata file not found at {LRU_METADATA_FILE}. Initializing fresh.")
            _lru_disk_metadata = {"adapters": [], "sft_runs": []}
    finally:
        _release_lock(lock_fd)


def _update_item_access(item_name: str, item_type: str, item_path: str):
    """Atomically updates or adds an item's access time and size in the LRU metadata."""
    func_start_time = time.time()
    global _lru_disk_metadata

    lock_fd = _acquire_lock(LRU_LOCK_FILE_QWEN)
    if lock_fd is None:
        print(
            f"[METRIC] [LRU Disk Cache] Warning: Could not acquire lock for updating {item_name}. Update skipped."
        )
        return

    try:
        # Load the latest metadata from disk
        load_meta_start_time = time.time()
        current_disk_metadata = {"adapters": [], "sft_runs": []}
        if os.path.exists(LRU_METADATA_FILE):
            try:
                with open(LRU_METADATA_FILE, "r") as f_read:
                    content = f_read.read()
                    if content.strip():
                        current_disk_metadata = json.loads(content)
                if "adapters" not in current_disk_metadata:
                    current_disk_metadata["adapters"] = []
                if "sft_runs" not in current_disk_metadata:
                    current_disk_metadata["sft_runs"] = []
            except json.JSONDecodeError:
                print(
                    f"[METRIC] [LRU Disk Cache] Warning: JSON decode error in _update_item_access for {item_name}. Initializing fresh."
                )
                current_disk_metadata = {"adapters": [], "sft_runs": []}  # Fallback

        _lru_disk_metadata = current_disk_metadata  # Operate on the fresh copy
        load_meta_duration = time.time() - load_meta_start_time
        if load_meta_duration > 0.001:  # Log if it takes more than 1ms
            print(
                f"[METRIC] [LRU Disk Cache] _update_item_access: Loading metadata took {load_meta_duration:.4f}s for {item_name}"
            )

        if item_type not in _lru_disk_metadata:
            _lru_disk_metadata[item_type] = []

        item_list = _lru_disk_metadata[item_type]
        found_item = None
        for item in item_list:
            if item.get("name") == item_name:
                found_item = item
                break

        current_size_mb = _get_dir_size_mb(item_path)
        current_time = int(time.time())

        if current_size_mb == 0 and not os.path.exists(item_path):
            if found_item:
                item_list.remove(found_item)
                print(
                    f"[METRIC] [LRU Disk Cache] Removed non-existent item '{item_name}' ({item_type}) from metadata."
                )
            # Save changes immediately
            save_meta_op_start_time = time.time()
            with open(LRU_METADATA_FILE, "w") as f_write:
                json.dump(_lru_disk_metadata, f_write, indent=4)
            save_meta_op_duration = time.time() - save_meta_op_start_time
            print(
                f"[METRIC] [LRU Disk Cache] _update_item_access: Saving metadata (item non-existent) for '{item_name}' took {save_meta_op_duration:.4f}s"
            )
            return

        if found_item:
            found_item["last_accessed_ts"] = current_time
            found_item["size_mb"] = current_size_mb
            found_item["path"] = item_path
            print(
                f"[METRIC] [LRU Disk Cache] Updated access for '{item_name}' ({item_type}), size: {current_size_mb:.2f} MB"
            )
        else:
            item_list.append(
                {
                    "name": item_name,
                    "path": item_path,
                    "size_mb": current_size_mb,
                    "last_accessed_ts": current_time,
                }
            )
            print(
                f"[METRIC] [LRU Disk Cache] Added new item to LRU: '{item_name}' ({item_type}), size: {current_size_mb:.2f} MB, path: {item_path}"
            )

        # Save changes immediately
        save_meta_op_start_time = time.time()
        with open(LRU_METADATA_FILE, "w") as f_write:
            json.dump(_lru_disk_metadata, f_write, indent=4)
        save_meta_op_duration = time.time() - save_meta_op_start_time
        print(
            f"[METRIC] [LRU Disk Cache] _update_item_access: Saving metadata (item added/updated) for '{item_name}' took {save_meta_op_duration:.4f}s"
        )

    except Exception as e:
        print(
            f"[METRIC] [LRU Disk Cache] Error during _update_item_access for {item_name}: {e}"
        )
    finally:
        _release_lock(lock_fd)
    func_duration = time.time() - func_start_time
    if func_duration > 0.01:  # Log if the whole function takes more than 10ms
        print(
            f"[METRIC] [LRU Disk Cache] Total _update_item_access for '{item_name}' ({item_type}) took {func_duration:.4f} seconds."
        )


def _ensure_storage_limits():
    """Ensures storage usage is within limits, evicting LRU items if necessary.
    This function performs an atomic read-modify-write on the metadata and FS.
    """
    func_start_time = time.time()
    global _lru_disk_metadata, state  # state is InferenceState for qwen_server

    lock_fd = _acquire_lock(LRU_LOCK_FILE_QWEN)
    if lock_fd is None:
        print(
            "[METRIC] [LRU Disk Cache] Warning: Could not acquire lock for _ensure_storage_limits. Operation skipped."
        )
        return

    try:
        # Load the very latest metadata from disk under lock
        current_disk_metadata = {"adapters": [], "sft_runs": []}
        if os.path.exists(LRU_METADATA_FILE):
            try:
                with open(LRU_METADATA_FILE, "r") as f_read:
                    content = f_read.read()
                    if content.strip():
                        current_disk_metadata = json.loads(content)
                if "adapters" not in current_disk_metadata:
                    current_disk_metadata["adapters"] = []
                if "sft_runs" not in current_disk_metadata:
                    current_disk_metadata["sft_runs"] = []
            except json.JSONDecodeError:
                print(
                    "[METRIC] [LRU Disk Cache] Warning: JSON decode error in _ensure_storage_limits. Initializing fresh."
                )
                current_disk_metadata = {"adapters": [], "sft_runs": []}

        _lru_disk_metadata = (
            current_disk_metadata  # Work with the fresh copy for this operation
        )

        max_adapter_storage_mb = float(
            os.getenv("MAX_ADAPTER_STORAGE_MB", DEFAULT_MAX_ADAPTER_STORAGE_MB)
        )
        max_sft_run_storage_mb = float(
            os.getenv("MAX_SFTRUN_STORAGE_MB", DEFAULT_MAX_SFTRUN_STORAGE_MB)
        )
        metadata_changed = False

        # --- Manage Adapters ---
        manage_adapters_start_time = time.time()
        adapters = sorted(
            _lru_disk_metadata.get("adapters", []),
            key=lambda x: x.get("last_accessed_ts", 0),  # type: ignore
        )
        current_adapter_size_mb = sum(item.get("size_mb", 0) for item in adapters)
        # print(f"[LRU Disk Cache] Current adapter storage: {current_adapter_size_mb:.2f} MB / {max_adapter_storage_mb:.2f} MB limit.")

        adapters_to_keep = []
        evicted_count = 0
        for item in adapters:
            item_name = item.get("name")
            item_path = item.get("path")
            item_size = item.get("size_mb", 0)

            if (
                current_adapter_size_mb <= max_adapter_storage_mb
                and item_path
                and os.path.exists(item_path)
            ):
                adapters_to_keep.append(item)
                continue

            if not item_path or not os.path.exists(item_path):
                if item_path:  # if path was defined, its size contributed, so subtract
                    current_adapter_size_mb -= item_size
                print(
                    f"[METRIC] [LRU Disk Cache] Evicting (metadata only, path missing): Adapter '{item_name}' from {item_path}"
                )
                evicted_count += 1
                metadata_changed = True
                continue

            # With the new hotswap logic, we should not delete an adapter from the model
            # as there is only one persistent adapter. We just evict from disk.
            if (
                item_name == state.currently_loaded_adapter
                and current_adapter_size_mb > max_adapter_storage_mb
            ):
                print(
                    f"[METRIC] [LRU Disk Cache] Cannot evict currently loaded adapter '{item_name}'. Skipping."
                )
                adapters_to_keep.append(item)
                continue

            if current_adapter_size_mb > max_adapter_storage_mb:
                print(
                    f"[METRIC] [LRU Disk Cache] Evicting adapter '{item_name}' (size: {item_size:.2f} MB, path: {item_path})"
                )
                try:
                    shutil.rmtree(item_path)
                    current_adapter_size_mb -= item_size
                    evicted_count += 1
                    metadata_changed = True
                except OSError as e:
                    print(
                        f"[METRIC] [LRU Disk Cache] Error deleting adapter directory {item_path}: {e}"
                    )
                    adapters_to_keep.append(item)
            else:  # Path exists, but we are now within budget
                adapters_to_keep.append(item)

        _lru_disk_metadata["adapters"] = sorted(
            adapters_to_keep,
            key=lambda x: x.get("last_accessed_ts", 0),  # type: ignore
            reverse=True,
        )
        if evicted_count > 0:
            print(
                f"[METRIC] [LRU Disk Cache] Evicted {evicted_count} adapters. Remaining adapter storage: {current_adapter_size_mb:.2f} MB."
            )
        manage_adapters_duration = time.time() - manage_adapters_start_time
        print(
            f"[METRIC] [LRU Disk Cache] Adapter storage management took {manage_adapters_duration:.2f} seconds."
        )

        # --- Manage SFT Runs (minimal for server) ---
        manage_sft_runs_start_time = time.time()
        sft_runs = sorted(
            _lru_disk_metadata.get("sft_runs", []),
            key=lambda x: x.get("last_accessed_ts", 0),  # type: ignore
        )
        current_sft_run_size_mb = sum(item.get("size_mb", 0) for item in sft_runs)

        sft_runs_to_keep = []
        evicted_sft_count = 0
        for item in sft_runs:
            item_name = item.get("name")
            item_path = item.get("path")
            item_size = item.get("size_mb", 0)

            if (
                current_sft_run_size_mb <= max_sft_run_storage_mb
                and item_path
                and os.path.exists(item_path)
            ):
                sft_runs_to_keep.append(item)
                continue

            if not item_path or not os.path.exists(item_path):
                if item_path:
                    current_sft_run_size_mb -= item_size
                evicted_sft_count += 1
                metadata_changed = True
                continue

            if current_sft_run_size_mb > max_sft_run_storage_mb:
                try:
                    shutil.rmtree(item_path)
                    current_sft_run_size_mb -= item_size
                    evicted_sft_count += 1
                    metadata_changed = True
                except OSError:
                    sft_runs_to_keep.append(item)
            else:
                sft_runs_to_keep.append(item)

        _lru_disk_metadata["sft_runs"] = sorted(
            sft_runs_to_keep,
            key=lambda x: x.get("last_accessed_ts", 0),  # type: ignore
            reverse=True,
        )
        manage_sft_runs_duration = time.time() - manage_sft_runs_start_time
        print(
            f"[METRIC] [LRU Disk Cache] SFT run storage management took {manage_sft_runs_duration:.2f} seconds."
        )

        save_meta_op_start_time = time.time()
        if metadata_changed or evicted_count > 0 or evicted_sft_count > 0:
            with open(LRU_METADATA_FILE, "w") as f_write:
                json.dump(_lru_disk_metadata, f_write, indent=4)
            # print(f"[LRU Disk Cache] Metadata (potentially) updated by _ensure_storage_limits.")
            save_meta_op_duration = time.time() - save_meta_op_start_time
            print(
                f"[METRIC] [LRU Disk Cache] Saving LRU metadata in _ensure_storage_limits took {save_meta_op_duration:.4f} seconds."
            )

    except Exception as e:
        print(f"[METRIC] [LRU Disk Cache] Error during _ensure_storage_limits: {e}")
    finally:
        _release_lock(lock_fd)
    func_duration = time.time() - func_start_time
    print(
        f"[METRIC] [LRU Disk Cache] Total _ensure_storage_limits execution time: {func_duration:.2f} seconds."
    )


# --- End LRU Disk Cache Management ---


def init():
    init_start_time = time.time()
    import gc
    import os

    from unsloth import FastVisionModel  # type: ignore # isort: skip
    import torch  # type: ignore
    from nebulous import Cache  # type: ignore
    from peft import LoraConfig, PeftModel  # type: ignore
    from unsloth_zoo.peft_utils import get_peft_regex  # type: ignore

    if "state" in globals():  # <-- already loaded by an earlier worker
        print("state already loaded by an earlier worker")
        return

    gc.collect()
    torch.cuda.empty_cache()

    PERSISTENT_INFERENCE_ADAPTER = "persistent_inference_adapter"

    # os.environ.setdefault("MAX_PIXELS", "100352")

    @dataclass
    class InferenceState:
        base_model: PeftModel
        model_processor: Any
        base_model_id: str
        cache: Cache
        currently_loaded_adapter: Optional[str]
        persistent_adapter_name: str
        adapter_versions: dict  # maps adapter_name -> last_loaded_updated_at

    print("loading model...")
    print("--- nvidia-smi before load ---")
    os.system("nvidia-smi")
    print("--- end nvidia-smi before load ---")
    base_model_load_start_time = time.time()
    base_model, model_processor = FastVisionModel.from_pretrained(
        BASE_MODEL_ID,
        load_in_4bit=False,
        # use_fast=True,
        dtype=torch.bfloat16,
        max_seq_length=32_768,
    )
    print(
        f"[METRIC] Loaded base model and tokenizer in {time.time() - base_model_load_start_time:.2f} seconds"
    )

    print("\nApplying initial PEFT setup with FastVisionModel.get_peft_model...")
    peft_setup_start_time = time.time()
    plumbed_model: PeftModel = FastVisionModel.get_peft_model(
        base_model,
        r=64,  # These values are arbitrary for the container, they get overwritten by hotswap
        lora_alpha=128,
        lora_dropout=0.0,
        bias="none",
        finetune_vision_layers=True,  # enable all layers for potential hotswaps
        finetune_language_layers=True,
    )
    print(f"Type of model after get_peft_model: {type(plumbed_model)}")
    print(
        f"[METRIC] Initial PEFT setup (get_peft_model) took {time.time() - peft_setup_start_time:.2f} seconds."
    )

    if "default" in plumbed_model.peft_config:
        target_modules_pattern = plumbed_model.peft_config["default"].target_modules
        print(
            "Captured initial target_modules pattern from 'default' adapter's config."
        )
        plumbed_model.delete_adapter("default")
        print("Deleted 'default' adapter.")
        plumbed_model.active_adapter = None
    else:
        # Fallback if unsloth changes the 'default' name
        print(
            "Warning: 'default' adapter not found. Generating target_modules pattern manually."
        )
        target_modules_pattern = get_peft_regex(
            base_model,
            finetune_vision_layers=True,
            finetune_language_layers=True,
            finetune_attention_modules=True,  # Be comprehensive
            finetune_mlp_modules=True,
        )

    # Add the single persistent adapter for inference
    persistent_lora_config = LoraConfig(
        r=64,  # placeholder
        lora_alpha=128,  # placeholder
        lora_dropout=0.0,
        bias="none",
        target_modules=target_modules_pattern,
    )
    plumbed_model.add_adapter(PERSISTENT_INFERENCE_ADAPTER, persistent_lora_config)
    plumbed_model.active_adapter = None  # Deactivate by default
    print(f"Added and deactivated persistent adapter '{PERSISTENT_INFERENCE_ADAPTER}'.")

    print("--- nvidia-smi after load ---")
    os.system("nvidia-smi")
    print("--- end nvidia-smi after load ---")

    global state
    state = InferenceState(
        base_model=plumbed_model,
        model_processor=model_processor,
        base_model_id=BASE_MODEL_ID,
        cache=Cache(),
        currently_loaded_adapter=None,
        persistent_adapter_name=PERSISTENT_INFERENCE_ADAPTER,
        adapter_versions={},
    )

    # --- LRU Disk Cache Init ---
    lru_init_start_time = time.time()
    _load_lru_metadata()
    _ensure_storage_limits()  # Perform initial cleanup if needed
    print(
        f"[METRIC] LRU Disk Cache init (_load_lru_metadata & _ensure_storage_limits) took {time.time() - lru_init_start_time:.2f} seconds."
    )
    # --- End LRU Disk Cache Init ---

    # --- after we finish creating the state object, call FastVisionModel.for_inference **once** so kernels are compiled without merging LoRA weights on every request.
    FastVisionModel.for_inference(plumbed_model)

    print(
        f"[METRIC] Total init() function execution time: {time.time() - init_start_time:.2f} seconds."
    )


def smart_adapter_loading_for_inference(
    model: Any,  # PeftModel
    adapter_to_load: Any,  # V1Adapter
    adapter_name: str,
    bucket: Any,
) -> bool:
    """
    Manages the single persistent adapter by hotswapping weights.
    Returns True if weights were changed, False otherwise.
    """
    func_start_time = time.time()
    from peft.utils.hotswap import hotswap_adapter  # type: ignore

    global state

    print(f"\n[METRIC] [Hotswap] Managing weights for '{adapter_name}'")

    # --- Extra debug context ---
    try:
        print(
            f"[DEBUG] currently_loaded_adapter={state.currently_loaded_adapter}  adapter_versions={state.adapter_versions.get(adapter_name)}  new_updated_at={getattr(adapter_to_load.metadata,'updated_at',None)}"
        )
    except Exception:
        pass

    # Check if we already have this adapter loaded with the same version.
    if state.currently_loaded_adapter == adapter_name:
        prev_ts = state.adapter_versions.get(adapter_name)
        current_ts = getattr(adapter_to_load.metadata, "updated_at", None)
        if prev_ts is not None and current_ts == prev_ts:
            print(
                f"[METRIC] [Hotswap] Adapter '{adapter_name}' is already loaded with same version (updated_at={current_ts}). No action needed."
            )
            return False
        else:
            print(
                f"[METRIC] [Hotswap] Adapter '{adapter_name}' version changed (prev={prev_ts}, new={current_ts}). Will reload."
            )

    # --- Get weights on disk, downloading if necessary ---
    # This logic replaces the main part of _load_adapter_traditionally
    persistent_adapter_path = os.path.join(ADAPTER_CACHE_DIR_BASE, adapter_name)

    # Determine if adapter weights are already present locally. The trainer may
    # save the actual LoRA weights either directly inside `persistent_adapter_path`
    #  (…/adapters/<adapter_name>/adapter_config.json)
    # or one level deeper (…/adapters/<adapter_name>/<adapter_name>/adapter_config.json).
    def _find_local_weight_dir(base_dir: str) -> Optional[str]:
        """Return the directory that contains adapter_config.json if it exists, else None."""
        candidate = os.path.join(base_dir, "adapter_config.json")
        if os.path.exists(candidate):
            return base_dir
        # check one-level sub-dirs for backwards-compatibility
        if os.path.isdir(base_dir):
            for entry in os.listdir(base_dir):
                sub = os.path.join(base_dir, entry)
                if os.path.isdir(sub) and os.path.exists(
                    os.path.join(sub, "adapter_config.json")
                ):
                    return sub
        return None

    local_weight_dir = _find_local_weight_dir(persistent_adapter_path)

    if local_weight_dir is None:
        print(
            f"[METRIC] [Hotswap] Weights for '{adapter_name}' not found locally under '{persistent_adapter_path}'. Downloading…"
        )
        download_start_time = time.time()
        try:
            # Clean directory before downloading to prevent issues with stale files
            if os.path.exists(persistent_adapter_path):
                shutil.rmtree(persistent_adapter_path)
            os.makedirs(persistent_adapter_path, exist_ok=True)

            bucket.copy(adapter_to_load.model_uri, persistent_adapter_path)
            print(
                f"[METRIC] [Hotswap] Downloaded in {time.time() - download_start_time:.2f} seconds"
            )
            # Update LRU metadata for the newly downloaded adapter
            _update_item_access(adapter_name, "adapters", persistent_adapter_path)
        except Exception as e_download:
            print(
                f"[METRIC] [Hotswap] Error downloading adapter {adapter_name} from {adapter_to_load.model_uri}: {e_download}"
            )
            raise
    else:
        print(
            f"[METRIC] [Hotswap] Found cached weights for '{adapter_name}' (dir: '{local_weight_dir}')."
        )
        # Update access time for the cached item
        _update_item_access(adapter_name, "adapters", persistent_adapter_path)

    # Snapshot the directory we believe holds the weights (if any) for troubleshooting.
    if local_weight_dir:
        try:
            print(
                f"[DEBUG] Contents of '{local_weight_dir}': {os.listdir(local_weight_dir)}"
            )
        except Exception as e_ls:
            print(f"[DEBUG] Could not list contents of {local_weight_dir}: {e_ls}")

    # Determine the directory that actually holds adapter_config.json after the potential download.
    # (download may have populated either persistent_adapter_path or its child directory)
    local_weight_dir = _find_local_weight_dir(persistent_adapter_path)
    if local_weight_dir is None:
        raise FileNotFoundError(
            f"adapter_config.json not found in '{persistent_adapter_path}' nor its first-level sub-dirs after download."
        )

    print(
        f"[METRIC] [Hotswap] Hotswapping weights from '{local_weight_dir}' into persistent adapter '{state.persistent_adapter_name}'"
    )
    hotswap_op_start_time = time.time()
    try:
        # Ensure the persistent adapter is active before hotswapping into it.
        # This is a requirement for the hotswap function.
        if model.active_adapter != state.persistent_adapter_name:
            print(
                f"  > Activating '{state.persistent_adapter_name}' before hotswapping."
            )
            model.set_adapter(state.persistent_adapter_name)

        hotswap_adapter(model, local_weight_dir, state.persistent_adapter_name)

        state.currently_loaded_adapter = adapter_name
        # Record version timestamp
        state.adapter_versions[adapter_name] = getattr(
            adapter_to_load.metadata, "updated_at", None
        )
        print(
            f"[METRIC] [Hotswap] Successfully hotswapped weights for '{adapter_name}' in {time.time() - hotswap_op_start_time:.2f}s."
        )

        # Debug: confirm adapter activation / environment right after hotswap
        try:
            print(
                f"[DEBUG] After hotswap: model.active_adapter={model.active_adapter},  persistent_adapter_name={state.persistent_adapter_name}"
            )
        except Exception:
            pass

    except Exception as e:
        print(f"[METRIC] [Hotswap] Hotswap operation failed: {e}")
        # If hotswap fails, reset the state to be safe
        state.currently_loaded_adapter = None
        raise

    print(
        f"[METRIC] [Hotswap] Total smart_adapter_loading for '{adapter_name}' took {time.time() - func_start_time:.2f}s"
    )
    return True


def infer_qwen_vl(
    message: Message[ChatRequest],
) -> ChatResponse:
    overall_inference_start_time = time.time()
    from qwen_vl_utils import process_vision_info  # type: ignore
    from unsloth import FastVisionModel  # type: ignore

    global state
    print("NEW STUFFSS $$$$$")

    print("message", message)
    os.system("nvidia-smi")

    training_request = message.content
    if not training_request:
        raise ValueError("No training request provided")

    # print("content", message.content)

    container_config = ContainerConfig.from_env()
    print("container_config", container_config)

    content = message.content
    if not content:
        raise ValueError("No content provided")

    load_adapter = content.model != "" and content.model != BASE_MODEL_ID
    print("load_adapter", load_adapter)

    adapter_management_start_time = time.time()
    if load_adapter:
        model_parts = content.model.split("/")
        if len(model_parts) == 2:
            namespace = model_parts[0]
            name = model_parts[1]
        else:
            namespace = message.handle
            name = model_parts[0]

        print("checking for adapter", f"'{namespace}/{name}'")
        adapters = Adapter.get(namespace=namespace, name=name, api_key=message.api_key)
        if adapters:
            adapter_to_load = adapters[0]
            print("found adapter info:", adapter_to_load)

            if not is_allowed(
                adapter_to_load.metadata.owner, message.user_id, message.orgs
            ):
                raise ValueError("You are not allowed to use this adapter")

            if not adapter_to_load.base_model == BASE_MODEL_ID:
                raise ValueError(
                    "The base model of the adapter does not match the model you are trying to use"
                )

            # Use smart adapter management
            bucket = Bucket()
            adapter_was_loaded = smart_adapter_loading_for_inference(
                state.base_model, adapter_to_load, content.model, bucket
            )

            if adapter_was_loaded:
                print(f"Adapter {content.model} weights were hotswapped successfully.")
            else:
                print(
                    f"Adapter {content.model} was already loaded - no hotswap needed."
                )

        else:
            raise ValueError(f"Adapter '{content.model}' not found")
        print(
            f"[METRIC] [Adapter Management Block] Adapter loading/checking total time: {time.time() - adapter_management_start_time:.2f} seconds"
        )
    else:
        print(
            f"[METRIC] [Adapter Management Block] No adapter loading requested. Time: {time.time() - adapter_management_start_time:.2f}s"
        )

    # --- Activate or Deactivate the Persistent Adapter ---
    print("\n[AdapterCycle] Managing persistent adapter state for request...")
    if load_adapter:
        # An adapter is requested, so ensure the persistent adapter is active.
        # The hotswapping logic should have already loaded the correct weights.
        if state.base_model.active_adapter != state.persistent_adapter_name:
            print(
                f"[METRIC] [AdapterCycle] Activating persistent adapter: '{state.persistent_adapter_name}'"
            )
            state.base_model.set_adapter(state.persistent_adapter_name)
        else:
            print(
                f"[METRIC] [AdapterCycle] Persistent adapter '{state.persistent_adapter_name}' is already active."
            )
    else:
        # Base model inference requested. Deactivate the persistent adapter.
        if state.base_model.active_adapter is not None:
            print(
                "[METRIC] [AdapterCycle] Deactivating all adapters for base model operation."
            )
            state.base_model.active_adapter = None
        else:
            print(
                "[METRIC] [AdapterCycle] No adapter is active, proceeding with base model operation."
            )

    active_after_manipulation = "N/A"
    try:
        active_after_manipulation = state.base_model.active_adapter
    except Exception as e_active_after:
        print(
            f"Note: Could not get active_adapter after manipulation: {e_active_after}"
        )
        pass
    print(f"Active adapter after explicit manipulation: {active_after_manipulation}")

    # NOTE: Removed per-request FastVisionModel.for_inference call to avoid
    # unintentionally merging LoRA weights into the backbone. The model was
    # prepared for inference once during `init()`.
    print("skipping per-request FastVisionModel.for_inference() to avoid LoRA merge")

    content_dict = content.model_dump()
    messages_oai = content_dict["messages"]
    messages = oai_to_qwen(messages_oai)

    # Preparation for inference
    # print("preparing inputs using messages: ", messages)
    input_prep_start_time = time.time()
    text = state.model_processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    # print("text: ", text)
    # print("processing vision info: ", messages)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = state.model_processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to("cuda")
    # print("inputs", inputs)
    print(
        f"[METRIC] Inputs prepared in {time.time() - input_prep_start_time:.2f} seconds"
    )

    # Inference: Generation of the output
    model_generate_start_time = time.time()

    # Decide which model object to call .generate() on
    if state.base_model.active_adapter is None:
        # No adapter active – use the underlying (non-PEFT) model to avoid KeyError
        underlying = getattr(state.base_model, "base_model", state.base_model)
        # LoraModel often stores the real model in its .model attribute
        if hasattr(underlying, "model"):
            model_to_generate_with = underlying.model
        else:
            model_to_generate_with = underlying
        print(
            "[DEBUG] No adapter active ➜ using underlying model for generation:",
            type(model_to_generate_with),
        )
    else:
        model_to_generate_with = (
            state.base_model
        )  # Adapter (persistent or hot-swapped) is active
        print(
            "[DEBUG] Adapter active ➜ using PeftModel for generation, active_adapter=",
            state.base_model.active_adapter,
        )

    # More introspection
    try:
        print(
            f"[DEBUG] Final model_to_generate_with class={type(model_to_generate_with)}"
        )
    except Exception:
        pass

    if model_to_generate_with is None:
        raise RuntimeError("Could not determine which model to use for generation.")

    generated_ids = None
    try:
        generated_ids = model_to_generate_with.generate(
            **inputs, max_new_tokens=content.max_tokens
        )
    except KeyError as ke:
        print(
            f"[WARN] generate() raised {ke}. active_adapter={state.base_model.active_adapter}. Will retry with underlying HF model."
        )
        try:
            fallback_underlying = getattr(
                state.base_model, "base_model", state.base_model
            )
            if hasattr(fallback_underlying, "model"):
                fallback_underlying = fallback_underlying.model
            print(
                f"[DEBUG] Retrying generate() on fallback_underlying class={type(fallback_underlying)}"
            )
            generated_ids = fallback_underlying.generate(
                **inputs, max_new_tokens=content.max_tokens
            )
        except Exception as e_fallback:
            print(f"[ERROR] Fallback generate also failed: {e_fallback}")
            raise
    except Exception as e_gen:
        print(f"[ERROR] Unexpected exception from generate(): {e_gen}")
        raise

    model_generate_duration = time.time() - model_generate_start_time
    print(f"[METRIC] Raw model.generate() took {model_generate_duration:.2f} seconds")

    decode_start_time = time.time()
    generated_ids_trimmed = [
        out_ids[len(in_ids) :]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = state.model_processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    decode_duration = time.time() - decode_start_time
    print(f"[METRIC] Decoding generated IDs took {decode_duration:.2f} seconds")

    print("output_text", output_text)
    print(
        f"[METRIC] Total generation (generate + decode) took {model_generate_duration + decode_duration:.2f} seconds"
    )

    # Build the Pydantic model, referencing your enumerations and classes
    response_build_start_time = time.time()
    response = ChatResponse(
        id=str(uuid.uuid4()),
        created=int(time.time()),
        model=content.model,
        object="chat.completion",
        choices=[
            CompletionChoice(
                index=0,
                finish_reason="stop",
                message=ResponseMessage(  # type: ignore
                    role="assistant", content=output_text[0]
                ),
                logprobs=Logprobs(content=[]),
            )
        ],
        service_tier=None,
        system_fingerprint=None,
        usage=None,
    )
    print(
        f"[METRIC] Total time: {time.time() - overall_inference_start_time:.2f} seconds"
    )
    print(
        f"[METRIC] Response object build time: {time.time() - response_build_start_time:.4f} seconds"
    )
    print(
        f" [METRIC] === Overall infer_qwen_vl request processed in {time.time() - overall_inference_start_time:.2f} seconds === "
    )

    return response


def QwenVLServer(
    platform: str = "runpod",
    accelerators: List[str] = ["1:A100_SXM"],
    model: str = "unsloth/Qwen2.5-VL-32B-Instruct",
    image: str = "ghcr.io/agentsea/orign/unsloth-infer:e030adf",  # "public.ecr.aws/d8i6n0n1/orign/unsloth-server:e030adf",  # "us-docker.pkg.dev/agentsea-dev/orign/unsloth-infer:latest" # "ghcr.io/agentsea/orign/unsloth-infer:5c28777",
    namespace: Optional[str] = None,
    env: Optional[List[V1EnvVar]] = None,
    config: Optional[NebuGlobalConfig] = None,
    hot_reload: bool = True,
    debug: bool = False,
    min_replicas: int = 1,
    max_replicas: int = 4,
    name: Optional[str] = None,
    wait_for_healthy: bool = True,
) -> Processor[ChatRequest, ChatResponse]:
    if env:
        env.append(V1EnvVar(key="BASE_MODEL_ID", value=model))
    else:
        env = [
            V1EnvVar(key="BASE_MODEL_ID", value=model),
        ]
    decorate = processor(
        image=image,
        # setup_script=setup_script,
        accelerators=accelerators,
        platform=platform,
        init_func=init,
        env=env,
        namespace=namespace,
        config=config,
        hot_reload=hot_reload,
        debug=debug,
        min_replicas=min_replicas,
        max_replicas=max_replicas,
        name=name,
        wait_for_healthy=wait_for_healthy,
    )
    return decorate(infer_qwen_vl)
