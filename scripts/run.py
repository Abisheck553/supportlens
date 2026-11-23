"""Launch the UI, API, and configured local model. Stop owned services on exit."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import webbrowser
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if not PYTHON.exists():
    raise SystemExit("Run python3 scripts/setup.py first.")
if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
    os.execv(str(PYTHON), [str(PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])

from dotenv import load_dotenv
from local_ai import ensure_ollama, read_json, stop_owned


def main():
    parser = argparse.ArgumentParser(description="Run SupportLens locally")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--open", action="store_true", help="Open your browser when ready"
    )
    parser.add_argument(
        "--no-ai", action="store_true", help="Use source excerpts without models"
    )
    args = parser.parse_args()
    if not (ROOT / "dist/index.html").exists():
        raise SystemExit(
            "Build the interface first: pnpm install --frozen-lockfile && pnpm build"
        )
    os.chdir(ROOT)
    load_dotenv(ROOT / ".env")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "backend")
    env["HF_HUB_DISABLE_TELEMETRY"] = "1"
    if args.no_ai:
        env.update(ANSWER_PROVIDER="extractive", ENABLE_SEMANTIC="false")
    model_process = None
    app_process = None
    try:
        if env.get("ANSWER_PROVIDER") == "ollama":
            base = env.get("OLLAMA_BASE_URL", "http://127.0.0.1:11435")
            model_process = ensure_ollama(ROOT, base)
            model = env.get("OLLAMA_MODEL", "qwen3:4b-instruct")
            available = {
                m["name"] for m in read_json(base.rstrip("/") + "/api/tags")["models"]
            }
            if model not in available:
                raise RuntimeError(
                    f"Model {model} is missing. Run python3 scripts/setup_ai.py."
                )
        url = f"http://127.0.0.1:{args.port}"
        print(f"\nSupportLens: {url}\nPress Ctrl+C to stop.\n", flush=True)
        app_process = subprocess.Popen(
            [
                str(PYTHON),
                "-m",
                "uvicorn",
                "supportlens.main:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(args.port),
            ],
            cwd=ROOT,
            env=env,
        )
        if args.open:

            def open_when_ready():
                for _ in range(80):
                    if app_process.poll() is not None:
                        return
                    try:
                        with urlopen(url + "/api/health", timeout=1):
                            webbrowser.open(url)
                            return
                    except OSError:
                        time.sleep(0.25)

            threading.Thread(target=open_when_ready, daemon=True).start()
        code = app_process.wait()
        if code:
            raise SystemExit(code)
    except KeyboardInterrupt:
        pass
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    finally:
        stop_owned(app_process)
        stop_owned(model_process)


if __name__ == "__main__":
    main()
