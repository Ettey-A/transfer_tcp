"""TCP file transfer protocol helpers."""  # Module docstring for low-level send/receive protocol code

import json  # Used to encode/decode JSON message headers
import socket  # Used for socket type hints and network I/O
import struct  # Used to pack/unpack binary header length (4-byte integer)
from pathlib import Path  # Used for file path handling
from typing import Any, Callable  # Type hints for dictionaries and callback functions

HEADER_SIZE_FMT = "!I"  # Format string: big-endian unsigned 32-bit integer for header byte length
CHUNK_SIZE = 64 * 1024  # Read/write files in 64 KB chunks for efficient transfer


def recv_exact(sock: socket.socket, size: int) -> bytes:  # Receive exactly `size` bytes from a TCP socket
    """Receive exactly `size` bytes from the socket."""  # Docstring for recv_exact
    data = bytearray()  # Mutable buffer to accumulate received bytes
    while len(data) < size:  # Keep reading until we have the full amount requested
        chunk = sock.recv(size - len(data))  # Read up to the remaining number of bytes needed
        if not chunk:  # Empty chunk means the connection was closed early
            raise ConnectionError("Connection closed unexpectedly")  # Raise error for incomplete read
        data.extend(chunk)  # Append newly received bytes to our buffer
    return bytes(data)  # Return immutable bytes object with the full data


def send_header(sock: socket.socket, payload: dict[str, Any]) -> None:  # Send a JSON header over the socket
    """Send a length-prefixed JSON header."""  # Docstring for send_header
    encoded = json.dumps(payload).encode("utf-8")  # Convert dict to JSON string, then to UTF-8 bytes
    sock.sendall(struct.pack(HEADER_SIZE_FMT, len(encoded)) + encoded)  # Send 4-byte length + JSON body


def recv_header(sock: socket.socket) -> dict[str, Any]:  # Receive and parse a length-prefixed JSON header
    """Receive a length-prefixed JSON header."""  # Docstring for recv_header
    header_size = struct.pack(HEADER_SIZE_FMT, 0).__len__()  # Header length field is always 4 bytes
    (length,) = struct.unpack(HEADER_SIZE_FMT, recv_exact(sock, header_size))  # Read and unpack header size
    return json.loads(recv_exact(sock, length).decode("utf-8"))  # Read JSON body and parse into a dict


def send_file(  # Send one file over an already-connected TCP socket
    sock: socket.socket,  # Active TCP connection to the peer
    file_path: Path,  # Path to the file on disk to send
    on_progress: Callable[[int, int], None] | None = None,  # Optional callback(sent_bytes, total_bytes)
) -> None:
    """Send a single file over the socket."""  # Docstring for send_file
    file_path = Path(file_path)  # Ensure we have a Path object
    size = file_path.stat().st_size  # Get file size in bytes from the filesystem
    send_header(sock, {"type": "file", "filename": file_path.name, "size": size})  # Tell peer what file is coming

    sent = 0  # Counter for how many bytes have been sent so far
    with file_path.open("rb") as handle:  # Open file in binary read mode
        while sent < size:  # Loop until entire file is sent
            chunk = handle.read(min(CHUNK_SIZE, size - sent))  # Read next chunk (up to CHUNK_SIZE bytes)
            if not chunk:  # No more data to read (unexpected early EOF)
                break  # Stop sending if file ended before expected size
            sock.sendall(chunk)  # Send chunk over TCP (blocks until all bytes are sent)
            sent += len(chunk)  # Update sent byte counter
            if on_progress:  # If UI or caller wants progress updates
                on_progress(sent, size)  # Report current progress (sent, total)


def recv_file(  # Receive one file from socket and save it to disk
    sock: socket.socket,  # Active TCP connection to the peer
    save_dir: Path,  # Directory where the received file should be saved
    header: dict[str, Any] | None = None,  # Optional pre-read header (avoids reading twice)
    on_progress: Callable[[int, int], None] | None = None,  # Optional progress callback
) -> Path:
    """Receive a single file and save it to `save_dir`."""  # Docstring for recv_file
    if header is None:  # If caller did not already read the file header
        header = recv_header(sock)  # Read the next message header from the socket

    if header.get("type") != "file":  # Verify this message is a file transfer message
        raise ValueError(f"Expected file header, got: {header}")  # Reject unknown message types

    filename = Path(header["filename"]).name  # Extract filename only (strip any path components)
    size = int(header["size"])  # Get expected file size in bytes from header
    destination = save_dir / filename  # Build full save path inside the target directory

    if destination.exists():  # If a file with the same name already exists
        stem = destination.stem  # Base name without extension (e.g. "report" from "report.pdf")
        suffix = destination.suffix  # File extension including dot (e.g. ".pdf")
        counter = 1  # Start numbering duplicates at 1
        while destination.exists():  # Keep trying new names until we find one that doesn't exist
            destination = save_dir / f"{stem}_{counter}{suffix}"  # e.g. report_1.pdf, report_2.pdf
            counter += 1  # Increment counter for next attempt if still taken

    received = 0  # Counter for how many bytes have been received so far
    with destination.open("wb") as handle:  # Open destination file in binary write mode
        while received < size:  # Loop until we have received the full file
            chunk = sock.recv(min(CHUNK_SIZE, size - received))  # Read next chunk from socket
            if not chunk:  # Connection closed before full file arrived
                raise ConnectionError("Connection closed before file transfer completed")  # Fail the transfer
            handle.write(chunk)  # Write received bytes to disk
            received += len(chunk)  # Update received byte counter
            if on_progress:  # If UI or caller wants progress updates
                on_progress(received, size)  # Report current progress (received, total)

    return destination  # Return path to the saved file on disk


def send_done(sock: socket.socket) -> None:  # Signal that no more files will be sent on this connection
    """Signal that no more files will be sent on this connection."""  # Docstring for send_done
    send_header(sock, {"type": "done"})  # Send a "done" header so receiver knows transfer is complete
