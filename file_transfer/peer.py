"""Peer-to-peer file transfer without a persistent server."""  # Module docstring for P2P connection logic

import socket  # Standard library for TCP socket connections
import time  # Used for connection timeouts and retry delays
from pathlib import Path  # Used for file path handling
from typing import Callable, Literal  # Type hints for callbacks and role string

from file_transfer.constants import DEFAULT_PORT  # Default TCP port (5050) shared by all peers
from file_transfer.protocol import recv_file, recv_header, send_done, send_file  # Low-level protocol helpers

Role = Literal["send", "receive"]  # Type alias: peer role is either sending or receiving files


class Peer:  # Main class that handles direct peer-to-peer file transfers
    """Connect directly to another peer and transfer files."""  # Class docstring

    def __init__(  # Constructor: set up optional callback functions for UI updates
        self,
        on_log: Callable[[str], None] | None = None,  # Called with status/log messages
        on_progress: Callable[[int, int], None] | None = None,  # Called with (current_bytes, total_bytes)
        on_finished: Callable[[], None] | None = None,  # Called when transfer completes successfully
        on_error: Callable[[str], None] | None = None,  # Called when transfer fails
        on_file_received: Callable[[Path], None] | None = None,  # Called when a file is saved (receive only)
    ) -> None:
        self.on_log = on_log  # Store log callback
        self.on_progress = on_progress  # Store progress callback
        self.on_finished = on_finished  # Store finished callback
        self.on_error = on_error  # Store error callback
        self.on_file_received = on_file_received  # Store file-received callback

    def _log(self, message: str) -> None:  # Internal helper to emit log messages if callback is set
        if self.on_log:  # Only call if a log handler was provided
            self.on_log(message)  # Forward the message to the callback (e.g. UI signal)

    def _fail(self, message: str) -> None:  # Internal helper to log and report an error
        self._log(message)  # Log the error message
        if self.on_error:  # Only call if an error handler was provided
            self.on_error(message)  # Forward the error to the callback (e.g. UI signal)

    def connect_to_peer(  # Outbound TCP connection used by the sending peer
        self,
        peer_ip: str,  # IP address of the remote peer to connect to
        port: int = DEFAULT_PORT,  # TCP port to connect on (default 5050)
        timeout: float = 30,  # Maximum seconds to keep retrying the connection
    ) -> socket.socket:
        """Outbound connection — used by the sending peer."""  # Docstring
        self._log(f"Connecting to peer {peer_ip}…")  # Log that we are attempting to connect
        deadline = time.time() + timeout  # Calculate absolute time when we should stop retrying
        last_error: OSError | None = None  # Store the most recent connection error for reporting

        while time.time() < deadline:  # Retry connecting until timeout expires
            try:  # Attempt a single TCP connection
                conn = socket.create_connection((peer_ip, port), timeout=2)  # Connect with 2-second socket timeout
                self._log(f"Connected to peer {peer_ip}")  # Log successful connection
                return conn  # Return the connected socket to the caller
            except OSError as exc:  # Connection refused, host unreachable, etc.
                last_error = exc  # Remember this error in case all retries fail
                time.sleep(0.5)  # Wait briefly before trying again

        message = f"Could not reach peer at {peer_ip}"  # Build user-friendly error message
        if last_error:  # Include underlying OS error if we have one
            message = f"{message}: {last_error}"  # Append details (e.g. "Connection refused")
        raise ConnectionError(message)  # Raise so caller/UI can show the failure

    def accept_from_peer(  # Temporary inbound listener used by the receiving peer
        self,
        peer_ip: str,  # IP address we expect the connection to come from
        port: int = DEFAULT_PORT,  # TCP port to listen on (default 5050)
        timeout: float = 30,  # Maximum seconds to wait for the peer to connect
    ) -> socket.socket:
        """Temporary inbound accept — used by the receiving peer, closes after transfer."""  # Docstring
        self._log(f"Waiting for peer {peer_ip}…")  # Log that we are waiting for incoming connection

        listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create TCP listening socket
        listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow port reuse after quick restart

        try:  # Try to bind to the port
            listen_sock.bind(("0.0.0.0", port))  # Listen on all network interfaces on the given port
        except OSError as exc:  # Port may already be in use by another app instance
            if exc.errno == 98:  # Linux errno 98 = Address already in use
                raise ConnectionError(  # Raise clear error for the user
                    f"Port {port} is already in use. "
                    "Close any other transfer windows on this computer and try again."
                ) from exc  # Chain original exception for debugging
            raise ConnectionError(f"Could not wait for peer: {exc}") from exc  # Other bind errors

        try:  # Main accept loop
            listen_sock.listen(1)  # Start listening; backlog of 1 pending connection
            listen_sock.settimeout(1.0)  # Set 1-second timeout so we can check overall deadline

            deadline = time.time() + timeout  # Calculate when to stop waiting
            while time.time() < deadline:  # Keep accepting until timeout
                try:  # Try to accept one incoming connection
                    conn, addr = listen_sock.accept()  # Block up to 1 second for a connection
                except TimeoutError:  # No connection within 1 second — check deadline and retry
                    continue  # Go back to while loop and try again
                except OSError as exc:  # Unexpected socket error during accept
                    raise ConnectionError(f"Could not accept peer connection: {exc}") from exc

                if addr[0] != peer_ip:  # Reject connections from unexpected IP addresses
                    self._log(f"Ignored connection from {addr[0]}")  # Log ignored connection
                    conn.close()  # Close unwanted connection
                    continue  # Wait for connection from the expected peer

                self._log(f"Peer connected from {addr[0]}")  # Log successful peer connection
                return conn  # Return connected socket to caller
        finally:  # Always run cleanup even if an error occurs
            listen_sock.close()  # Close listening socket (no longer needed after accept)

        raise ConnectionError(f"Peer {peer_ip} did not connect within {int(timeout)}s")  # Timed out waiting

    def establish_connection(  # Route to correct connection method based on send/receive role
        self,
        peer_ip: str,  # IP of the other peer
        role: Role,  # "send" = connect outbound, "receive" = wait for inbound
        port: int = DEFAULT_PORT,  # TCP port to use
        timeout: float = 30,  # Connection timeout in seconds
    ) -> socket.socket:
        if role == "send":  # Sender initiates outbound connection
            return self.connect_to_peer(peer_ip, port, timeout)  # Connect to peer and return socket
        return self.accept_from_peer(peer_ip, port, timeout)  # Receiver waits for peer and returns socket

    def send_files(self, peer_ip: str, file_paths: list[Path], port: int = DEFAULT_PORT) -> None:  # Send files to peer
        if not file_paths:  # Guard against empty file list
            self._fail("No files selected")  # Report error and return
            return  # Stop execution

        try:  # Wrap entire send operation in try/except
            conn = self.establish_connection(peer_ip, role="send", port=port)  # Connect to receiving peer
            with conn:  # Context manager ensures socket is closed when done
                for file_path in file_paths:  # Send each selected file one after another
                    path = Path(file_path)  # Ensure Path object
                    if not path.is_file():  # Skip directories or missing paths
                        self._log(f"Skipped (not a file): {path}")  # Log skipped item
                        continue  # Move to next file
                    self._log(f"Sending: {path.name}")  # Log current file being sent
                    send_file(conn, path, on_progress=self.on_progress)  # Send file using protocol helper
                    self._log(f"Sent: {path.name}")  # Log completion of this file

                send_done(conn)  # Send "done" message so receiver knows transfer is complete
                self._log("Transfer complete")  # Log overall success
                if self.on_finished:  # Notify UI/caller of success
                    self.on_finished()  # Call finished callback
        except (ConnectionError, OSError, TimeoutError) as exc:  # Catch network-related failures
            self._fail(f"Send failed: {exc}")  # Log and report error to UI

    def receive_files(  # Receive files from peer and save to disk
        self,
        peer_ip: str,  # IP address we expect the sender to connect from
        save_dir: Path,  # Directory where received files will be saved
        port: int = DEFAULT_PORT,  # TCP port to listen on
    ) -> None:
        save_dir = Path(save_dir)  # Ensure save_dir is a Path object
        save_dir.mkdir(parents=True, exist_ok=True)  # Create save directory if it doesn't exist

        try:  # Wrap entire receive operation in try/except
            conn = self.establish_connection(peer_ip, role="receive", port=port)  # Wait for sender to connect
            with conn:  # Context manager ensures socket is closed when done
                self._log("Receiving files…")  # Log that we are ready to receive
                while True:  # Keep reading messages until "done" is received
                    header = recv_header(conn)  # Read next message header from socket
                    if header.get("type") == "done":  # Sender signaled end of transfer
                        self._log("Transfer complete")  # Log completion
                        break  # Exit receive loop
                    if header.get("type") != "file":  # Unknown message type
                        self._log(f"Unknown message: {header.get('type')}")  # Log unexpected message
                        break  # Stop receiving on unknown message

                    saved = recv_file(  # Receive and save the file described by header
                        conn,  # Active TCP connection
                        save_dir,  # Where to save the file
                        header=header,  # Pass already-read header to avoid reading twice
                        on_progress=self.on_progress,  # Forward progress to UI
                    )
                    self._log(f"Received: {saved.name}")  # Log saved filename
                    if self.on_file_received:  # Notify UI that a file was saved
                        self.on_file_received(saved)  # Call callback with saved file path

                if self.on_finished:  # Notify UI/caller that all files were received
                    self.on_finished()  # Call finished callback
        except (ConnectionError, OSError, TimeoutError, ValueError) as exc:  # Catch network and protocol errors
            self._fail(f"Receive failed: {exc}")  # Log and report error to UI
