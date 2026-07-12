#!/usr/bin/env python3
"""Entry point for the file transfer application."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIREMENTS = ROOT / "requirements.txt"
VENV_DIR = ROOT / ".venv"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _has_pyqt6(python: str | Path = sys.executable) -> bool:
    result = subprocess.run(
        [str(python), "-c", "import PyQt6"],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, check=False).returncode


def _install_into(python: Path | str) -> bool:
    if not REQUIREMENTS.exists():
        print("ERROR: requirements.txt not found next to main.py.")
        return False
    code = _run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    return code == 0


def _create_venv() -> Path | None:
    print("Creating local virtual environment in .venv ...")
    code = _run([sys.executable, "-m", "venv", str(VENV_DIR)])
    if code != 0:
        print("ERROR: Could not create virtual environment.")
        print("Install Python with pip/venv support, then try again.")
        return None
    python = _venv_python()
    if not python.exists():
        print(f"ERROR: Expected venv Python at {python}")
        return None
    return python


def _relaunch(python: Path) -> None:
    print("Starting app with project virtual environment...")
    os.execv(str(python), [str(python), str(ROOT / "main.py"), *sys.argv[1:]])


def ensure_dependencies() -> None:
    """Make sure PyQt6 is available, installing into a local .venv if needed."""
    if _has_pyqt6():
        return

    print("PyQt6 is not installed for this Python. Setting up project .venv...")
    print(f"Current Python: {sys.executable}")

    python = _venv_python()
    if python.exists() and _has_pyqt6(python):
        _relaunch(python)
        return

    if not python.exists():
        created = _create_venv()
        if created is None:
            sys.exit(1)
        python = created

    if not _has_pyqt6(python):
        print("Installing dependencies into .venv ...")
        if not _install_into(python):
            print("ERROR: Failed to install dependencies.")
            print("Try manually:")
            print(f"  {python} -m pip install -r requirements.txt")
            sys.exit(1)

    if not _has_pyqt6(python):
        print("ERROR: PyQt6 still not available after install.")
        sys.exit(1)

    _relaunch(python)


if __name__ == "__main__":
    ensure_dependencies()
    from file_transfer.ui.main_window import run_app

    run_app()
