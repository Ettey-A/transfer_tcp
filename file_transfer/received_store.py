"""Store and query history of received files."""  # Module docstring: this file manages received-file history

import json  # Import JSON module to read/write the history file as JSON text
from dataclasses import asdict, dataclass  # asdict converts a dataclass to a dict; dataclass builds simple data classes
from datetime import datetime, timezone  # datetime for timestamps; timezone for UTC time
from pathlib import Path  # Path for filesystem path handling


@dataclass  # Decorator: auto-creates __init__, __repr__, etc. for this data class
class ReceivedFile:  # Class that represents one received file in the history
    """One received file entry."""  # Class docstring

    path: str  # Full absolute path to the received file on disk
    name: str  # File name only (e.g. "report.pdf")
    size: int  # File size in bytes
    received_at: str  # When it was received, stored as an ISO-8601 timestamp string

    @classmethod  # Marks from_path as a class method (called on the class, not an instance)
    def from_path(cls, file_path: Path) -> "ReceivedFile":  # Build a ReceivedFile from a disk path
        path = Path(file_path)  # Ensure file_path is a Path object
        size = path.stat().st_size if path.exists() else 0  # Read size if file exists; otherwise use 0
        return cls(  # Create and return a ReceivedFile instance
            path=str(path.resolve()),  # Store absolute resolved path as a string
            name=path.name,  # Store just the filename
            size=size,  # Store the byte size
            received_at=datetime.now(timezone.utc).isoformat(),  # Store current UTC time in ISO format
        )


class ReceivedStore:  # Class that saves and loads received-file history from JSON
    """Persists received-file history to a JSON file."""  # Class docstring

    def __init__(self, history_path: Path | None = None) -> None:  # Create store; optional custom history file path
        self.history_path = Path(  # Set where the JSON history file lives
            history_path  # Use caller-provided path if given
            or (Path.home() / ".file_transfer" / "received.json")  # Otherwise default to ~/.file_transfer/received.json
        )
        self.history_path.parent.mkdir(parents=True, exist_ok=True)  # Create .file_transfer folder if it does not exist
        if not self.history_path.exists():  # If history file has never been created
            self._write([])  # Create it as an empty JSON list

    def _read(self) -> list[dict]:  # Load history entries from disk as a list of dictionaries
        try:  # Protect against missing/corrupt files
            data = json.loads(self.history_path.read_text(encoding="utf-8"))  # Read file text and parse JSON
            return data if isinstance(data, list) else []  # Return list if valid; otherwise return empty list
        except (OSError, json.JSONDecodeError):  # File missing/unreadable or JSON invalid
            return []  # Fail safely with an empty history

    def _write(self, items: list[dict]) -> None:  # Save history entries to the JSON file
        self.history_path.write_text(  # Overwrite the history file with new contents
            json.dumps(items, indent=2),  # Convert list of dicts to pretty-printed JSON text
            encoding="utf-8",  # Write using UTF-8 encoding
        )

    def add(self, file_path: Path) -> ReceivedFile:  # Add a newly received file to the history
        entry = ReceivedFile.from_path(file_path)  # Build a ReceivedFile record from the saved path
        items = self._read()  # Load current history from disk
        items.insert(0, asdict(entry))  # Insert new entry at the front (newest first) as a dict
        self._write(items)  # Save updated history back to disk
        return entry  # Return the created entry to the caller/UI

    def list_files(self) -> list[ReceivedFile]:  # Return all history entries as ReceivedFile objects
        files: list[ReceivedFile] = []  # Start with an empty result list
        for item in self._read():  # Loop through each dict loaded from JSON
            try:  # Skip bad/incomplete entries instead of crashing
                files.append(  # Add a rebuilt ReceivedFile to the result list
                    ReceivedFile(  # Construct ReceivedFile from dictionary fields
                        path=str(item["path"]),  # Required: full file path
                        name=str(item["name"]),  # Required: file name
                        size=int(item.get("size", 0)),  # Optional size; default 0 if missing
                        received_at=str(item.get("received_at", "")),  # Optional timestamp; default empty
                    )
                )
            except (KeyError, TypeError, ValueError):  # Missing keys or wrong types
                continue  # Skip this bad entry and keep going
        return files  # Return the full list of valid received files

    def clear(self) -> None:  # Remove all entries from history (does not delete files on disk)
        self._write([])  # Write an empty list to the JSON history file

    def remove(self, path: str) -> None:  # Remove one history entry by its file path
        items = [item for item in self._read() if item.get("path") != path]  # Keep every entry except the matching path
        self._write(items)  # Save the filtered list back to disk
