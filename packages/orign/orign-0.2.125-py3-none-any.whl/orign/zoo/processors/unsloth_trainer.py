import fcntl  # Added for file locking
import gc
import json
import os
import secrets
import shutil
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from nebulous import Message, Processor, processor
from nebulous.config import GlobalConfig as NebuGlobalConfig
from nebulous.containers.models import V1EnvVar
from nebulous.errors import RetriableError
from nebulous.processors.models import (
    V1Scale,
    V1ScaleDown,
    V1ScaleUp,
    V1ScaleZero,
)
from pydantic import BaseModel

from orign import V1TrainingStatus, find_latest_checkpoint

BASE_MODEL_ID = "unsloth/Qwen2.5-VL-32B-Instruct"
ADAPTER_DIR = "/nebulous/cache/adapters"
MAX_LOADED_ADAPTERS = 10

PERSISTENT_ADAPTER_NAME = "active_training_adapter"

# --- LRU Disk Cache Management ---
LRU_METADATA_FILE = "/nebulous/cache/lru_disk_cache.json"
ADAPTER_CACHE_DIR_BASE = ADAPTER_DIR
SFT_RUNS_DIR_BASE = "./runs"  # Relative to CWD
LRU_LOCK_FILE = "/nebulous/cache/lru_disk_cache.lock"  # Lock file for metadata

DEFAULT_MAX_ADAPTER_STORAGE_MB = 100 * 1024  # 100 GB
DEFAULT_MAX_SFTRUN_STORAGE_MB = 100 * 1024  # 100 GB

# Global variable to hold loaded metadata
_lru_disk_metadata = {"adapters": [], "sft_runs": []}
_lock_fd = None  # Global to hold lock file descriptor if needed, though prefer local


def _acquire_lock(lock_file_path: str) -> Optional[int]:
    lock_fd = os.open(lock_file_path, os.O_RDWR | os.O_CREAT | os.O_TRUNC)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # print(f"Acquired lock on {lock_file_path}")
        return lock_fd
    except BlockingIOError:
        # print(f"Could not acquire lock on {lock_file_path}, already locked.")
        os.close(lock_fd)
        return None


def _release_lock(lock_fd: Optional[int]):
    if lock_fd is not None:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
        # print("Released lock")


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

    lock_fd = _acquire_lock(LRU_LOCK_FILE)
    if lock_fd is None:
        print(
            f"Warning: Could not acquire lock for loading {LRU_METADATA_FILE}. Using in-memory or potentially stale data."
        )
        # Decide on fallback: either use current _lru_disk_metadata or reset it.
        # For safety, if we can't lock to read, assume we don't know the true state.
        # However, an existing in-memory _lru_disk_metadata might be from a previous successful load.
        # Let's proceed with current in-memory state if lock fails, but log verbosely.
        if not _lru_disk_metadata or (
            _lru_disk_metadata.get("adapters") == []
            and _lru_disk_metadata.get("sft_runs") == []
        ):
            print(
                "No in-memory LRU data, and lock failed. Initializing fresh for safety."
            )
            _lru_disk_metadata = {"adapters": [], "sft_runs": []}
        return

    try:
        os.makedirs(os.path.dirname(LRU_METADATA_FILE), exist_ok=True)
        if os.path.exists(LRU_METADATA_FILE):
            try:
                with open(LRU_METADATA_FILE, "r") as f:
                    # Ensure file is not empty before loading
                    content = f.read()
                    if content.strip():
                        _lru_disk_metadata = json.loads(content)
                    else:
                        _lru_disk_metadata = {"adapters": [], "sft_runs": []}
                # Ensure basic structure
                if "adapters" not in _lru_disk_metadata:
                    _lru_disk_metadata["adapters"] = []
                if "sft_runs" not in _lru_disk_metadata:
                    _lru_disk_metadata["sft_runs"] = []
                # print(f"LRU metadata loaded from {LRU_METADATA_FILE}")
            except json.JSONDecodeError:
                print(
                    f"Warning: Could not decode LRU metadata from {LRU_METADATA_FILE}. Starting fresh."
                )
                _lru_disk_metadata = {"adapters": [], "sft_runs": []}
        else:
            # print(f"LRU metadata file not found at {LRU_METADATA_FILE}. Initializing fresh.")
            _lru_disk_metadata = {"adapters": [], "sft_runs": []}
    finally:
        _release_lock(lock_fd)


def _update_item_access(item_name: str, item_type: str, item_path: str):
    """Updates or adds an item's access time and size in the LRU metadata.
    Locking is handled by _load_lru_metadata and _save_lru_metadata.
    This function assumes _lru_disk_metadata is the current, authoritative copy.
    """
    update_item_access_start_time = time.time()
    global _lru_disk_metadata

    # It's better to acquire a lock for the read-modify-write cycle here
    # if _load_lru_metadata itself isn't called immediately before.
    # Let's refine: _update_item_access should be atomic.

    lock_fd = _acquire_lock(LRU_LOCK_FILE)
    if lock_fd is None:
        print(
            f"Warning: Could not acquire lock for updating LRU item {item_name}. Update skipped."
        )
        return

    try:
        # Load the latest metadata from disk to avoid operating on a stale in-memory version
        # This mimics _load_lru_metadata's core file reading logic but within an existing lock
        temp_metadata = {"adapters": [], "sft_runs": []}  # Default if file is empty/new
        if os.path.exists(LRU_METADATA_FILE):
            try:
                with open(LRU_METADATA_FILE, "r") as f_read:
                    content = f_read.read()
                    if content.strip():  # Check if file is not empty
                        temp_metadata = json.loads(content)
                if "adapters" not in temp_metadata:
                    temp_metadata["adapters"] = []
                if "sft_runs" not in temp_metadata:
                    temp_metadata["sft_runs"] = []
            except json.JSONDecodeError:
                print(
                    f"Warning: JSON decode error during _update_item_access for {item_name}. Using fresh metadata for this op."
                )
                # If decode fails, we might overwrite. This is a risk.
                # Or, we could choose to not proceed with the update.
                # For now, let's proceed assuming we'll save a corrected version.
                temp_metadata = {"adapters": [], "sft_runs": []}  # Fallback

        _lru_disk_metadata = (
            temp_metadata  # Update global with what we just read under lock
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

        if current_size_mb == 0 and not os.path.exists(
            item_path
        ):  # Item effectively gone
            if found_item:
                item_list.remove(found_item)
                print(
                    f"Removed non-existent item '{item_name}' ({item_type}) from LRU metadata."
                )
            # Save immediately after modification
            save_op_start_time = time.time()
            with open(LRU_METADATA_FILE, "w") as f_write:
                json.dump(_lru_disk_metadata, f_write, indent=4)
            save_duration = time.time() - save_op_start_time
            print(
                f"[METRIC] _update_item_access: Saving metadata (item non-existent) for '{item_name}' took {save_duration:.4f}s"
            )
            return  # Lock will be released in finally

        if found_item:
            found_item["last_accessed_ts"] = current_time
            found_item["size_mb"] = current_size_mb
            found_item["path"] = item_path
            print(
                f"Updated LRU access for '{item_name}' ({item_type}), size: {current_size_mb:.2f} MB"
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
                f"Added new item to LRU: '{item_name}' ({item_type}), size: {current_size_mb:.2f} MB, path: {item_path}"
            )

        # Save immediately after modification
        save_op_start_time = time.time()
        with open(LRU_METADATA_FILE, "w") as f_write:
            json.dump(_lru_disk_metadata, f_write, indent=4)
        save_duration = time.time() - save_op_start_time
        print(
            f"[METRIC] _update_item_access: Saving metadata (item updated/added) for '{item_name}' took {save_duration:.4f}s"
        )

    except Exception as e:
        print(f"Error during _update_item_access for {item_name}: {e}")
    finally:
        _release_lock(lock_fd)
    update_item_access_duration = time.time() - update_item_access_start_time
    # Limit printing for very fast operations to avoid log spam
    if update_item_access_duration > 0.01:
        print(
            f"[METRIC] Total _update_item_access for '{item_name}' ({item_type}) took {update_item_access_duration:.4f} seconds."
        )


def _ensure_storage_limits():
    """Ensures storage usage is within limits, evicting LRU items if necessary.
    This function performs a read-modify-write cycle on the metadata and file system.
    """
    ensure_limits_start_time = time.time()
    global _lru_disk_metadata, state

    lock_fd = _acquire_lock(LRU_LOCK_FILE)
    if lock_fd is None:
        print(
            "Warning: Could not acquire lock for _ensure_storage_limits. Operation skipped."
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
                    "Warning: JSON decode error in _ensure_storage_limits. Initializing fresh for this op."
                )
                # Fallback to an empty structure if decode fails, to prevent operating on corrupted data
                current_disk_metadata = {"adapters": [], "sft_runs": []}

        _lru_disk_metadata = current_disk_metadata  # Work with the fresh copy

        max_adapter_storage_mb = float(
            os.getenv("MAX_ADAPTER_STORAGE_MB", DEFAULT_MAX_ADAPTER_STORAGE_MB)
        )
        max_sft_run_storage_mb = float(
            os.getenv("MAX_SFTRUN_STORAGE_MB", DEFAULT_MAX_SFTRUN_STORAGE_MB)
        )

        # --- Manage Adapters ---
        manage_adapters_start_time = time.time()
        adapters = sorted(
            _lru_disk_metadata.get("adapters", []),
            key=lambda x: x.get("last_accessed_ts", 0),  # type: ignore
        )
        current_adapter_size_mb = sum(item.get("size_mb", 0) for item in adapters)
        # print(f"Current adapter storage: {current_adapter_size_mb:.2f} MB / {max_adapter_storage_mb:.2f} MB limit.")

        adapters_to_keep = []
        evicted_adapter_count = 0
        metadata_changed = False

        for item in adapters:
            if (
                current_adapter_size_mb <= max_adapter_storage_mb
                and item.get("path")
                and os.path.exists(item.get("path"))
            ):
                adapters_to_keep.append(item)
                continue

            item_path = item.get("path")
            item_name = item.get("name")
            item_size = item.get("size_mb", 0)

            if not item_path or not os.path.exists(item_path):
                if item_path:  # Only subtract size if it was supposed to be there
                    current_adapter_size_mb -= item_size
                print(
                    f"Evicting (metadata only, path missing): Adapter '{item_name}' from {item_path}"
                )
                evicted_adapter_count += 1
                metadata_changed = True
                continue

            if current_adapter_size_mb > max_adapter_storage_mb:
                print(
                    f"Evicting adapter '{item_name}' (size: {item_size:.2f} MB, path: {item_path}) to free up space."
                )
                try:
                    shutil.rmtree(item_path)
                    current_adapter_size_mb -= item_size
                    evicted_adapter_count += 1
                    metadata_changed = True

                    # With the persistent adapter strategy, item_name (from disk) should not be
                    # the same as PERSISTENT_ADAPTER_NAME unless something is very wrong with paths.
                    # We don't manage multiple adapters in PeftModel anymore.
                    if (
                        hasattr(state, "base_model")
                        and hasattr(state.base_model, "peft_config")
                        and item_name in state.base_model.peft_config
                    ):
                        if item_name != PERSISTENT_ADAPTER_NAME:
                            print(
                                f"[Disk Cache Eviction] Deleting adapter '{item_name}' also from PeftModel (this is unexpected)."
                            )
                            state.base_model.delete_adapter(item_name)
                            # If the deleted adapter was somehow active, reset to PERSISTENT_ADAPTER_NAME or None
                            if state.base_model.active_adapter == item_name:
                                if (
                                    PERSISTENT_ADAPTER_NAME
                                    in state.base_model.peft_config
                                ):
                                    state.base_model.set_adapter(
                                        PERSISTENT_ADAPTER_NAME
                                    )
                                else:
                                    state.base_model.active_adapter = (
                                        None  # Should not happen
                                    )
                        else:
                            # This case (evicting the persistent adapter's name from disk metadata) seems unlikely
                            # unless ADAPTER_DIR is being cleared of the persistent adapter's own named folder.
                            # We should not delete PERSISTENT_ADAPTER_NAME from the model itself here.
                            print(
                                f"[Disk Cache Eviction] Note: '{item_name}' matches PERSISTENT_ADAPTER_NAME. Not removing from PeftModel."
                            )

                        _torch = globals().get("torch")
                        if (
                            _torch
                            and hasattr(_torch.cuda, "is_available")
                            and _torch.cuda.is_available()
                        ):
                            _torch.cuda.empty_cache()
                        gc.collect()
                except OSError as e:
                    print(f"Error deleting adapter directory {item_path}: {e}")
                    adapters_to_keep.append(item)  # Keep if deletion failed
            else:  # Path exists, but we are within budget now
                adapters_to_keep.append(item)

        _lru_disk_metadata["adapters"] = sorted(
            adapters_to_keep,
            key=lambda x: x.get("last_accessed_ts", 0),  # type: ignore
            reverse=True,
        )
        if evicted_adapter_count > 0:
            print(
                f"Evicted {evicted_adapter_count} adapters. Remaining adapter storage: {current_adapter_size_mb:.2f} MB."
            )
        manage_adapters_end_time = time.time()
        print(
            f"[METRIC] Adapter storage management took {manage_adapters_end_time - manage_adapters_start_time:.2f} seconds."
        )

        # --- Manage SFT Runs ---
        manage_sft_runs_start_time = time.time()
        sft_runs = sorted(
            _lru_disk_metadata.get("sft_runs", []),
            key=lambda x: x.get("last_accessed_ts", 0),  # type: ignore
        )
        current_sft_run_size_mb = sum(item.get("size_mb", 0) for item in sft_runs)
        # print(f"Current SFT run storage: {current_sft_run_size_mb:.2f} MB / {max_sft_run_storage_mb:.2f} MB limit.")

        sft_runs_to_keep = []
        evicted_sft_count = 0
        for item in sft_runs:
            if (
                current_sft_run_size_mb <= max_sft_run_storage_mb
                and item.get("path")
                and os.path.exists(item.get("path"))
            ):
                sft_runs_to_keep.append(item)
                continue

            item_path = item.get("path")
            item_name = item.get("name")
            item_size = item.get("size_mb", 0)

            if not item_path or not os.path.exists(item_path):
                if item_path:
                    current_sft_run_size_mb -= item_size
                print(
                    f"Evicting (metadata only, path missing): SFT run '{item_name}' from {item_path}"
                )
                evicted_sft_count += 1
                metadata_changed = True
                continue

            if current_sft_run_size_mb > max_sft_run_storage_mb:
                print(
                    f"Evicting SFT run '{item_name}' (size: {item_size:.2f} MB, path: {item_path}) to free up space."
                )
                try:
                    shutil.rmtree(item_path)
                    current_sft_run_size_mb -= item_size
                    evicted_sft_count += 1
                    metadata_changed = True
                except OSError as e:
                    print(f"Error deleting SFT run directory {item_path}: {e}")
                    sft_runs_to_keep.append(item)
            else:  # Path exists, but we are within budget
                sft_runs_to_keep.append(item)

        _lru_disk_metadata["sft_runs"] = sorted(
            sft_runs_to_keep,
            key=lambda x: x.get("last_accessed_ts", 0),  # type: ignore
            reverse=True,
        )
        if evicted_sft_count > 0:
            print(
                f"Evicted {evicted_sft_count} SFT runs. Remaining SFT run storage: {current_sft_run_size_mb:.2f} MB."
            )
        manage_sft_runs_end_time = time.time()
        print(
            f"[METRIC] SFT run storage management took {manage_sft_runs_end_time - manage_sft_runs_start_time:.2f} seconds."
        )

        save_metadata_start_time = time.time()
        if (
            metadata_changed or evicted_adapter_count > 0 or evicted_sft_count > 0
        ):  # Save if any changes were made
            with open(LRU_METADATA_FILE, "w") as f_write:
                json.dump(_lru_disk_metadata, f_write, indent=4)
            # print(f"LRU metadata (potentially) updated by _ensure_storage_limits.")
        save_metadata_end_time = time.time()
        if metadata_changed or evicted_adapter_count > 0 or evicted_sft_count > 0:
            print(
                f"[METRIC] Saving LRU metadata took {save_metadata_end_time - save_metadata_start_time:.2f} seconds."
            )

    except Exception as e:
        print(f"Error during _ensure_storage_limits: {e}")
    finally:
        _release_lock(lock_fd)
    ensure_limits_end_time = time.time()
    print(
        f"[METRIC] Total _ensure_storage_limits execution time: {ensure_limits_end_time - ensure_limits_start_time:.2f} seconds."
    )


# --- End LRU Disk Cache Management ---


def _process_dataset_line(line: str) -> Optional[Dict[str, Any]]:
    """Processes a single line of a dataset file. Import is local for pickling."""
    from chatmux import oai_to_unsloth

    if line.strip():
        try:
            return oai_to_unsloth(json.loads(line))
        except json.JSONDecodeError:
            print(f"Warning: could not decode JSON from line: {line[:200]}...")
            return None
    return None


def passthrough_formatting_func(example: Dict[str, Any]) -> List[str]:
    """
    The dataset is already formatted by oai_to_unsloth.
    This function is a dummy to satisfy the SFTTrainer's validation,
    which expects a function that returns a list of strings for vision models.
    The actual content returned does not matter since `remove_unused_columns=False`
    is set in the training arguments, ensuring the original data columns
    (like 'images') are preserved for the data collator.
    """
    return [""]


LORA_RANK = 64
LORA_ALPHA = 128
LORA_DROPOUT = 0
MAX_LENGTH = 32_768


class TrainingRequest(BaseModel):
    adapter: str
    dataset: str
    model: str = BASE_MODEL_ID
    max_length: int = 32_768
    epochs: int = 1
    batch_size: int = 4
    gradient_accumulation_steps: int = 2
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_steps: int = 5
    logging_steps: int = 1
    optimizer: str = "adamw_8bit"
    owner: Optional[str] = None
    labels: Optional[Dict[str, str]] = None


class TrainingResponse(BaseModel):
    loss: float
    train_steps_per_second: float
    train_samples_per_second: float
    train_runtime: float
    adapter: str
    adapter_uri: str


scale = V1Scale(
    up=V1ScaleUp(above_pressure=10, duration="5m"),
    down=V1ScaleDown(below_pressure=2, duration="10m"),
    zero=V1ScaleZero(duration="10m"),
)

setup_script = """
apt update
apt install -y git
pip install torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install trl peft transformers bitsandbytes sentencepiece accelerate orign
pip install -e git+https://github.com/pbarker/unsloth-zoo.git#egg=unsloth_zoo
pip install unsloth
pip install -e git+https://github.com/pbarker/unsloth-zoo.git#egg=unsloth_zoo
pip install huggingface_hub[hf_xet]
"""


def init():
    init_start_time = time.time()
    import gc

    from unsloth import FastVisionModel  # type: ignore # isort: skip
    import torch  # type: ignore  # type: ignore
    from nebulous import Cache  # type: ignore
    from peft import LoraConfig, PeftModel  # type: ignore  # noqa: F401
    from unsloth_zoo.peft_utils import get_peft_regex  # type: ignore

    from orign import V1Adapter

    if "state" in globals():  # <-- already loaded by an earlier worker
        print("state already loaded by an earlier worker")
        return

    gc.collect()
    torch.cuda.empty_cache()  # os.environ.setdefault("MAX_PIXELS", "100352")

    os.makedirs(ADAPTER_DIR, exist_ok=True)

    # --- LRU Disk Cache Init ---
    _load_lru_metadata()
    _ensure_storage_limits()  # Perform initial cleanup if needed
    # --- End LRU Disk Cache Init ---

    @dataclass
    class TrainingState:
        base_model: FastVisionModel
        model_processor: Any
        base_model_id: str
        adapters: List[V1Adapter]
        cache: Cache

    print("Loading base model and tokenizer...")
    base_model_load_start_time = time.time()
    base_model, model_processor = FastVisionModel.from_pretrained(
        BASE_MODEL_ID,
        dtype=torch.bfloat16,
        load_in_4bit=False,
        max_seq_length=MAX_LENGTH,
        use_gradient_checkpointing="unsloth",
    )
    model_load_end_time = time.time()
    print(
        f"[METRIC] Base model and tokenizer loaded in {model_load_end_time - base_model_load_start_time:.2f} seconds."
    )

    print("\nApplying initial PEFT setup with FastVisionModel.get_peft_model...")
    peft_setup_start_time = time.time()
    plumbed_model: PeftModel = FastVisionModel.get_peft_model(
        base_model,
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        finetune_vision_layers=True,
        finetune_language_layers=True,
        # target_modules is determined internally by Unsloth based on above flags
    )
    print(f"Type of model after get_peft_model: {type(plumbed_model)}")
    peft_setup_end_time = time.time()
    print(
        f"[METRIC] Initial PEFT setup (get_peft_model) took {peft_setup_end_time - peft_setup_start_time:.2f} seconds."
    )

    global G_INITIAL_TARGET_MODULES_PATTERN

    # --- Capture the target_modules from the "default" adapter ---
    capture_target_modules_start_time = time.time()
    if "default" in plumbed_model.peft_config:
        G_INITIAL_TARGET_MODULES_PATTERN = plumbed_model.peft_config[
            "default"
        ].target_modules
        print(
            "Captured initial target_modules pattern from 'default' adapter's config."
        )

        # Delete the default adapter since we'll manage our own adapters
        print("Deleting 'default' adapter created by get_peft_model.")
        plumbed_model.delete_adapter("default")
    else:
        print(
            "Warning: 'default' adapter not found. Attempting to generate target_modules pattern manually."
        )
        G_INITIAL_TARGET_MODULES_PATTERN = get_peft_regex(
            base_model,
            finetune_vision_layers=True,
            finetune_language_layers=True,
            finetune_attention_modules=True,
            finetune_mlp_modules=True,
        )
        print("Generated initial target_modules pattern (fallback).")

    if G_INITIAL_TARGET_MODULES_PATTERN is None:
        raise RuntimeError(
            "Could not determine initial target_modules pattern. Aborting."
        )
    capture_target_modules_end_time = time.time()
    print(
        f"[METRIC] Target modules pattern capture/generation took {capture_target_modules_end_time - capture_target_modules_start_time:.2f} seconds."
    )

    plumbed_model.active_adapter = None
    print(
        f"Initial target_modules pattern to be reused: '{str(G_INITIAL_TARGET_MODULES_PATTERN)[:200]}...'"
    )

    # Add the single persistent adapter
    print(f"Attempting to add persistent adapter: '{PERSISTENT_ADAPTER_NAME}'")
    add_persistent_adapter_start_time = time.time()
    persistent_lora_config = LoraConfig(
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,  # Consistent with FastVisionModel.get_peft_model
        bias="none",
        target_modules=G_INITIAL_TARGET_MODULES_PATTERN,
    )
    try:
        if PERSISTENT_ADAPTER_NAME in plumbed_model.peft_config:
            print(
                f"Persistent adapter '{PERSISTENT_ADAPTER_NAME}' already exists. Deleting before re-adding."
            )
            plumbed_model.delete_adapter(PERSISTENT_ADAPTER_NAME)

        plumbed_model.add_adapter(
            adapter_name=PERSISTENT_ADAPTER_NAME, peft_config=persistent_lora_config
        )
        print(f"Successfully added persistent adapter '{PERSISTENT_ADAPTER_NAME}'.")
        plumbed_model.set_adapter(PERSISTENT_ADAPTER_NAME)
        print(f"Set '{PERSISTENT_ADAPTER_NAME}' as the active adapter.")
    except Exception as e:
        print(
            f"Error adding or setting persistent adapter '{PERSISTENT_ADAPTER_NAME}': {e}"
        )
        print(
            f"G_INITIAL_TARGET_MODULES_PATTERN type: {type(G_INITIAL_TARGET_MODULES_PATTERN)}, value: {str(G_INITIAL_TARGET_MODULES_PATTERN)[:200]}"
        )
        raise RuntimeError(
            f"Failed to add or set persistent adapter '{PERSISTENT_ADAPTER_NAME}': {e}"
        )

    global state
    state = TrainingState(
        base_model=plumbed_model,
        model_processor=model_processor,
        base_model_id=BASE_MODEL_ID,
        adapters=[],
        cache=Cache(),
    )
    add_persistent_adapter_end_time = time.time()
    print(
        f"[METRIC] Adding persistent adapter and TrainingState init took {add_persistent_adapter_end_time - add_persistent_adapter_start_time:.2f} seconds."
    )
    init_end_time = time.time()
    print(
        f"[METRIC] Total init() function execution time: {init_end_time - init_start_time:.2f} seconds."
    )


def add_or_load_adapter_for_model(
    model: "PeftModel",  # type: ignore # noqa: F821
    adapter_name: str,
    resume_training: bool,
) -> str:
    """
    Manages the single persistent adapter by hotswapping weights.
    The model always has PERSISTENT_ADAPTER_NAME loaded. This function
    hotswaps weights from 'adapter_name' into PERSISTENT_ADAPTER_NAME.
    """
    func_start_time = time.time()
    # from peft import LoraConfig # No longer needed for creating new configs here.

    print(
        f"\n[Persistent Adapter] Managing weights for '{adapter_name}' into '{PERSISTENT_ADAPTER_NAME}', resume: {resume_training}"
    )

    adapter_base_folder = os.path.join(
        ADAPTER_DIR, adapter_name
    )  # e.g., /nebulous/cache/adapters/customer_A_adapter
    # Path to the actual adapter files (weights, config) for 'adapter_name'
    path_containing_adapter_files = os.path.join(
        adapter_base_folder, adapter_name
    )  # e.g., /nebulous/cache/adapters/customer_A_adapter/customer_A_adapter

    os.makedirs(
        adapter_base_folder, exist_ok=True
    )  # Ensure base directory for adapter_name exists

    # Hotswapping should point to the directory containing adapter_config.json
    # The trainer used to save a nested directory. We check for that structure first
    # for backwards compatibility.
    path_for_hotswap = path_containing_adapter_files
    if not os.path.exists(os.path.join(path_for_hotswap, "adapter_config.json")):
        potential_legacy_path = os.path.join(path_for_hotswap, PERSISTENT_ADAPTER_NAME)
        if os.path.exists(os.path.join(potential_legacy_path, "adapter_config.json")):
            print(
                f"[Persistent Adapter] Found legacy adapter structure. Using path: {potential_legacy_path} for hotswap."
            )
            path_for_hotswap = potential_legacy_path

    has_saved_weights = os.path.isdir(path_for_hotswap) and os.listdir(path_for_hotswap)
    print(
        f"[Persistent Adapter] Weights for '{adapter_name}' exist at '{path_for_hotswap}': {has_saved_weights}"
    )

    hotswap_available = False
    hotswap_module = None  # Renamed from hotswap_adapter to avoid conflict with peft.utils.hotswap.hotswap_adapter
    try:
        from peft.utils.hotswap import (  # type: ignore
            hotswap_adapter as imported_hotswap_func,  # type: ignore
        )

        hotswap_module = imported_hotswap_func
        hotswap_available = True
        print("[Persistent Adapter] hotswap_adapter successfully imported.")
    except ImportError as e:
        print(
            f"[Persistent Adapter] hotswap_adapter import failed: {e}. Hotswapping strategy will fail."
        )
    except Exception as e:
        print(
            f"[Persistent Adapter] Unexpected error importing hotswap_adapter: {type(e).__name__}: {e}"
        )

    if not hotswap_available or hotswap_module is None:
        print(
            "[Persistent Adapter] CRITICAL: Hotswap functionality is not available. Weight loading will likely fail or be skipped."
        )

    if has_saved_weights and resume_training:
        print(
            f"[Persistent Adapter] Attempting to HOTSWAP weights from '{path_for_hotswap}' into '{PERSISTENT_ADAPTER_NAME}'."
        )
        if hotswap_available and hotswap_module:
            try:
                if model.active_adapter != PERSISTENT_ADAPTER_NAME:
                    print(
                        f"[Persistent Adapter] Setting '{PERSISTENT_ADAPTER_NAME}' as active before hotswap."
                    )
                    model.set_adapter(PERSISTENT_ADAPTER_NAME)

                hotswap_start_time = time.time()
                hotswap_module(
                    model,
                    path_for_hotswap,  # Source of weights
                    adapter_name=PERSISTENT_ADAPTER_NAME,  # Target adapter in the model to update
                    torch_device=(
                        "cuda"
                        if hasattr(model, "device")
                        and model.device
                        and model.device.type == "cuda"
                        else None
                    ),
                )
                hotswap_end_time = time.time()
                print(
                    f"[METRIC] [Persistent Adapter] Hotswap time: {hotswap_end_time - hotswap_start_time:.2f}s. "
                    f"Successfully hotswapped weights from '{adapter_name}' into '{PERSISTENT_ADAPTER_NAME}'."
                )
            except Exception as e:
                print(
                    f"[Persistent Adapter] Hotswap FAILED for '{adapter_name}' weights: {type(e).__name__}: {str(e)}"
                )
                import traceback

                traceback.print_exc()
                if resume_training:
                    print(
                        f"[Persistent Adapter] WARNING: Failed to hotswap weights for resume of '{adapter_name}'. Training will proceed with current weights in '{PERSISTENT_ADAPTER_NAME}'."
                    )
        else:
            print(
                f"[Persistent Adapter] Hotswap not available, cannot load weights for '{adapter_name}'."
            )
            if resume_training:
                print(
                    f"[Persistent Adapter] WARNING: Cannot resume '{adapter_name}' as hotswap is unavailable."
                )
    elif not resume_training:
        print(
            f"[Persistent Adapter] Not resuming or no saved weights for '{adapter_name}'. '{PERSISTENT_ADAPTER_NAME}' will use its current (or initial) weights for new training."
        )
        # Optional: consider resetting PERSISTENT_ADAPTER_NAME to a pristine state if truly fresh LoRA layers are needed.
        # For now, we rely on training to overwrite existing weights in PERSISTENT_ADAPTER_NAME.

    # Ensure the persistent adapter is set as active for the upcoming training.
    if model.active_adapter != PERSISTENT_ADAPTER_NAME:
        model.set_adapter(PERSISTENT_ADAPTER_NAME)
    print(
        f"[Persistent Adapter] Active adapter in model: '{model.active_adapters}' (should include '{PERSISTENT_ADAPTER_NAME}')"
    )

    # Update LRU disk cache for the actual adapter's artifacts on disk
    _update_item_access(adapter_name, "adapters", adapter_base_folder)
    print(
        f"[METRIC] [Persistent Adapter] add_or_load_adapter_for_model for '{adapter_name}' took {time.time() - func_start_time:.2f}s"
    )
    return adapter_base_folder


def drop_adapter_from_model(model: "PeftModel", adapter_name_to_drop: str):  # type: ignore # noqa: F821
    # This function is now largely a no-op with the persistent adapter strategy.
    # We should NOT drop PERSISTENT_ADAPTER_NAME.
    # Other adapters should not be in the model's peft_config.
    # import torch  # type: ignore # Removed as it's not used
    # global state # state is not used here for loaded_adapter_names_lru anymore

    print(f"\n[Adapter Management] Request to drop adapter: '{adapter_name_to_drop}'")

    if adapter_name_to_drop == PERSISTENT_ADAPTER_NAME:
        print(
            f"[Adapter Management] Attempt to drop the persistent adapter '{PERSISTENT_ADAPTER_NAME}'. This is not allowed. Ignoring."
        )
        return

    # Removed LRU cache logic for state.loaded_adapter_names_lru

    if adapter_name_to_drop in model.peft_config:
        print(
            f"[Adapter Management] WARNING: Adapter '{adapter_name_to_drop}' found in PeftModel's config unexpectedly. "
            "It should not be there with the persistent adapter strategy. Deleting it."
        )
        if model.active_adapter == adapter_name_to_drop:
            # This case should ideally not happen if PERSISTENT_ADAPTER_NAME is always active or active is None
            print(
                f"[Adapter Management] Deactivated unexpected adapter '{adapter_name_to_drop}'. Setting active to PERSISTENT_ADAPTER_NAME if not None, else None."
            )
            # If the active adapter was this unexpected one, try to set persistent or None
            if PERSISTENT_ADAPTER_NAME in model.peft_config:  # safety check
                model.set_adapter(PERSISTENT_ADAPTER_NAME)
            else:
                model.active_adapter = None

        try:
            model.delete_adapter(adapter_name_to_drop)
            print(
                f"[Adapter Management] Successfully deleted unexpected adapter '{adapter_name_to_drop}'."
            )
        except Exception as e:
            print(
                f"[Adapter Management] Error deleting unexpected adapter '{adapter_name_to_drop}': {e}"
            )
    else:
        print(
            f"[Adapter Management] Adapter '{adapter_name_to_drop}' not found in PeftModel config (as expected). No model deletion needed."
        )

    # torch.cuda.empty_cache() # Generally not needed here, let higher level functions manage GPU memory.
    # gc.collect()
    print(
        f"[Adapter Management] Finished (pseudo) dropping adapter '{adapter_name_to_drop}'.\n"
    )


class TimedDataCollator:
    """Wraps a data collator to measure performance of __call__."""

    def __init__(self, collator: Any):
        self.collator = collator
        self.total_time = 0.0
        self.count = 0
        self.timings = []

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = self.collator(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        self.total_time += duration
        self.timings.append(duration)
        self.count += 1
        return result

    def report(self):
        if not self.timings:
            return "Data collator was not called."

        avg_time = self.total_time / self.count
        max_time = max(self.timings)
        min_time = min(self.timings)

        report_str = (
            f"Data collator call metrics: \n"
            f"  - Count: {self.count}\n"
            f"  - Total time: {self.total_time:.4f}s\n"
            f"  - Average time: {avg_time:.4f}s\n"
            f"  - Min time: {min_time:.4f}s\n"
            f"  - Max time: {max_time:.4f}s"
        )
        return report_str


def train_lora_adapter(
    adapter_name_to_train: str,
    training_dataset: Any,
    num_epochs: int = 1,
    resume_from_saved_state: bool = False,
    checkpoint_path: Optional[str] = None,
    batch_size: int = 2,
    gradient_accumulation_steps: int = 4,
    learning_rate: float = 2e-4,
    weight_decay: float = 0.01,
    warmup_steps: int = 5,
    logging_steps: int = 1,
    save_steps: int = 5,
    optimizer: str = "adamw_8bit",
):
    import json  # Added for reading trainer_state.json
    import os  # ensure os is imported locally if not already

    import torch  # type: ignore
    from trl import SFTConfig, SFTTrainer  # type: ignore
    from unsloth import FastVisionModel, is_bf16_supported  # type: ignore
    from unsloth.trainer import UnslothVisionDataCollator  # type: ignore

    global state

    print(
        f"\n--- Starting train_lora_adapter for adapter: '{adapter_name_to_train}' (Epochs: {num_epochs}, Resume: {resume_from_saved_state}) ---"
    )

    os.system("nvidia-smi")

    # Use smart adapter management
    start_adapter_time = time.time()
    adapter_base_save_folder = add_or_load_adapter_for_model(
        state.base_model,
        adapter_name_to_train,
        resume_from_saved_state or bool(checkpoint_path),
    )
    end_adapter_time = time.time()
    print(
        f"[METRIC] Time taken to load adapter: {end_adapter_time - start_adapter_time} seconds"
    )
    print(
        f"Adapter base save folder for '{adapter_name_to_train}': {adapter_base_save_folder}"
    )

    loaded_adapter_names = []
    if hasattr(state.base_model, "peft_config"):
        loaded_adapter_names = list(state.base_model.peft_config.keys())
    print("loaded_adapter_names: ", loaded_adapter_names)

    # The smart management ensures the correct adapter is active
    print(f"Training will use adapter: '{adapter_name_to_train}'")
    print(f"Currently active adapters: {state.base_model.active_adapters}")

    print("\nPreparing model for training with FastVisionModel.for_training...")
    for_training_start_time = time.time()
    model_ready_for_training = FastVisionModel.for_training(state.base_model)
    print(
        f"[METRIC] FastVisionModel.for_training took {time.time() - for_training_start_time:.4f}s."
    )
    print("Model prepared for training.")

    print(
        f"DEBUG: model_ready_for_training is state.base_model: {model_ready_for_training is state.base_model}"
    )
    if hasattr(model_ready_for_training, "active_adapter"):
        print(
            f"DEBUG: model_ready_for_training.active_adapter: {model_ready_for_training.active_adapter}"
        )
    if (
        hasattr(model_ready_for_training, "peft_config")
        and model_ready_for_training.peft_config
    ):
        print(
            f"DEBUG: model_ready_for_training.peft_config.keys(): {list(model_ready_for_training.peft_config.keys())}"
        )
    else:
        print("DEBUG: model_ready_for_training has no peft_config or it is empty.")

    if hasattr(state.base_model, "active_adapter"):
        print(
            f"DEBUG: state.base_model.active_adapter after for_training: {state.base_model.active_adapter}"
        )
    if hasattr(state.base_model, "peft_config") and state.base_model.peft_config:
        print(
            f"DEBUG: state.base_model.peft_config.keys() after for_training: {list(state.base_model.peft_config.keys())}"
        )
    else:
        print(
            "DEBUG: state.base_model has no peft_config or it is empty after for_training."
        )

    print("\nModel's trainable parameters (on instance passed to SFTTrainer):")
    try:
        model_ready_for_training.print_trainable_parameters()
    except AttributeError:
        total_params = sum(p.numel() for p in model_ready_for_training.parameters())
        trainable_params = sum(
            p.numel() for p in model_ready_for_training.parameters() if p.requires_grad
        )
        print(
            f"trainable params: {trainable_params:,} || all params: {total_params:,} || trainable%: {100 * trainable_params / total_params:.4f}"
        )

    # Use the learning_rate provided via TrainingRequest
    print(f"Using learning_rate for SFTTrainer: {learning_rate}")

    print("trainable params:")
    for name, param in model_ready_for_training.named_parameters():
        if param.requires_grad:
            print(name)

    sft_config_args = SFTConfig(
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        num_train_epochs=num_epochs,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        warmup_steps=warmup_steps,
        optim=optimizer,
        # optim="apollo_adamw",
        # optim_target_modules=[r".*.attn.*", r".*.mlp.*"],
        fp16=not is_bf16_supported(),
        bf16=is_bf16_supported(),
        save_strategy="epoch",
        save_total_limit=1,
        output_dir=f"./runs/{adapter_name_to_train}",
        logging_steps=logging_steps,
        report_to="none",
        remove_unused_columns=False,
        dataset_num_proc=1,
    )

    # Initialize collator separately to observe its effect on model's active_adapter
    print("Initializing UnslothVisionDataCollator...")
    collator_init_start_time = time.time()
    data_collator = UnslothVisionDataCollator(
        model_ready_for_training, state.model_processor, resize="max"
    )
    collator_init_duration = time.time() - collator_init_start_time
    print(
        f"[METRIC] UnslothVisionDataCollator initialized in {collator_init_duration:.4f}s."
    )
    print("Wrapping data collator for performance monitoring.")
    data_collator = TimedDataCollator(data_collator)
    active_adapter_after_collator = "N/A"
    if hasattr(model_ready_for_training, "active_adapter"):
        active_adapter_after_collator = model_ready_for_training.active_adapter
    print(
        f"model_ready_for_training.active_adapter after collator init: {active_adapter_after_collator}"
    )

    # Print available adapters before defensive set
    if (
        hasattr(model_ready_for_training, "peft_config")
        and model_ready_for_training.peft_config
    ):
        print(
            f"Available adapters in model_ready_for_training.peft_config before defensive set: {list(model_ready_for_training.peft_config.keys())}"
        )
    else:
        print(
            "model_ready_for_training has no peft_config or it is empty before defensive set."
        )

    # Defensive: Ensure active_adapter is set on model_ready_for_training
    # right before SFTTrainer initialization.
    if (
        hasattr(model_ready_for_training, "set_adapter")
        and hasattr(model_ready_for_training, "peft_config")
        and PERSISTENT_ADAPTER_NAME in model_ready_for_training.peft_config
    ):
        print(
            f"Defensively re-setting active adapter to '{PERSISTENT_ADAPTER_NAME}' on model_ready_for_training before SFTTrainer constructor."
        )
        model_ready_for_training.set_adapter(PERSISTENT_ADAPTER_NAME)

    print("Initializing SFTTrainer...")
    sft_trainer_init_start_time = time.time()
    trainer = SFTTrainer(
        model=model_ready_for_training,
        tokenizer=state.model_processor,
        data_collator=data_collator,  # Use the pre-initialized collator
        train_dataset=training_dataset,
        args=sft_config_args,
        formatting_func=passthrough_formatting_func,
    )
    sft_trainer_init_duration = time.time() - sft_trainer_init_start_time
    print(f"[METRIC] SFTTrainer initialized in {sft_trainer_init_duration:.4f}s.")

    # For SFTTrainer's resume_from_checkpoint:
    # If checkpoint_path is explicitly given, use it.
    # Else, if resume_from_saved_state is True, pass True to trainer.train() to load latest from output_dir.
    # Otherwise, no resume.
    sft_trainer_resume_arg = None
    if checkpoint_path:
        sft_trainer_resume_arg = checkpoint_path
        print(
            f"SFTTrainer will attempt to resume from EXPLICIT checkpoint path: '{sft_trainer_resume_arg}'"
        )
    elif resume_from_saved_state:
        sft_trainer_resume_arg = (
            True  # Let Trainer find the latest checkpoint in output_dir
        )
        print(
            f"SFTTrainer will attempt to resume from the latest checkpoint in its output_dir: {sft_config_args.output_dir}"
        )
    else:
        print(
            "SFTTrainer training from scratch (no SFTTrainer checkpoint specified or found for resume)."
        )

    # Check if the directory for SFTTrainer resume exists if a path was constructed (not True)
    if isinstance(sft_trainer_resume_arg, str) and not os.path.isdir(
        sft_trainer_resume_arg
    ):
        print(
            f"Warning: SFTTrainer resume path '{sft_trainer_resume_arg}' not found. Training from scratch."
        )
        sft_trainer_resume_arg = None  # Fallback to no resume

    print("\nInspecting SFT checkpoint for prior epoch count before training starts...")
    sft_checkpoint_dir_to_inspect = None
    if isinstance(sft_trainer_resume_arg, str) and os.path.isdir(
        sft_trainer_resume_arg
    ):
        sft_checkpoint_dir_to_inspect = sft_trainer_resume_arg
        print(
            f"SFTTrainer is configured to resume from explicit path: {sft_checkpoint_dir_to_inspect}"
        )
    elif sft_trainer_resume_arg is True:
        # SFTTrainer will look in sft_config_args.output_dir
        print(
            f"SFTTrainer is configured to resume from latest in output_dir: {sft_config_args.output_dir}"
        )
        # We need to find what SFTTrainer would find.
        # find_latest_checkpoint is imported from orign, which should be available.
        latest_sft_checkpoint_in_output_dir = find_latest_checkpoint(
            sft_config_args.output_dir
        )
        if latest_sft_checkpoint_in_output_dir:
            sft_checkpoint_dir_to_inspect = latest_sft_checkpoint_in_output_dir
            print(
                f"Found latest SFT checkpoint for inspection: {sft_checkpoint_dir_to_inspect}"
            )
        else:
            print(
                f"No SFT checkpoint found in {sft_config_args.output_dir} to inspect for prior epochs."
            )
    else:
        print(
            "SFTTrainer is not configured to resume from a checkpoint. No prior SFT epochs to report from trainer_state.json."
        )

    if sft_checkpoint_dir_to_inspect:
        trainer_state_path_to_inspect = os.path.join(
            sft_checkpoint_dir_to_inspect, "trainer_state.json"
        )
        print(
            f"Attempting to read SFT trainer state from: {trainer_state_path_to_inspect}"
        )
        if os.path.exists(trainer_state_path_to_inspect):
            try:
                with open(trainer_state_path_to_inspect, "r") as f:
                    sft_state_data = json.load(f)
                sft_epochs_completed = sft_state_data.get("epoch", 0.0)
                sft_global_step = sft_state_data.get("global_step", 0)
                print(
                    f"  >> SFT Checkpoint State: Epochs completed = {sft_epochs_completed}, Global steps = {sft_global_step}"
                )
            except Exception as e:
                print(
                    f"  >> Warning: Failed to read/parse SFT {trainer_state_path_to_inspect}: {e}"
                )
        else:
            print(f"  >> Warning: SFT {trainer_state_path_to_inspect} not found.")
    print("--- End of SFT Checkpoint Inspection ---")

    print("\nStarting SFTTrainer training...")
    train_start_time = time.time()
    trainer.train(resume_from_checkpoint=sft_trainer_resume_arg)
    train_duration = time.time() - train_start_time
    print(f"[METRIC] SFTTrainer training finished in {train_duration:.2f} seconds.")

    # Report collator metrics
    print(f"[METRIC] {data_collator.report()}")

    # Save adapter weights
    # Construct the correct path: ADAPTER_DIR/adapter_name_to_train/adapter_name_to_train
    # adapter_base_save_folder is ADAPTER_DIR/adapter_name_to_train
    target_adapter_weights_save_path = os.path.join(
        adapter_base_save_folder, adapter_name_to_train
    )
    print(
        f"\nSaving weights of '{PERSISTENT_ADAPTER_NAME}' (representing '{adapter_name_to_train}') to: {target_adapter_weights_save_path}"
    )
    os.makedirs(
        target_adapter_weights_save_path, exist_ok=True
    )  # Ensure directory exists
    save_model_start_time = time.time()
    # Save the active adapter (PERSISTENT_ADAPTER_NAME) into the target path.
    # Since only one adapter is in the model, PEFT saves it directly to the given path.
    model_ready_for_training.save_pretrained(target_adapter_weights_save_path)
    save_model_duration = time.time() - save_model_start_time
    print(
        f"[METRIC] Adapter weights saved in {save_model_duration:.2f} seconds to {target_adapter_weights_save_path}."
    )

    # Post-process the saved directory. If peft created a subdirectory for the
    # persistent adapter, move its contents to the parent directory.
    saved_adapter_subdir = os.path.join(
        target_adapter_weights_save_path, PERSISTENT_ADAPTER_NAME
    )
    if os.path.isdir(saved_adapter_subdir):
        print(
            f"Found saved adapter in subdirectory '{PERSISTENT_ADAPTER_NAME}'. Moving contents to parent directory."
        )
        for item in os.listdir(saved_adapter_subdir):
            source_item = os.path.join(saved_adapter_subdir, item)
            dest_item = os.path.join(target_adapter_weights_save_path, item)
            shutil.move(source_item, dest_item)
        os.rmdir(saved_adapter_subdir)
        print("Successfully moved adapter contents.")

    # With smart management, we keep the adapter loaded for fast future access
    # The LRU cache in add_or_load_adapter_for_model will handle eviction.
    # We'll just deactivate the current adapter if it's active.
    # print(
    #     f"[LRU Management] Adapter '{adapter_name_to_train}' remains in LRU cache: {list(state.loaded_adapter_names_lru)}. Deactivating if active."
    # ) # Old LRU comment

    # With the persistent adapter, PERSISTENT_ADAPTER_NAME is always 'loaded' in the model structure.
    # Its weights are hotswapped. After training, we can deactivate it (set active_adapter = None).
    print(
        f"[Persistent Adapter] Training for '{adapter_name_to_train}' (using '{PERSISTENT_ADAPTER_NAME}') finished."
    )
    if (
        state.base_model.active_adapter == PERSISTENT_ADAPTER_NAME
        or PERSISTENT_ADAPTER_NAME
        in state.base_model.active_adapters  # Handles if active_adapters is a list
    ):  # Check both single and multiple active adapters
        state.base_model.active_adapter = None  # Deactivate
        print(
            f"[Persistent Adapter] Deactivated '{PERSISTENT_ADAPTER_NAME}'. No active adapter set by default."
        )
    else:
        # This case should ideally not occur if PERSISTENT_ADAPTER_NAME was correctly managed.
        print(
            f"[Persistent Adapter] Warning: '{PERSISTENT_ADAPTER_NAME}' was not the active adapter after training for '{adapter_name_to_train}'. Current active: {state.base_model.active_adapters}"
        )

    del trainer, model_ready_for_training
    torch.cuda.empty_cache()
    gc.collect()
    print(
        f"--- train_lora_adapter for adapter: '{adapter_name_to_train}' completed ---\n"
    )

    # --- LRU Disk Cache: Update access for adapter after training (weights saved within train_lora_adapter) ---
    _update_item_access(
        adapter_name_to_train,
        "adapters",
        os.path.join(ADAPTER_DIR, adapter_name_to_train),
    )
    # ---


def train_unsloth_sft(message: Message[TrainingRequest]) -> TrainingResponse:
    import gc
    import json
    import multiprocessing
    import shutil

    import requests
    import torch  # type: ignore
    from datasets import Dataset  # type: ignore
    from nebulous import (
        Bucket,
        ContainerConfig,
        V1ResourceReference,
        is_allowed,
    )

    from orign import Adapter, Training, V1LoraParams

    global state
    if not hasattr(state, "base_model") or not hasattr(state, "model_processor"):
        raise RuntimeError(
            "Base model and processor not initialized. Ensure init() has run."
        )

    # --- LRU Disk Cache: Make space before starting ---
    print("Ensuring storage limits before starting training operations...")
    _ensure_storage_limits()
    # ---

    # First ensure CUDA cache is cleared
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()

    # Force garbage collection multiple times to ensure all tensors are released
    gc.collect()

    print("message", message)
    if not message.content:
        raise ValueError("No training request provided")
    training_request: TrainingRequest = message.content

    container_config = ContainerConfig.from_env()
    print("container_config", container_config)

    bucket = Bucket()

    print("determining adapter namespace and name...")
    adapter_parts = training_request.adapter.split("/")
    if len(adapter_parts) == 2:
        print("adapter_parts", adapter_parts)
        adapter_namespace = adapter_parts[0]
        adapter_name = adapter_parts[1]
    else:
        adapter_name = training_request.adapter
        if training_request.owner:
            print("owner", training_request.owner)
            adapter_namespace = training_request.owner
        else:
            print("no owner, using message.handle", message.handle)
            adapter_namespace = message.handle

    print("adapter_namespace", adapter_namespace)
    if not adapter_namespace:
        raise ValueError("Could not determine adapter namespace")

    # Define local and bucket paths
    # ADAPTER_DIR is global: /nebulous/cache/adapters
    local_adapter_weights_dir_for_current_adapter = os.path.join(
        ADAPTER_DIR, adapter_name
    )
    # train_lora_adapter saves adapter weights into a subfolder named adapter_name within this
    actual_local_adapter_files_path = os.path.join(
        local_adapter_weights_dir_for_current_adapter, adapter_name
    )

    local_sft_runs_dir = f"./runs/{adapter_name}"

    # Bucket URIs
    adapter_weights_bucket_uri = f"{container_config.namespace_volume_uri}/adapters/{adapter_namespace}/{adapter_name}"
    sft_checkpoints_bucket_uri = f"{container_config.namespace_volume_uri}/sft_runs/{adapter_namespace}/{adapter_name}"

    if training_request.labels:
        training_labels = training_request.labels.copy()
    else:
        training_labels = {}
    training_labels["message_id"] = message.id
    training_labels["container_id"] = os.getenv("NEBU_CONTAINER_ID", "unknown")
    random_chars = secrets.token_hex(3)

    adapter_ref = V1ResourceReference(
        name=adapter_name,
        namespace=adapter_namespace,
        kind="Adapter",
    )
    print("adapter_ref: ", adapter_ref)

    training = None
    try:
        print("creating training with api_key", message.api_key)
        training = Training(
            name=adapter_name + "-" + random_chars,
            namespace=adapter_namespace,
            config_data=message.model_dump(),
            adapter=adapter_ref,
            labels=training_labels,
            unique_adapter_active=True,
            api_key=message.api_key,
        )
        print("\n >> marking initial training as running")
        training.update(status=V1TrainingStatus.RUNNING)
    except Exception as e:
        print(
            f"FATAL: Failed to create or update Training resource for {adapter_ref}: {e}  --- retrying..."
        )
        raise RetriableError(
            f"Failed to set up Training resource: {e}  --- retrying..."
        ) from e

    failure = False
    try:
        start_adapter_time = time.time()
        adapter_resource = None
        try:
            adapters_found = Adapter.get(
                adapter_namespace, adapter_name, api_key=message.api_key
            )
            if adapters_found:
                adapter_resource = adapters_found[0]
        except Exception:
            adapters_found = []  # noqa
        print("found adapter resource", adapter_resource)

        is_continue = False
        epochs_trained_so_far = 0
        sft_checkpoint_to_resume_from = (
            None  # This will be local_sft_runs_dir if resuming
        )

        if adapter_resource:
            print("Found existing adapter resource: ", adapter_resource)
            epochs_trained_so_far = adapter_resource.epochs_trained

            if not is_allowed(
                adapter_resource.metadata.owner, message.user_id, message.orgs
            ):
                raise ValueError("You are not allowed to train this existing adapter")

            # Sync adapter weights from bucket to local ADAPTER_DIR/adapter_name
            # train_lora_adapter expects them in ADAPTER_DIR/adapter_name/adapter_name
            print(
                f"Attempting to sync adapter weights from {adapter_weights_bucket_uri} to {actual_local_adapter_files_path}"
            )
            os.makedirs(
                actual_local_adapter_files_path, exist_ok=True
            )  # Ensure target dir exists for sync

            adapter_sync_start_time = time.time()
            try:
                bucket.sync(adapter_weights_bucket_uri, actual_local_adapter_files_path)
                print(f"Synced adapter weights to {actual_local_adapter_files_path}")
                is_continue = True
                # --- LRU Disk Cache: Update access for synced adapter ---
                _update_item_access(
                    adapter_name,
                    "adapters",
                    local_adapter_weights_dir_for_current_adapter,
                )
                # ---
            except Exception as e:
                print(
                    f"Warning: Failed to sync adapter weights from {adapter_weights_bucket_uri}: {e}. May proceed without them if adapter is being created fresh by train_lora_adapter."
                )
            adapter_sync_end_time = time.time()
            print(
                f"[METRIC] Time taken to sync adapter weights: {adapter_sync_end_time - adapter_sync_start_time} seconds"
            )

            # Check if we have a specific checkpoint URI instead of a general SFT runs directory
            checkpoint_uri = adapter_resource.checkpoint_uri
            # If checkpoint URI points to a specific checkpoint (contains "/checkpoint-")
            if checkpoint_uri and "/checkpoint-" in checkpoint_uri:
                checkpoint_name = os.path.basename(checkpoint_uri)
                print(
                    f"Found specific checkpoint reference: {checkpoint_name} in {checkpoint_uri}"
                )

                # Create local directory for this specific checkpoint
                local_checkpoint_dir = os.path.join(local_sft_runs_dir, checkpoint_name)
                os.makedirs(local_checkpoint_dir, exist_ok=True)

                # Sync that specific checkpoint from bucket
                try:
                    print(
                        f"Syncing specific checkpoint from {checkpoint_uri} to {local_checkpoint_dir}"
                    )
                    sync_start_time = time.time()
                    bucket.sync(checkpoint_uri, local_checkpoint_dir)
                    sync_end_time = time.time()
                    print(
                        f"[METRIC] Time taken to sync specific checkpoint: {sync_end_time - sync_start_time} seconds"
                    )
                    print(f"Successfully synced checkpoint {checkpoint_name}")
                    sft_checkpoint_to_resume_from = local_checkpoint_dir
                    is_continue = True
                except Exception as e:
                    print(f"Failed to sync specific checkpoint: {e}")
                    is_continue = False
            else:
                # Fallback to old behavior in case checkpoint_uri is not a specific checkpoint
                print(
                    f"No specific checkpoint reference found in adapter. Will sync from general checkpoint directory: {checkpoint_uri}"
                )
                try:
                    bucket.sync(checkpoint_uri, local_sft_runs_dir)
                    # Look for latest checkpoint in the synced directory
                    latest_checkpoint = find_latest_checkpoint(local_sft_runs_dir)
                    if latest_checkpoint:
                        print(
                            f"Found latest checkpoint in synced directory: {latest_checkpoint}"
                        )
                        sft_checkpoint_to_resume_from = latest_checkpoint
                        is_continue = True
                    else:
                        print("No valid checkpoint found in synced directory")
                        is_continue = False
                except Exception as e:
                    print(f"Failed to sync from general checkpoint directory: {e}")
                    is_continue = False
        else:
            print(
                f"No existing Adapter resource found for {adapter_namespace}/{adapter_name}. This will be a new training."
            )
            # Clean up local directories for a fresh start if they exist from a failed previous run
            if os.path.exists(local_adapter_weights_dir_for_current_adapter):
                shutil.rmtree(local_adapter_weights_dir_for_current_adapter)
                print(
                    f"Cleaned up existing local adapter dir: {local_adapter_weights_dir_for_current_adapter}"
                )
            if os.path.exists(local_sft_runs_dir):
                shutil.rmtree(local_sft_runs_dir)
                print(f"Cleaned up existing local SFT runs dir: {local_sft_runs_dir}")
            os.makedirs(local_adapter_weights_dir_for_current_adapter, exist_ok=True)
            os.makedirs(local_sft_runs_dir, exist_ok=True)

        end_adapter_time = time.time()
        print(
            f"[METRIC] Time taken to download adapter: {end_adapter_time - start_adapter_time} seconds"
        )

        print("Downloading dataset")
        time_start_download = time.time()
        response = requests.get(training_request.dataset)
        response.raise_for_status()
        print(
            f"[METRIC] Downloaded dataset in {time.time() - time_start_download} seconds"
        )

        lines = response.content.decode("utf-8").splitlines()

        time_start_convert = time.time()
        print("Converting dataset using multiprocessing...")
        try:
            # Determine number of processes, with a fallback
            num_processes = multiprocessing.cpu_count()
            print(f"Using {num_processes} processes to convert dataset.")
        except NotImplementedError:
            num_processes = 2  # A reasonable fallback
            print(
                f"Warning: could not determine CPU count. Falling back to {num_processes} processes."
            )

        with multiprocessing.Pool(processes=num_processes) as pool:
            # The map function will apply _process_dataset_line to each item in lines
            results = pool.map(_process_dataset_line, lines)

        # Filter out None results from lines that were empty or failed to parse
        converted_dataset = [r for r in results if r is not None]

        # Convert to a datasets.Dataset object before passing to the trainer
        training_dataset_obj = Dataset.from_list(converted_dataset)

        print(
            f"[METRIC] Converted dataset in {time.time() - time_start_convert} seconds"
        )
        print("dataset example", converted_dataset[:1])

        # Calculate the cumulative target number of epochs
        cumulative_target_epochs = epochs_trained_so_far + training_request.epochs
        print(
            f"Adapter '{adapter_name}': Has {epochs_trained_so_far} epochs trained. Requesting additional {training_request.epochs} epochs. Target cumulative epochs: {cumulative_target_epochs}."
        )
        print(
            f"Calling train_lora_adapter for '{adapter_name}'. Resume SFT: {is_continue}, SFT checkpoint path hint: {sft_checkpoint_to_resume_from}"
        )

        time_start_train = time.time()
        train_lora_adapter(
            adapter_name_to_train=adapter_name,
            training_dataset=training_dataset_obj,
            num_epochs=cumulative_target_epochs,  # Pass cumulative target epochs
            resume_from_saved_state=is_continue,  # For adapter weights loading
            checkpoint_path=sft_checkpoint_to_resume_from
            if is_continue
            else None,  # For SFTTrainer resume
            batch_size=training_request.batch_size,
            gradient_accumulation_steps=training_request.gradient_accumulation_steps,
            learning_rate=training_request.learning_rate,
            weight_decay=training_request.weight_decay,
            warmup_steps=training_request.warmup_steps,
            logging_steps=training_request.logging_steps,
            optimizer=training_request.optimizer,
        )
        print(
            f"[METRIC] train_lora_adapter completed in {time.time() - time_start_train} seconds"
        )

        # After training, sync artifacts to bucket
        # 1. Sync adapter weights
        # train_lora_adapter saves them to actual_local_adapter_files_path
        if os.path.exists(actual_local_adapter_files_path) and os.listdir(
            actual_local_adapter_files_path
        ):
            print(
                f"Syncing adapter weights from {actual_local_adapter_files_path} to {adapter_weights_bucket_uri}"
            )
            bucket.copy(actual_local_adapter_files_path, adapter_weights_bucket_uri)
            print("Synced adapter weights to bucket.")
        else:
            print(
                f"Warning: Local adapter files path {actual_local_adapter_files_path} is empty or does not exist after training. Cannot sync to bucket."
            )

        # 2. Sync SFT checkpoints
        # train_lora_adapter's SFTTrainer saves to local_sft_runs_dir
        if os.path.exists(local_sft_runs_dir) and os.listdir(local_sft_runs_dir):
            # Find the latest checkpoint directory
            latest_checkpoint = find_latest_checkpoint(local_sft_runs_dir)
            if latest_checkpoint:
                # --- Prune checkpoint directory before uploading ---
                print(f"Preparing to prune checkpoint directory: {latest_checkpoint}")
                print(f"  Target adapter to keep artifacts for: '{adapter_name}'")

                adapters_in_peft_config = []
                if hasattr(state, "base_model") and hasattr(
                    state.base_model, "peft_config"
                ):
                    adapters_in_peft_config = list(state.base_model.peft_config.keys())
                    print(
                        f"  Adapters known to be loaded in base_model's peft_config: {adapters_in_peft_config}"
                    )
                else:
                    print(
                        "  Warning: Could not retrieve loaded adapters from state.base_model.peft_config. Pruning might be affected."
                    )

                items_in_checkpoint_main_dir = os.listdir(latest_checkpoint)
                print(
                    f"  Items found in checkpoint directory '{latest_checkpoint}': {items_in_checkpoint_main_dir}"
                )

                for item_name in items_in_checkpoint_main_dir:
                    item_full_path = os.path.join(latest_checkpoint, item_name)
                    if os.path.isdir(item_full_path):
                        # Check if this directory is an adapter-like directory
                        is_adapter_like_dir = os.path.exists(
                            os.path.join(item_full_path, "adapter_config.json")
                        ) and (
                            os.path.exists(
                                os.path.join(item_full_path, "adapter_model.bin")
                            )
                            or os.path.exists(
                                os.path.join(
                                    item_full_path, "adapter_model.safetensors"
                                )
                            )
                        )

                        if is_adapter_like_dir:
                            if item_name == PERSISTENT_ADAPTER_NAME:
                                print(
                                    f"    Keeping: Trained adapter directory '{item_name}' (as {PERSISTENT_ADAPTER_NAME}) in SFT checkpoint."
                                )
                            else:
                                # This case should ideally not happen if peft_config only has PERSISTENT_ADAPTER_NAME
                                print(
                                    f"    Pruning: Removing unexpected/other adapter directory '{item_name}' from SFT checkpoint."
                                )
                                shutil.rmtree(item_full_path)
                        else:
                            print(
                                f"    Keeping: Non-adapter directory '{item_name}' in SFT checkpoint (e.g., optimizer.pt, etc.)."
                            )
                    else:
                        # Keep all files at the root of the checkpoint directory (e.g., optimizer.pt, trainer_state.json)
                        print(f"    Keeping: File '{item_name}'.")
                print(
                    f"  Pruning of SFT checkpoint directory '{latest_checkpoint}' complete."
                )
                # --- End of pruning ---

                # Extract the checkpoint name (e.g., "checkpoint-132")
                latest_checkpoint_name = os.path.basename(latest_checkpoint)
                # Create a specific path for just the latest checkpoint
                latest_checkpoint_bucket_uri = (
                    f"{sft_checkpoints_bucket_uri}/{latest_checkpoint_name}"
                )

                print(
                    f"Syncing latest SFT checkpoint from {latest_checkpoint} to {latest_checkpoint_bucket_uri}"
                )
                bucket.copy(latest_checkpoint, latest_checkpoint_bucket_uri)
                print(f"Synced latest checkpoint ({latest_checkpoint_name}) to bucket.")

                # We'll use this specific checkpoint URI instead of the parent directory
                checkpoint_uri_for_adapter = latest_checkpoint_bucket_uri
            else:
                print(
                    f"Warning: Could not find a checkpoint directory in {local_sft_runs_dir}"
                )
                checkpoint_uri_for_adapter = sft_checkpoints_bucket_uri
        else:
            print(
                f"Warning: Local SFT runs directory {local_sft_runs_dir} is empty or does not exist after training. Cannot sync to bucket."
            )
            checkpoint_uri_for_adapter = sft_checkpoints_bucket_uri

        # --- LRU Disk Cache: Update access for SFT run directory ---
        if os.path.exists(local_sft_runs_dir):
            _update_item_access(
                f"{adapter_name}_sft_run", "sft_runs", local_sft_runs_dir
            )
        # ---

        # Collect metrics from trainer_state.json in the local SFT runs directory
        training_metrics = {}
        trainer_state_path = None  # Initialize to None

        latest_checkpoint_dir = find_latest_checkpoint(local_sft_runs_dir)
        if latest_checkpoint_dir:
            trainer_state_path = os.path.join(
                latest_checkpoint_dir, "trainer_state.json"
            )
            print(f"Found latest checkpoint directory: {latest_checkpoint_dir}")
            print(f"Attempting to load trainer_state.json from: {trainer_state_path}")
        else:
            print(
                f"Warning: No checkpoint directory found in {local_sft_runs_dir}. Looking for trainer_state.json in the root of SFT runs dir as a fallback."
            )
            # Fallback to old behavior if no checkpoint dir is found, though less likely to succeed
            trainer_state_path = os.path.join(local_sft_runs_dir, "trainer_state.json")

        if trainer_state_path and os.path.exists(trainer_state_path):
            try:
                with open(trainer_state_path, "r") as f:
                    state_data = json.load(f)
                training_metrics = state_data
                print(f"Loaded training metrics from {trainer_state_path}")
                log_history = state_data.get("log_history", [])
                if log_history:
                    print(f"  Final log_history entry: {log_history[-1]}")
            except Exception as e:
                print(f"Warning: Failed to read/parse {trainer_state_path}: {e}.")
        else:
            print(f"Warning: {trainer_state_path} not found. Metrics will be empty.")

        # Update Adapter resource with the specific checkpoint URI
        final_epochs_trained = epochs_trained_so_far + training_request.epochs

        Adapter(
            name=adapter_name,
            namespace=adapter_namespace,
            model_uri=adapter_weights_bucket_uri,  # URI now points to the adapter weights in the bucket
            checkpoint_uri=checkpoint_uri_for_adapter,  # URI now points to the specific latest checkpoint
            owner=training_request.owner or message.user_id,  # type: ignore
            base_model=training_request.model,  # This is the original base model ID like "unsloth/Qwen2.5-VL-32B-Instruct"
            epochs_trained=final_epochs_trained,
            examples_trained=(
                adapter_resource.examples_trained if adapter_resource else 0
            )
            + len(converted_dataset),
            last_trained=int(time.time()),
            lora=V1LoraParams(
                r=LORA_RANK,
                alpha=LORA_ALPHA,
                dropout=LORA_DROPOUT,
            ),
            labels=training_request.labels,
            api_key=message.api_key,
        )

        training.log(data=training_metrics)

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        # Extract metrics for TrainingResponse
        # Use .get() with defaults to avoid KeyError if metrics are missing
        final_loss = 0.0
        train_steps_per_second = 0.0
        train_samples_per_second = 0.0
        train_runtime = 0.0

        if training_metrics:
            log_history = training_metrics.get("log_history", [])
            if log_history:  # Get loss from the last step
                final_loss = log_history[-1].get(
                    "loss", log_history[-1].get("train_loss", 0.0)
                )

            # These specific keys might not be in log_history but directly in trainer_stats from SFTTrainer
            # train_lora_adapter doesn't directly return trainer_stats, so we rely on trainer_state.json
            # which might have slightly different structure for aggregated stats.
            # For now, let's use what's typically available or default to 0.
            train_steps_per_second = training_metrics.get(
                "train_steps_per_second", 0.0
            )  # This key might not exist directly
            train_samples_per_second = training_metrics.get(
                "train_samples_per_second", 0.0
            )  # This key might not exist
            train_runtime = training_metrics.get(
                "train_runtime", time.time() - time_start_train
            )  # Fallback to measured time

        return TrainingResponse(
            loss=final_loss,
            train_steps_per_second=train_steps_per_second,
            train_samples_per_second=train_samples_per_second,
            train_runtime=train_runtime,
            adapter=training_request.adapter,
            adapter_uri=adapter_weights_bucket_uri,  # Return the bucket URI for the adapter weights
        )
    except Exception as e:
        print(f"Error training unsloth: {e}")
        failure = True
        if training:
            print("\n >> marking training as failed due to exception")
            training.update(status=V1TrainingStatus.FAILED)
        # If an error occurs, we must still return a TrainingResponse or raise.
        # Raising the original error is often better for debugging.
        raise
    finally:
        print(
            f"finally block: training resource exists: {bool(training)}, failure: {failure}"
        )
        if training:
            if failure:
                if (
                    training.training.status != V1TrainingStatus.FAILED
                ):  # Avoid double update if already set
                    print("\n >> ensuring training is marked as FAILED in finally")
                    training.update(status=V1TrainingStatus.FAILED)
            else:
                if training.training.status != V1TrainingStatus.COMPLETED:
                    print("\n >> marking training as COMPLETED in finally")
                    training.update(status=V1TrainingStatus.COMPLETED)


def UnslothSFT(
    platform: str = "runpod",
    accelerators: List[str] = ["1:H100_SXM"],
    image: str = "ghcr.io/agentsea/orign/unsloth-train:e030adf",  # "public.ecr.aws/d8i6n0n1/orign/unsloth-trainer:e030adf",  # , # "us-docker.pkg.dev/agentsea-dev/orign/unsloth-train:latest"
    scale: V1Scale = scale,
    namespace: Optional[str] = None,
    env: Optional[List[V1EnvVar]] = None,
    config: Optional[NebuGlobalConfig] = None,
    hot_reload: bool = True,
    debug: bool = False,
    min_replicas: int = 1,
    max_replicas: int = 4,
    name: Optional[str] = None,
    wait_for_healthy: bool = True,
) -> Processor[TrainingRequest, TrainingResponse]:
    decorate = processor(
        image=image,
        # setup_script=setup_script,
        accelerators=accelerators,
        platform=platform,
        scale=scale,
        namespace=namespace,
        env=env,
        init_func=init,
        # execution_mode="subprocess",
        config=config,
        hot_reload=hot_reload,
        debug=debug,
        min_replicas=min_replicas,
        max_replicas=max_replicas,
        name=name,
        wait_for_healthy=wait_for_healthy,
    )
    return decorate(train_unsloth_sft)
