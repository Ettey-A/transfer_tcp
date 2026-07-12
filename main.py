#!/usr/bin/env python3  # Shebang: on Unix, run this file with Python 3 when executed directly
"""Entry point for the file transfer application."""  # Module docstring describing this file's purpose

import os  # Import OS helpers (detect Windows vs Linux, replace process with execv)
import subprocess  # Import subprocess to run pip/venv/python check commands
import sys  # Import sys for current Python path, exit codes, and command-line args
from pathlib import Path  # Import Path for filesystem path handling


ROOT = Path(__file__).resolve().parent  # Absolute path to the folder that contains this main.py
REQUIREMENTS = ROOT / "requirements.txt"  # Full path to the dependency list file
VENV_DIR = ROOT / ".venv"  # Full path to the project virtual environment folder


def _venv_python() -> Path:  # Return the Python executable inside the project .venv
    if os.name == "nt":  # True on Windows ("nt" = New Technology)
        return VENV_DIR / "Scripts" / "python.exe"  # Windows venv Python lives under Scripts\
    return VENV_DIR / "bin" / "python"  # Linux/macOS venv Python lives under bin/


def _has_pyqt6(python: str | Path = sys.executable) -> bool:  # Check if PyQt6 can be imported by a Python
    result = subprocess.run(  # Run a short Python one-liner in a child process
        [str(python), "-c", "import PyQt6"],  # Ask that Python to import PyQt6
        capture_output=True,  # Hide stdout/stderr from the console during the check
        check=False,  # Do not raise an exception if the import fails
    )
    return result.returncode == 0  # Success (0) means PyQt6 is installed for that Python


def _run(cmd: list[str]) -> int:  # Run a shell command and return its exit code
    print("+", " ".join(cmd))  # Print the command so the user can see what is running
    return subprocess.run(cmd, check=False).returncode  # Run it and return 0 on success, non-zero on failure


def _install_into(python: Path | str) -> bool:  # Install requirements into a given Python/venv
    if not REQUIREMENTS.exists():  # Stop if requirements.txt is missing
        print("ERROR: requirements.txt not found next to main.py.")  # Tell the user what is wrong
        return False  # Signal install failure
    code = _run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)])  # pip install -r requirements.txt
    return code == 0  # True if pip succeeded


def _create_venv() -> Path | None:  # Create a new .venv and return its Python path (or None on failure)
    print("Creating local virtual environment in .venv ...")  # Tell the user setup is starting
    code = _run([sys.executable, "-m", "venv", str(VENV_DIR)])  # Create .venv using current Python
    if code != 0:  # venv creation failed
        print("ERROR: Could not create virtual environment.")  # Explain the failure
        print("Install Python with pip/venv support, then try again.")  # Suggest a fix
        return None  # Signal failure to the caller
    python = _venv_python()  # Get expected path to the new venv's Python
    if not python.exists():  # The venv folder exists but Python binary is missing
        print(f"ERROR: Expected venv Python at {python}")  # Show the missing path
        return None  # Signal failure
    return python  # Return the working venv Python path


def _relaunch(python: Path) -> None:  # Restart this script using the venv Python
    print("Starting app with project virtual environment...")  # Tell the user we are switching Pythons
    os.execv(str(python), [str(python), str(ROOT / "main.py"), *sys.argv[1:]])  # Replace this process with venv Python running main.py


def ensure_dependencies() -> None:  # Make sure PyQt6 exists, creating/installing .venv if needed
    """Make sure PyQt6 is available, installing into a local .venv if needed."""  # Function docstring
    if _has_pyqt6():  # Current Python already has PyQt6
        return  # Nothing more to do; continue launching the app

    print("PyQt6 is not installed for this Python. Setting up project .venv...")  # Explain why setup starts
    print(f"Current Python: {sys.executable}")  # Show which Python was used to start the app

    python = _venv_python()  # Path where project venv Python should be
    if python.exists() and _has_pyqt6(python):  # .venv already exists and already has PyQt6
        _relaunch(python)  # Restart using that venv Python
        return  # Unreachable after execv, but kept for clarity

    if not python.exists():  # No project .venv yet
        created = _create_venv()  # Create a new virtual environment
        if created is None:  # Creation failed
            sys.exit(1)  # Exit the program with error code 1
        python = created  # Use the newly created venv Python

    if not _has_pyqt6(python):  # Venv exists but PyQt6 is still missing
        print("Installing dependencies into .venv ...")  # Tell the user install is starting
        if not _install_into(python):  # Try pip install from requirements.txt
            print("ERROR: Failed to install dependencies.")  # Install failed
            print("Try manually:")  # Suggest a manual command
            print(f"  {python} -m pip install -r requirements.txt")  # Exact command to run by hand
            sys.exit(1)  # Exit with error

    if not _has_pyqt6(python):  # Final safety check after install
        print("ERROR: PyQt6 still not available after install.")  # Install claimed success but import still fails
        sys.exit(1)  # Exit with error

    _relaunch(python)  # Restart this script under the venv Python that has PyQt6


if __name__ == "__main__":  # Only run this block when the file is executed directly (not imported)
    ensure_dependencies()  # Ensure PyQt6/venv are ready before importing the GUI
    from file_transfer.ui.main_window import run_app  # Import GUI starter only after dependencies exist

    run_app()  # Launch the PyQt6 application window and event loop
