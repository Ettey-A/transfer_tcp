"""Network helper utilities."""  # Module docstring for network-related helper functions

import socket  # Standard library for network operations and IP detection


def get_local_ip() -> str:  # Function that returns this computer's local network IP address
    """Return the machine's local network IP address."""  # Docstring explaining the function
    try:  # Try the primary method for detecting the local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:  # Create a UDP socket (no real connection needed)
            sock.connect(("8.8.8.8", 80))  # Fake outbound connect so OS picks the correct local interface
            return sock.getsockname()[0]  # Return the local IP address bound to that interface
    except OSError:  # If network detection fails (offline, no route, etc.)
        return "127.0.0.1"  # Fall back to localhost so the app still shows something usable
