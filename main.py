#!/usr/bin/env python3  # Shebang: run this file with Python 3 when executed directly
"""Entry point for the file transfer application."""  # Module docstring describing this file's purpose

from file_transfer.ui.main_window import run_app  # Import the function that starts the GUI


if __name__ == "__main__":  # Only run when this file is executed directly (not imported)
    run_app()  # Launch the PyQt6 application window and event loop
