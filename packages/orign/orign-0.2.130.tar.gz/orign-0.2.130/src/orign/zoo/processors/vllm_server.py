import asyncio
import fcntl
import json
import os
import shutil
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Optional

from chatmux.openai import (
    ChatRequest,
    ChatResponse,
    CompletionChoice,
    Logprobs,
    ResponseMessage,
)
from orign import Adapter

from nebulous import (
    Bucket,
    Message,
    Processor,
    V1EnvVar,
    is_allowed,
    processor,
)
from nebulous.config import GlobalConfig as NebuGlobalConfig

if TYPE_CHECKING:
    from vllm import LLM  # type: ignore
    from vllm.lora.request import LoRARequest  # type: ignore

# VLLM doesn't require a complex setup script like unsloth.
# We assume the container image has VLLM and its dependencies installed.
# A simple setup could be:
# setup_script = """
# apt update && apt install -y git
# pip install vllm qwen-vl-utils chatmux orign sentencepiece transformers
# """

BASE_MODEL_ID = os.getenv("BASE_MODEL_ID", "Qwen/Qwen2.5-VL-32B-Instruct")


def _get_model_prompt(
    model_id: str, messages: list, processor: Any
) -> tuple[str, Optional[dict]]:
    """
    Constructs the prompt and multi-modal data for a given model.
    """
    from vllm.multimodal.utils import fetch_image  # type: ignore

    image_urls = []
    # Extract image URLs and text from messages
    for message in messages:
        if isinstance(message.get("content"), list):
            for part in message["content"]:
                if part.get("type") == "image_url":
                    image_url = part["image_url"]["url"]
                    # vLLM's fetch_image can handle data URIs
                    image_urls.append(image_url)

    image_data = [fetch_image(url) for url in image_urls]
    multi_modal_data = {"image": image_data} if image_data else None

    prompt = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    return prompt, multi_modal_data


# --- LRU Disk Cache Management (Adapted from qwen_server.py) ---
LRU_METADATA_FILE = (
    "/nebulous/cache/lru_disk_cache_qwen_vllm_server.json"  # Server-specific metadata
)
ADAPTER_CACHE_DIR_BASE = "/nebulous/cache/adapters"  # Shared with trainer
SFT_RUNS_DIR_BASE = (
    "./sft_runs_server_placeholder"  # Placeholder, server doesn't manage these directly
)
LRU_LOCK_FILE_QWEN = (
    "/nebulous/cache/lru_disk_cache_qwen_vllm_server.lock"  # Server-specific lock file
)

DEFAULT_MAX_ADAPTER_STORAGE_MB = float(
    os.getenv("MAX_ADAPTER_STORAGE_MB", 10 * 1024)
)  # 10 GB
DEFAULT_MAX_SFTRUN_STORAGE_MB = float(
    os.getenv("MAX_SFTRUN_STORAGE_MB", 1 * 1024)
)  # 1 GB (low, as server shouldn't store these)

# Global variable to hold loaded metadata
_lru_disk_metadata = {"adapters": [], "sft_runs": []}


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
            except json.JSONDecodeError:
                print(
                    f"[METRIC] [LRU Disk Cache] Warning: Could not decode metadata from {LRU_METADATA_FILE}. Starting fresh."
                )
                _lru_disk_metadata = {"adapters": [], "sft_runs": []}
        else:
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
                current_disk_metadata = {"adapters": [], "sft_runs": []}  # Fallback

        _lru_disk_metadata = current_disk_metadata

        if item_type not in _lru_disk_metadata:
            _lru_disk_metadata[item_type] = []

        item_list = _lru_disk_metadata[item_type]
        found_item = next(
            (item for item in item_list if item.get("name") == item_name), None
        )

        current_size_mb = _get_dir_size_mb(item_path)
        current_time = int(time.time())

        if current_size_mb == 0 and not os.path.exists(item_path):
            if found_item:
                item_list.remove(found_item)
                print(
                    f"[METRIC] [LRU Disk Cache] Removed non-existent item '{item_name}' ({item_type}) from metadata."
                )
            with open(LRU_METADATA_FILE, "w") as f_write:
                json.dump(_lru_disk_metadata, f_write, indent=4)
            return

        if found_item:
            found_item["last_accessed_ts"] = current_time
            found_item["size_mb"] = current_size_mb
            found_item["path"] = item_path
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

        with open(LRU_METADATA_FILE, "w") as f_write:
            json.dump(_lru_disk_metadata, f_write, indent=4)

    except Exception as e:
        print(
            f"[METRIC] [LRU Disk Cache] Error during _update_item_access for {item_name}: {e}"
        )
    finally:
        _release_lock(lock_fd)
    func_duration = time.time() - func_start_time
    if func_duration > 0.01:
        print(
            f"[METRIC] [LRU Disk Cache] Total _update_item_access for '{item_name}' ({item_type}) took {func_duration:.4f} seconds."
        )


async def _ensure_storage_limits():
    """Ensures storage usage is within limits, evicting LRU items if necessary."""
    global _lru_disk_metadata, state

    lock_fd = _acquire_lock(LRU_LOCK_FILE_QWEN)
    if lock_fd is None:
        print(
            "[METRIC] [LRU Disk Cache] Warning: Could not acquire lock for _ensure_storage_limits. Operation skipped."
        )
        return

    try:
        # Load latest metadata
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
                current_disk_metadata = {"adapters": [], "sft_runs": []}

        _lru_disk_metadata = current_disk_metadata

        max_adapter_storage_mb = float(
            os.getenv("MAX_ADAPTER_STORAGE_MB", DEFAULT_MAX_ADAPTER_STORAGE_MB)
        )
        metadata_changed = False

        # --- Manage Adapters ---
        adapters = sorted(
            _lru_disk_metadata.get("adapters", []),
            key=lambda x: x.get("last_accessed_ts", 0),  # type: ignore
        )
        current_adapter_size_mb = sum(item.get("size_mb", 0) for item in adapters)

        adapters_to_keep = []
        evicted_count = 0
        for item in adapters:
            item_name = item.get("name")
            item_path = item.get("path")
            item_size = item.get("size_mb", 0)

            # Evict if over budget or path missing
            if current_adapter_size_mb > max_adapter_storage_mb or not (
                item_path and os.path.exists(item_path)
            ):
                print(
                    f"[METRIC] [LRU Disk Cache] Evicting adapter '{item_name}' (size: {item_size:.2f} MB)"
                )
                if item_path and os.path.exists(item_path):
                    try:
                        shutil.rmtree(item_path)
                        current_adapter_size_mb -= item_size
                    except OSError as e:
                        print(
                            f"[METRIC] [LRU Disk Cache] Error deleting adapter directory {item_path}: {e}"
                        )
                        adapters_to_keep.append(item)  # Keep if deletion fails
                        continue

                # Unload from VLLM engine
                if item_name in state.loaded_adapters:
                    lora_id_to_remove = state.loaded_adapters[item_name]
                    await asyncio.to_thread(state.engine.remove_lora, lora_id_to_remove)
                    del state.loaded_adapters[item_name]
                    print(
                        f"[METRIC] [VLLM] Unloaded adapter '{item_name}' from engine."
                    )

                evicted_count += 1
                metadata_changed = True
            else:
                adapters_to_keep.append(item)

        _lru_disk_metadata["adapters"] = sorted(
            adapters_to_keep,
            key=lambda x: x.get("last_accessed_ts", 0),  # type: ignore
            reverse=True,
        )
        if evicted_count > 0:
            print(f"[METRIC] [LRU Disk Cache] Evicted {evicted_count} adapters.")

        if metadata_changed:
            with open(LRU_METADATA_FILE, "w") as f_write:
                json.dump(_lru_disk_metadata, f_write, indent=4)
    except Exception as e:
        print(f"[METRIC] [LRU Disk Cache] Error during _ensure_storage_limits: {e}")
    finally:
        _release_lock(lock_fd)


# --- End LRU Disk Cache Management ---


@dataclass
class VLLMInferenceState:
    engine: "LLM"
    base_model_id: str
    tokenizer: Any
    processor: Any
    loaded_adapters: dict  # maps adapter_name -> lora_int_id


def init():
    """
    Initializes the VLLM engine and other components.
    This function is called once per worker.
    """
    from vllm import LLM  # type: ignore

    init_start_time = time.time()
    from transformers import AutoProcessor, AutoTokenizer  # type: ignore

    if "state" in globals():
        print("VLLM state already loaded by an earlier worker.")
        return

    print("--- Initializing VLLM Engine ---")

    engine = LLM(
        model=BASE_MODEL_ID,
        tokenizer=BASE_MODEL_ID,
        trust_remote_code=True,
        enable_lora=True,
        max_loras=int(os.getenv("VLLM_MAX_LORAS", "1")),
        max_model_len=26_214,
        gpu_memory_utilization=0.97,
        enforce_eager=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    try:
        processor = AutoProcessor.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    except Exception:
        processor = tokenizer

    global state
    state = VLLMInferenceState(
        engine=engine,
        base_model_id=BASE_MODEL_ID,
        tokenizer=tokenizer,
        processor=processor,
        loaded_adapters={},  # _name -> int_id
    )

    # --- LRU Disk Cache Init ---
    _load_lru_metadata()
    # Run async function in a sync context

    asyncio.run(_ensure_storage_limits())

    print(
        f"[METRIC] Total init() function execution time: {time.time() - init_start_time:.2f} seconds."
    )


async def manage_adapter_vllm(
    adapter_id: str, adapter_to_load: Any, bucket: Any
) -> Optional["LoRARequest"]:
    """
    Manages adapter lifecycle for VLLM: checks cache, downloads if needed, and loads into engine.
    Returns a LoRARequest if the adapter is ready for inference.
    """
    from vllm.lora.request import LoRARequest  # type: ignore

    global state
    adapter_name = adapter_id

    # Check if adapter is already loaded in VLLM
    if adapter_name in state.loaded_adapters:
        # Optionally, check for version updates and reload if necessary
        lora_int_id = state.loaded_adapters[adapter_name]
        adapter_path = os.path.join(ADAPTER_CACHE_DIR_BASE, adapter_name)
        _update_item_access(adapter_name, "adapters", adapter_path)
        print(f"[METRIC] [VLLM] Adapter '{adapter_name}' already loaded.")
        return LoRARequest(
            lora_name=adapter_name,
            lora_int_id=lora_int_id,
            lora_local_path=adapter_path,
        )

    # Adapter not in engine, check if on disk
    adapter_path = os.path.join(ADAPTER_CACHE_DIR_BASE, adapter_name)
    if not os.path.exists(os.path.join(adapter_path, "adapter_config.json")):
        print(
            f"[METRIC] [VLLM] Adapter '{adapter_name}' not found locally. Downloading..."
        )
        if os.path.exists(adapter_path):
            shutil.rmtree(adapter_path)
        os.makedirs(adapter_path, exist_ok=True)
        try:
            bucket.copy(adapter_to_load.model_uri, adapter_path)
            print(f"[METRIC] [VLLM] Downloaded adapter '{adapter_name}'.")
        except Exception as e:
            print(f"Error downloading adapter {adapter_name}: {e}")
            return None

    # Update access time *before* loading, so it's not immediately evicted
    _update_item_access(adapter_name, "adapters", adapter_path)

    # Load into VLLM engine
    try:
        # Find a unique int ID for the LoRA
        lora_int_id = 1
        while lora_int_id in state.loaded_adapters.values():
            lora_int_id += 1

        lora_request = LoRARequest(
            lora_name=adapter_name,
            lora_int_id=lora_int_id,
            lora_local_path=adapter_path,
        )
        await asyncio.to_thread(state.engine.add_lora, lora_request)
        state.loaded_adapters[adapter_name] = lora_int_id
        print(
            f"[METRIC] [VLLM] Successfully loaded adapter '{adapter_name}' with ID {lora_int_id}."
        )

        # After loading, check if we are over storage limits
        await _ensure_storage_limits()

        return lora_request
    except Exception as e:
        print(
            f"[ERROR] [VLLM] Failed to load adapter '{adapter_name}' into VLLM engine: {e}"
        )
        # Clean up failed download/load
        if os.path.exists(adapter_path):
            shutil.rmtree(adapter_path)
        return None


async def infer_qwen_vl_vllm(message: Message[ChatRequest]) -> ChatResponse:
    overall_inference_start_time = time.time()
    from vllm import SamplingParams  # type: ignore
    from vllm.lora.request import LoRARequest  # type: ignore
    from vllm.utils import random_uuid  # type: ignore

    global state
    print("--- VLLM INFERENCE REQUEST ---")

    content = message.content
    if not content:
        raise ValueError("No content provided")

    lora_request: Optional[LoRARequest] = None
    model_id = content.model or BASE_MODEL_ID

    if model_id and model_id != BASE_MODEL_ID:
        model_parts = model_id.split("/")
        namespace = model_parts[0] if len(model_parts) == 2 else message.handle
        name = model_parts[1] if len(model_parts) == 2 else model_parts[0]
        adapter_name = f"{namespace}/{name}"

        print(f"Request for adapter: '{adapter_name}'")
        adapters = Adapter.get(namespace=namespace, name=name, api_key=message.api_key)
        if not adapters:
            raise ValueError(f"Adapter '{adapter_name}' not found")

        adapter_to_load = adapters[0]
        if not is_allowed(
            adapter_to_load.metadata.owner, message.user_id, message.orgs
        ):
            raise ValueError("You are not allowed to use this adapter")

        bucket: Any = Bucket()
        lora_request = await manage_adapter_vllm(adapter_name, adapter_to_load, bucket)
        if not lora_request:
            raise RuntimeError(f"Failed to load or prepare adapter '{adapter_name}'")
    else:
        model_id = BASE_MODEL_ID

    # Prepare prompt and inputs
    messages_oai = content.model_dump()["messages"]

    # Use the helper to get model-specific prompt and image data
    text_prompt, multi_modal_data = _get_model_prompt(
        model_id, messages_oai, state.processor
    )

    sampling_params = SamplingParams(
        max_tokens=content.max_tokens or 1024,
        temperature=content.temperature or 0.7,
        top_p=content.top_p or 1.0,
        stop=content.stop,
    )

    # Generate text
    outputs = await asyncio.to_thread(
        state.engine.generate,
        prompts=[text_prompt],
        sampling_params=sampling_params,
        lora_request=lora_request,
        multi_modal_data=multi_modal_data,
    )

    final_output = outputs[0]

    output_text = final_output.outputs[0].text
    print(f"Generated text: {output_text[:100]}...")

    response = ChatResponse(
        id=random_uuid(),
        created=int(time.time()),
        model=model_id,
        object="chat.completion",
        choices=[
            CompletionChoice(
                index=0,
                finish_reason="stop",
                message=ResponseMessage(role="assistant", content=output_text),  # type: ignore
                logprobs=Logprobs(content=[]),
            )
        ],
        service_tier=None,
        system_fingerprint=None,
        usage=None,
    )

    print(
        f"--- VLLM Request processed in {time.time() - overall_inference_start_time:.2f}s ---"
    )
    return response


def QwenVLServer(
    platform: str = "runpod",
    accelerators: List[str] = ["1:A100_SXM"],
    model: str = "Qwen/Qwen2.5-VL-32B-Instruct",  # Default to a standard VLLM-compatible model
    image: str = "ghcr.io/agentsea/orign/unsloth-infer:f23ec7f",  # A new image for VLLM
    namespace: Optional[str] = None,
    env: Optional[List[V1EnvVar]] = None,
    config: Optional[NebuGlobalConfig] = None,
    # Hot-reload can interfere with the Nebulous file-sync mechanism because rclone
    # briefly removes/renames the source files while syncing, causing the consumer
    # to think the entry-point is missing.  Disable it by default; callers can
    # still opt-in explicitly when they know their environment supports it.
    hot_reload: bool = False,
    debug: bool = False,
    min_replicas: int = 1,
    max_replicas: int = 4,
    name: Optional[str] = None,
    wait_for_healthy: bool = True,
) -> Processor[ChatRequest, ChatResponse]:
    if env:
        env.append(V1EnvVar(key="BASE_MODEL_ID", value=model))
    else:
        env = [V1EnvVar(key="BASE_MODEL_ID", value=model)]

    decorate = processor(
        image=image,
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
    return decorate(infer_qwen_vl_vllm)
