"""Background workers for transfers."""

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from file_transfer.listener import IncomingListener
from file_transfer.peer import Peer


class SendWorker(QObject):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, peer_ip: str, file_paths: list[Path]) -> None:
        super().__init__()
        self._peer_ip = peer_ip
        self._file_paths = file_paths
        self._peer = Peer(
            on_progress=self.progress.emit,
            on_finished=self.finished.emit,
            on_error=self.error.emit,
        )

    def run(self) -> None:
        self._peer.send_files(self._peer_ip, self._file_paths)


class ListenerWorker(QObject):
    started = pyqtSignal()
    progress = pyqtSignal(int, int)
    file_received = pyqtSignal(str)
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, save_dir: Path) -> None:
        super().__init__()
        self._listener = IncomingListener(
            save_dir=save_dir,
            on_log=self.log.emit,
            on_progress=self.progress.emit,
            on_file_received=lambda path: self.file_received.emit(str(path)),
            on_started=self.started.emit,
            on_error=self.error.emit,
        )

    def start(self) -> None:
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()

    def pause(self) -> None:
        self._listener.pause()

    def resume(self) -> None:
        self._listener.resume()
