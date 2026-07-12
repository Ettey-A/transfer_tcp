"""Background listener that accepts incoming file transfers."""  # Module docstring: describes this file's purpose

import socket  # Import TCP networking support (bind, listen, accept, close)
import threading  # Import threads so listening and file handling can run in the background
import time  # Import time.sleep to avoid a busy loop while the listener is paused
from pathlib import Path  # Import Path for save-directory path handling
from typing import Callable  # Import Callable for typing optional callback functions

from file_transfer.constants import DEFAULT_PORT  # Import the shared default TCP port (5050)
from file_transfer.protocol import recv_file, recv_header  # Import helpers to read headers and save files


class IncomingListener:  # Define the class that waits for senders and receives files
    """Listens for senders and saves files. Runs while the app is open."""  # Class docstring

    def __init__(  # Constructor: set up save location, port, callbacks, and internal state
        self,  # The IncomingListener instance being created
        save_dir: Path,  # Folder where received files will be written (e.g. Downloads)
        port: int = DEFAULT_PORT,  # TCP port to listen on; defaults to 5050
        on_log: Callable[[str], None] | None = None,  # Optional callback for status/log messages
        on_progress: Callable[[int, int], None] | None = None,  # Optional callback for (bytes_done, total_bytes)
        on_file_received: Callable[[Path], None] | None = None,  # Optional callback when a file is saved
        on_started: Callable[[], None] | None = None,  # Optional callback when listening successfully starts
        on_error: Callable[[str], None] | None = None,  # Optional callback when startup fails
    ) -> None:  # Constructor returns nothing
        self.save_dir = Path(save_dir)  # Store save directory as a Path object
        self.port = port  # Store the listen port number
        self.on_log = on_log  # Store the log callback (or None)
        self.on_progress = on_progress  # Store the progress callback (or None)
        self.on_file_received = on_file_received  # Store the file-received callback (or None)
        self.on_started = on_started  # Store the started callback (or None)
        self.on_error = on_error  # Store the error callback (or None)

        self._sock: socket.socket | None = None  # Will hold the listening socket; None until start()
        self._thread: threading.Thread | None = None  # Will hold the background listen thread; None until start()
        self._stop = threading.Event()  # Event flag used to tell the listen loop to exit
        self._paused = threading.Event()  # Event flag used to temporarily skip accepting connections

    @property  # Make is_running usable like an attribute: listener.is_running
    def is_running(self) -> bool:  # Returns True if the background listen thread is still alive
        return self._thread is not None and self._thread.is_alive()  # Thread exists and has not finished

    def _log(self, message: str) -> None:  # Internal helper to send a log message to the UI if wired
        if self.on_log:  # Only call if a log callback was provided
            self.on_log(message)  # Forward the message to the callback

    def start(self) -> None:  # Start listening for incoming transfers in a background thread
        if self.is_running:  # If already listening, do nothing
            return  # Exit early to avoid starting a second listener
        self.save_dir.mkdir(parents=True, exist_ok=True)  # Create save folder (and parents) if missing
        self._stop.clear()  # Clear stop flag so the loop is allowed to run
        self._paused.clear()  # Clear pause flag so accept() is allowed
        self._thread = threading.Thread(target=self._run, daemon=True)  # Create daemon thread that runs _run()
        self._thread.start()  # Start the background thread (begins listening)

    def stop(self) -> None:  # Stop listening and clean up the socket/thread
        self._stop.set()  # Signal the listen loop to exit
        if self._sock:  # If a listening socket exists
            try:  # Try to close it (this also unblocks accept())
                self._sock.close()  # Close the listening socket
            except OSError:  # Ignore close errors (socket may already be closed)
                pass  # Do nothing on close failure
        if self._thread and self._thread.is_alive():  # If the listen thread is still running
            self._thread.join(timeout=2)  # Wait up to 2 seconds for the thread to finish
        self._sock = None  # Forget the socket reference
        self._thread = None  # Forget the thread reference

    def pause(self) -> None:  # Temporarily stop accepting new connections
        """Temporarily stop accepting so this machine can send on the same port."""  # Method docstring
        self._paused.set()  # Set paused flag so the loop skips accept()

    def resume(self) -> None:  # Allow accepting connections again after pause
        self._paused.clear()  # Clear paused flag so the loop resumes accept()

    def _run(self) -> None:  # Background thread body: bind, listen, and accept senders
        try:  # Catch bind/listen failures (e.g. port already in use)
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create an IPv4 TCP socket
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow quick rebinding after restart
            self._sock.bind(("0.0.0.0", self.port))  # Listen on all network interfaces at self.port
            self._sock.listen(5)  # Start listening; allow up to 5 pending connections
            self._sock.settimeout(0.5)  # Make accept() time out every 0.5s so we can check stop/pause
            if self.on_started:  # If a started callback was provided
                self.on_started()  # Notify UI that listening has begun
            self._log(f"Ready to receive on port {self.port}")  # Log that we are ready

            while not self._stop.is_set():  # Keep looping until stop() is called
                if self._paused.is_set():  # If pause() was called
                    time.sleep(0.2)  # Sleep briefly to avoid burning CPU
                    continue  # Skip accept() and check flags again
                try:  # Try to accept one incoming connection
                    conn, addr = self._sock.accept()  # Block (up to timeout) for a sender connection
                except TimeoutError:  # No connection within 0.5 seconds
                    continue  # Loop again and re-check stop/pause
                except OSError:  # Socket closed or other accept error (often during stop())
                    break  # Exit the accept loop
                self._log(f"Incoming from {addr[0]}")  # Log the sender's IP address
                threading.Thread(  # Start a new thread to handle this one sender
                    target=self._handle,  # Run _handle() in that thread
                    args=(conn, addr),  # Pass the connected socket and address
                    daemon=True,  # Daemon thread exits when the app exits
                ).start()  # Begin handling this transfer immediately
        except OSError as exc:  # Bind/listen failed (port busy, permission denied, etc.)
            message = f"Could not start receiver: {exc}"  # Build a user-readable error message
            self._log(message)  # Log the error
            if self.on_error:  # If an error callback was provided
                self.on_error(message)  # Notify UI of the failure
        finally:  # Always clean up the listening socket when _run ends
            if self._sock:  # If the socket still exists
                try:  # Try to close it
                    self._sock.close()  # Close the listening socket
                except OSError:  # Ignore close errors
                    pass  # Do nothing on close failure
                self._sock = None  # Clear the socket reference

    def _handle(self, conn: socket.socket, addr: tuple[str, int]) -> None:  # Handle one sender connection
        with conn:  # Ensure the connection socket is closed when this block ends
            try:  # Catch transfer/protocol errors for this connection
                while True:  # Keep reading messages until sender says "done" or error
                    header = recv_header(conn)  # Read the next length-prefixed JSON header from the sender
                    if header.get("type") == "done":  # Sender finished sending all files
                        self._log(f"Transfer finished from {addr[0]}")  # Log completion with sender IP
                        break  # Exit the message loop for this connection
                    if header.get("type") != "file":  # Unexpected message type
                        break  # Stop handling this connection
                    saved = recv_file(  # Receive the file bytes and write them to disk
                        conn,  # Use this TCP connection
                        self.save_dir,  # Save into the configured downloads folder
                        header=header,  # Pass the already-read header (filename/size)
                        on_progress=self.on_progress,  # Forward progress updates to the UI
                    )
                    self._log(f"Saved: {saved.name}")  # Log the saved filename
                    if self.on_file_received:  # If a file-received callback was provided
                        self.on_file_received(saved)  # Notify UI with the saved file path
            except (ConnectionError, OSError, ValueError) as exc:  # Network or protocol failure
                self._log(f"Receive error: {exc}")  # Log the error for this connection
