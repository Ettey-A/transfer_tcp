"""Main application window."""

import socket
from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from file_transfer.network import get_local_ip
from file_transfer.received_store import ReceivedStore
from file_transfer.ui.received_panel import ReceivedFilesPanel
from file_transfer.ui.styles import APP_STYLESHEET
from file_transfer.ui.workers import ListenerWorker, SendWorker

SAVE_DIR = Path.home() / "Downloads"


class DropZone(QFrame):
    """Click or drop files here."""

    def __init__(self, on_files_selected: Callable[[list[Path]], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setProperty("active", False)
        self._on_files_selected = on_files_selected
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)

        self.title_label = QLabel("Drop files here or click to browse")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #374151; border: none;")

        self.hint_label = QLabel("No files selected")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("font-size: 12px; color: #9ca3af; border: none;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.hint_label)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            paths, _ = QFileDialog.getOpenFileNames(self.window(), "Select Files")
            if paths:
                self._on_files_selected([Path(p) for p in paths])
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("active", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self.setProperty("active", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        paths = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                paths.append(path)
        if paths:
            self._on_files_selected(paths)
        self.setProperty("active", False)
        self.style().unpolish(self)
        self.style().polish(self)
        event.acceptProposedAction()

    def set_file_summary(self, count: int, preview: str) -> None:
        if count == 0:
            self.title_label.setText("Drop files here or click to browse")
            self.hint_label.setText("No files selected")
            return
        self.title_label.setText(f"{count} file{'s' if count != 1 else ''} ready")
        self.hint_label.setText(preview)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("File Transfer")
        # Native window frame (minimize / maximize / close from Windows)
        self.setMinimumSize(500, 680)
        self.resize(540, 740)

        self._send_thread: QThread | None = None
        self._send_worker: SendWorker | None = None
        self._listener_thread: QThread | None = None
        self._listener_worker: ListenerWorker | None = None
        self._selected_files: list[Path] = []
        self._received_store = ReceivedStore()

        self._build_ui()
        self._start_listener()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("File Transfer")
        title.setObjectName("appTitle")
        subtitle = QLabel("Enter the recipient's IP, choose files, and send.")
        subtitle.setObjectName("appSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        root.addWidget(self._build_connection_card())
        root.addWidget(self._build_files_card())
        root.addWidget(self._build_send_card())
        self.received_panel = ReceivedFilesPanel(self._received_store)
        root.addWidget(self.received_panel)
        root.addStretch()

    def _card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        return card

    def _build_connection_card(self) -> QFrame:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        section = QLabel("RECIPIENT")
        section.setObjectName("sectionTitle")

        local_row = QHBoxLayout()
        local_label = QLabel("Your IP (share this)")
        local_label.setObjectName("fieldLabel")
        self.local_ip_label = QLabel(get_local_ip())
        self.local_ip_label.setObjectName("localIpValue")
        local_row.addWidget(local_label)
        local_row.addStretch()
        local_row.addWidget(self.local_ip_label)

        self.ready_label = QLabel("Ready to receive files automatically")
        self.ready_label.setObjectName("readyLabel")

        recipient_label = QLabel("Recipient IP")
        recipient_label.setObjectName("fieldLabel")
        self.recipient_ip_edit = QLineEdit()
        self.recipient_ip_edit.setPlaceholderText("e.g. 192.168.1.42")

        layout.addWidget(section)
        layout.addLayout(local_row)
        layout.addWidget(self.ready_label)
        layout.addWidget(recipient_label)
        layout.addWidget(self.recipient_ip_edit)
        return card

    def _build_files_card(self) -> QFrame:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        section = QLabel("FILES")
        section.setObjectName("sectionTitle")

        self.drop_zone = DropZone(self._set_selected_files)
        self.choose_btn = QPushButton("Browse Files")
        self.choose_btn.setObjectName("chooseBtn")
        self.choose_btn.clicked.connect(self._pick_files)

        layout.addWidget(section)
        layout.addWidget(self.drop_zone)
        layout.addWidget(self.choose_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        return card

    def _build_send_card(self) -> QFrame:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        self.send_btn = QPushButton("Send to Recipient")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.clicked.connect(self._send_files)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        self.status_label = QLabel("Waiting for transfers")
        self.status_label.setObjectName("statusLabel")

        layout.addWidget(self.send_btn)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        return card

    def _start_listener(self) -> None:
        self._listener_thread = QThread()
        self._listener_worker = ListenerWorker(SAVE_DIR)
        self._listener_worker.moveToThread(self._listener_thread)
        self._listener_thread.started.connect(self._listener_worker.start)
        self._listener_worker.started.connect(self._on_listener_started)
        self._listener_worker.file_received.connect(self._on_file_received)
        self._listener_worker.progress.connect(self._update_progress)
        self._listener_worker.error.connect(self._on_listener_error)
        self._listener_thread.start()

    def _on_listener_started(self) -> None:
        self.ready_label.setText("Ready to receive files automatically")
        self._set_status("Waiting for transfers")

    def _on_listener_error(self, message: str) -> None:
        self.ready_label.setText("Receiver not available")
        self.ready_label.setStyleSheet("color: #dc2626; font-size: 12px;")
        self._set_status(message)

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _set_selected_files(self, paths: list[Path]) -> None:
        self._selected_files = paths
        if not paths:
            self.drop_zone.set_file_summary(0, "")
            return
        preview = ", ".join(p.name for p in paths[:2])
        if len(paths) > 2:
            preview += f" +{len(paths) - 2} more"
        self.drop_zone.set_file_summary(len(paths), preview)

    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        self._set_selected_files([Path(p) for p in paths])

    def _update_progress(self, current: int, total: int) -> None:
        if total <= 0:
            self.progress_bar.setValue(0)
            return
        percent = int((current / total) * 100)
        self.progress_bar.setValue(percent)
        self._set_status(f"Transferring… {percent}%")

    def _validate_recipient_ip(self) -> str | None:
        if self._send_thread is not None and self._send_thread.isRunning():
            QMessageBox.warning(self, "Busy", "A send is already in progress.")
            return None

        recipient_ip = self.recipient_ip_edit.text().strip()
        if not recipient_ip:
            QMessageBox.warning(self, "Missing IP", "Enter the recipient's IP address.")
            return None
        try:
            socket.inet_aton(recipient_ip)
        except OSError:
            QMessageBox.warning(self, "Invalid IP", "Enter a valid IP address.")
            return None
        return recipient_ip

    def _set_busy(self, busy: bool) -> None:
        self.choose_btn.setEnabled(not busy)
        self.send_btn.setEnabled(not busy)
        self.recipient_ip_edit.setEnabled(not busy)
        self.drop_zone.setEnabled(not busy)

    def _send_files(self) -> None:
        recipient_ip = self._validate_recipient_ip()
        if not recipient_ip:
            return
        if not self._selected_files:
            QMessageBox.warning(self, "No Files", "Choose files to send first.")
            return

        # Free the port while we send from this machine
        if self._listener_worker:
            self._listener_worker.pause()

        self._send_thread = QThread()
        self._send_worker = SendWorker(recipient_ip, list(self._selected_files))
        self._send_worker.moveToThread(self._send_thread)
        self._send_thread.started.connect(self._send_worker.run)
        self._send_worker.progress.connect(self._update_progress)
        self._send_worker.finished.connect(self._on_send_finished)
        self._send_worker.error.connect(self._on_send_error)
        self._send_worker.finished.connect(self._send_thread.quit)
        self._send_worker.error.connect(self._send_thread.quit)
        self._send_worker.finished.connect(self._send_worker.deleteLater)
        self._send_worker.error.connect(self._send_worker.deleteLater)
        self._send_thread.finished.connect(self._send_thread.deleteLater)

        self._set_busy(True)
        self.progress_bar.setValue(0)
        self._set_status(f"Sending to {recipient_ip}…")
        self._send_thread.start()

    def _on_send_finished(self) -> None:
        self._set_busy(False)
        self.progress_bar.setValue(100)
        self._set_status("Files sent")
        if self._listener_worker:
            self._listener_worker.resume()
        QMessageBox.information(self, "Done", "Files sent successfully.")

    def _on_send_error(self, message: str) -> None:
        self._set_busy(False)
        self._set_status("Send failed")
        if self._listener_worker:
            self._listener_worker.resume()
        QMessageBox.critical(self, "Failed", message)

    def _on_file_received(self, path: str) -> None:
        file_path = Path(path)
        self.received_panel.add_received(file_path)
        self.progress_bar.setValue(100)
        self._set_status(f"Received: {file_path.name}")
        QMessageBox.information(self, "File Received", f"Saved to Downloads:\n{file_path.name}")

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._listener_worker:
            self._listener_worker.stop()
        if self._listener_thread:
            self._listener_thread.quit()
            self._listener_thread.wait(2000)
        if self._send_thread and self._send_thread.isRunning():
            self._send_thread.quit()
            self._send_thread.wait(2000)
        super().closeEvent(event)


def run_app() -> None:
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)

    font = QFont()
    font.setFamilies(["Segoe UI", "Arial", "sans-serif"])
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
