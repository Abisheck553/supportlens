"""Create an isolated Python environment. Uses a bundled UI when one is present."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
if sys.version_info < (3, 11):
    raise SystemExit("SupportLens needs Python 3.11 or newer.")
python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if not python.exists():
    subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
subprocess.run(
    [str(python), "-m", "pip", "install", "-r", "requirements.lock"], check=True
)
if not (ROOT / "dist/index.html").exists():
    pnpm = shutil.which("pnpm")
    if not pnpm:
        raise SystemExit(
            "Python is ready. Install Node.js 22+ and pnpm 11.25.0, then run: pnpm install --frozen-lockfile && pnpm build"
        )
    subprocess.run([pnpm, "install", "--frozen-lockfile"], check=True)
    subprocess.run([pnpm, "build"], check=True)
print("\nSupportLens is ready. Start it with: python3 scripts/run.py")
