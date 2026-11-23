"""One-time local AI setup; model weights stay outside Git and release archives."""

import argparse
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
from urllib.request import urlretrieve

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
OLLAMA_URL = (
    "https://github.com/ollama/ollama/releases/download/v0.40.17/ollama-darwin.tgz"
)
OLLAMA_SHA256 = "4b9db20d077c5a1e52fb4a6f2e6791f76ae945fd07c9b1a5647c82e927826653"
EMBEDDING_REPO = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3:4b-instruct")
    args = parser.parse_args()
    if not PYTHON.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/setup.py")], check=True)
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        os.execv(
            str(PYTHON), [str(PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]]
        )
    os.chdir(ROOT)
    subprocess.run(
        [str(PYTHON), "-m", "pip", "install", "-r", "requirements-ai.lock"], check=True
    )
    os.environ["HF_HOME"] = str(ROOT / ".runtime/huggingface")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    from dotenv import set_key
    from huggingface_hub import snapshot_download
    from local_ai import ensure_ollama, find_ollama, stop_owned
    import httpx

    runtime = ROOT / ".runtime"
    runtime.mkdir(exist_ok=True)
    if not find_ollama(ROOT):
        if platform.system() != "Darwin":
            raise SystemExit(
                "Install Ollama from https://ollama.com/download, then rerun this command."
            )
        archive = runtime / "ollama-darwin.tgz"
        print("Downloading the official Ollama runtime…", flush=True)
        urlretrieve(OLLAMA_URL, archive)
        with archive.open("rb") as data:
            if hashlib.file_digest(data, "sha256").hexdigest() != OLLAMA_SHA256:
                raise SystemExit("Ollama download failed its checksum check.")
        destination = runtime / "ollama"
        destination.mkdir(exist_ok=True)
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                target = (destination / member.name).resolve()
                if not target.is_relative_to(destination.resolve()):
                    raise SystemExit("Unexpected archive path.")
                if member.issym() or member.islnk():
                    link = (target.parent / member.linkname).resolve()
                    if not link.is_relative_to(destination.resolve()):
                        raise SystemExit("Unexpected archive link.")
            tar.extractall(destination)
        archive.unlink()
    print("Downloading the pinned embedding model…", flush=True)
    snapshot_download(
        EMBEDDING_REPO,
        revision=EMBEDDING_REVISION,
        local_dir=runtime / "minilm",
        allow_patterns=["*.json", "*.txt", "model.safetensors", "1_Pooling/*"],
    )
    base = "http://127.0.0.1:11435"
    owned = ensure_ollama(ROOT, base)
    try:
        print(f"Downloading {args.model}; this can take several minutes…", flush=True)
        response = httpx.post(
            base + "/api/pull",
            json={"model": args.model, "stream": False},
            timeout=3600,
        )
        response.raise_for_status()
        if response.json().get("status") != "success":
            raise RuntimeError("Model download did not report success.")
    finally:
        stop_owned(owned)
    for key, value in {
        "ANSWER_PROVIDER": "ollama",
        "OLLAMA_BASE_URL": base,
        "OLLAMA_MODEL": args.model,
        "ENABLE_SEMANTIC": "true",
        "EMBEDDING_MODEL": ".runtime/minilm",
    }.items():
        set_key(ROOT / ".env", key, value)
    print(
        "Local AI is configured. Start SupportLens with python3 scripts/run.py --open"
    )


if __name__ == "__main__":
    main()
