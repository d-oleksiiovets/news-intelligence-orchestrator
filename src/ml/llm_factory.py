import subprocess
import sys
import requests
import time
import atexit
import os
from pathlib import Path

from src.config.settings import settings
from src.ml.remote_llm import RemoteLLMEngine
from src.ml.local_llm import LocalLLMEngine
from src.ml.base_llm import BaseLLMEngine
from src.ml.model_downloader import ensure_model_file
from src.config.logger import StatusLog

_LLM_SERVER_PROCESS = None

def _llm_server_runner(llm_settings):
    global _LLM_SERVER_PROCESS

    model_path = llm_settings["local"]["model_path"]
    model_url = llm_settings["local"].get("model_url")
    n_ctx = llm_settings["local"]["n_ctx"]
    n_gpu_layers = llm_settings["local"]["n_gpu_layers"]
    url = llm_settings["local"]["url"]

    resolved_model_path = ensure_model_file(model_path, model_url)

    if os.name != "nt":
        subprocess.run(["pkill", "-f", "llama_cpp.server"], capture_output=True, check=False)

    cmd = [
        sys.executable, "-m", "llama_cpp.server",
        "--model", str(Path(resolved_model_path)), "--n_ctx", str(n_ctx),
        "--n_gpu_layers", str(n_gpu_layers)
    ]

    StatusLog.info("Starting local LLM server...")
    server_env = os.environ.copy()
    server_env.pop("LLAMA_API_KEY", None)
    server_env.pop("OPENAI_API_KEY", None)
    server_env.pop("API_KEY", None)
    _LLM_SERVER_PROCESS = subprocess.Popen(cmd, env=server_env)

    for _ in range(30):
        try:
            requests.get(f"{url}/health", timeout=2)
            StatusLog.success("Local LLM server is ready.")
            return
        except requests.ConnectionError:
            time.sleep(2)

    raise RuntimeError("Local LLM server failed to start in 60 seconds.")


def stop_llm_server():
    global _LLM_SERVER_PROCESS

    if _LLM_SERVER_PROCESS is None:
        return

    if _LLM_SERVER_PROCESS.poll() is not None:
        _LLM_SERVER_PROCESS = None
        return

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(_LLM_SERVER_PROCESS.pid)],
                capture_output=True,
                check=False,
            )
        else:
            _LLM_SERVER_PROCESS.terminate()
        _LLM_SERVER_PROCESS.wait(timeout=10)
    except Exception:
        _LLM_SERVER_PROCESS.kill()
    finally:
        _LLM_SERVER_PROCESS = None


atexit.register(stop_llm_server)

def create_llm_engine(llm_settings: dict) -> BaseLLMEngine:
    # Use remote LLM only if API_KEY is set and is not empty/none
    if settings.API_KEY:
        return RemoteLLMEngine(llm_settings)
    
    # Otherwise start local LLM server
    _llm_server_runner(llm_settings)
    return LocalLLMEngine(llm_settings)