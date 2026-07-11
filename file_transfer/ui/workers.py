"""Background workers for peer-to-peer transfers."""  # Module docstring for Qt background thread workers

from pathlib import Path  # Used for file path type hints

from PyQt6.QtCore import QObject, pyqtSignal  # Qt base class and signal system for thread-safe UI updates

from file_transfer.peer import Peer  # Core P2P transfer logic used by both workers


class SendWorker(QObject):  # Qt worker object that sends files on a background thread
    log = pyqtSignal(str)  # Signal emitted with log messages (not currently wired in simplified UI)
    progress = pyqtSignal(int, int)  # Signal emitted with (bytes_done, total_bytes) during transfer
    finished = pyqtSignal()  # Signal emitted when sending completes successfully
    error = pyqtSignal(str)  # Signal emitted when sending fails with an error message

    def __init__(self, peer_ip: str, file_paths: list[Path]) -> None:  # Initialize send worker with target and files
        super().__init__()  # Call QObject constructor
        self._peer_ip = peer_ip  # Store the remote peer's IP address
        self._file_paths = file_paths  # Store list of local file paths to send
        self._peer = Peer(  # Create Peer instance and wire its callbacks to Qt signals
            on_log=self.log.emit,  # Forward log messages to UI thread via signal
            on_progress=self.progress.emit,  # Forward progress updates to UI thread
            on_finished=self.finished.emit,  # Forward success notification to UI thread
            on_error=self.error.emit,  # Forward error messages to UI thread
        )

    def run(self) -> None:  # Entry point called when the background thread starts
        self._peer.send_files(self._peer_ip, self._file_paths)  # Connect to peer and send all selected files


class ReceiveWorker(QObject):  # Qt worker object that receives files on a background thread
    log = pyqtSignal(str)  # Signal emitted with log messages (not currently wired in simplified UI)
    progress = pyqtSignal(int, int)  # Signal emitted with (bytes_done, total_bytes) during transfer
    finished = pyqtSignal()  # Signal emitted when receiving completes successfully
    error = pyqtSignal(str)  # Signal emitted when receiving fails with an error message
    file_received = pyqtSignal(str)  # Signal emitted with path string when each file is saved

    def __init__(self, peer_ip: str, save_dir: Path) -> None:  # Initialize receive worker with peer IP and save folder
        super().__init__()  # Call QObject constructor
        self._peer_ip = peer_ip  # Store the remote peer's IP address we expect to connect from
        self._save_dir = save_dir  # Store directory where received files will be saved (Downloads)
        self._peer = Peer(  # Create Peer instance and wire its callbacks to Qt signals
            on_log=self.log.emit,  # Forward log messages to UI thread via signal
            on_progress=self.progress.emit,  # Forward progress updates to UI thread
            on_finished=self.finished.emit,  # Forward success notification to UI thread
            on_error=self.error.emit,  # Forward error messages to UI thread
            on_file_received=lambda path: self.file_received.emit(str(path)),  # Emit file path when each file arrives
        )

    def run(self) -> None:  # Entry point called when the background thread starts
        self._peer.receive_files(self._peer_ip, self._save_dir)  # Wait for peer and receive all incoming files
