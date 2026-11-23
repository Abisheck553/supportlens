"""Shared local model lifecycle helpers. Never starts a network-facing service."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from urllib.parse import urlparse
from urllib.request import urlopen


def read_json(url, timeout=2):
    with urlopen(url, timeout=timeout) as response:
        return json.load(response)


def find_ollama(root):
    candidates = [
        root / ".runtime/ollama/ollama",
        shutil.which("ollama"),
        "/Applications/Ollama.app/Contents/Resources/ollama",
    ]
    return next((str(p) for p in candidates if p and Path(p).is_file()), None)


def ensure_ollama(root, base_url):
    try:
        read_json(base_url.rstrip("/") + "/api/version")
        return None
    except (OSError, ValueError):
        pass
    parsed = urlparse(base_url)
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("The configured remote model service is unavailable.")
    binary = find_ollama(root)
    if not binary:
        raise RuntimeError(
            "Install the local AI setup first: python3 scripts/setup_ai.py"
        )
    runtime = root / ".runtime"
    runtime.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update(
        OLLAMA_HOST=parsed.netloc,
        OLLAMA_NO_CLOUD="1",
        OLLAMA_CONTEXT_LENGTH="4096",
        OLLAMA_MODELS=str(runtime / "ollama-models"),
    )
    with (runtime / "ollama.log").open("a") as log:
        process = subprocess.Popen(
            [binary, "serve"], cwd=root, env=env, stdout=log, stderr=log
        )
    for _ in range(80):
        try:
            read_json(base_url.rstrip("/") + "/api/version")
            return process
        except (OSError, ValueError):
            if process.poll() is not None:
                raise RuntimeError("Ollama could not start. See .runtime/ollama.log.")
            time.sleep(0.25)
    process.terminate()
    raise RuntimeError("Timed out starting Ollama. See .runtime/ollama.log.")


def stop_owned(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
