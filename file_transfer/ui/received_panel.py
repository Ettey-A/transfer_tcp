"""UI panel for viewing received files."""

import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from file_transfer.received_store import ReceivedFile, ReceivedStore


def format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{num_bytes} B"


def format_time(iso_text: str) -> str:
    if not iso_text:
        return ""
    try:
        return iso_text.replace("T", " ").split("+")[0].split(".")[0]
    except ValueError:
        return iso_text


def open_path(path: Path) -> None:
    """Open a file or folder with the OS default app."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found:\n{path}")

    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


class ReceivedFilesPanel(QFrame):
    """Lists received files with open / folder / clear actions."""

    file_opened = pyqtSignal(str)

    def __init__(self, store: ReceivedStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._store = store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(8)
        section = QLabel("RECEIVED FILES")
        section.setObjectName("sectionTitle")
        header.addWidget(section)
        header.addStretch()

        self.count_label = QLabel("0 files")
        self.count_label.setObjectName("fieldLabel")
        header.addWidget(self.count_label)
        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("receivedList")
        self.list_widget.setMinimumHeight(100)
        self.list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemDoubleClicked.connect(self._open_selected)
        layout.addWidget(self.list_widget, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 4, 0, 0)

        self.open_btn = QPushButton("Open")
        self.open_btn.setObjectName("chooseBtn")
        self.open_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.open_btn.clicked.connect(self._open_selected)

        self.folder_btn = QPushButton("Show Folder")
        self.folder_btn.setObjectName("chooseBtn")
        self.folder_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.folder_btn.clicked.connect(self._show_folder)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("chooseBtn")
        self.refresh_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.refresh_btn.clicked.connect(self.refresh)

        self.clear_btn = QPushButton("Clear List")
        self.clear_btn.setObjectName("chooseBtn")
        self.clear_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.clear_btn.clicked.connect(self._clear_list)

        btn_row.addWidget(self.open_btn)
        btn_row.addWidget(self.folder_btn)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addWidget(self.clear_btn)
        layout.addLayout(btn_row)

        self.refresh()

    def add_received(self, path: Path) -> ReceivedFile:
        entry = self._store.add(path)
        self.refresh()
        return entry

    def refresh(self) -> None:
        self.list_widget.clear()
        files = self._store.list_files()
        self.count_label.setText(f"{len(files)} file{'s' if len(files) != 1 else ''}")

        for entry in files:
            exists = Path(entry.path).exists()
            status = "" if exists else " (missing)"
            text = f"{entry.name}  •  {format_size(entry.size)}  •  {format_time(entry.received_at)}{status}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, entry.path)
            if not exists:
                item.setForeground(Qt.GlobalColor.gray)
            self.list_widget.addItem(item)

        if not files:
            empty = QListWidgetItem("No files received yet")
            empty.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_widget.addItem(empty)

    def _selected_path(self) -> Path | None:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path:
            return None
        return Path(path)

    def _open_selected(self) -> None:
        path = self._selected_path()
        if path is None:
            QMessageBox.information(self, "Received Files", "Select a file first.")
            return
        try:
            open_path(path)
            self.file_opened.emit(str(path))
        except OSError as exc:
            QMessageBox.warning(self, "Open Failed", str(exc))
            self.refresh()

    def _show_folder(self) -> None:
        path = self._selected_path()
        if path is None:
            folder = Path.home() / "Downloads"
        else:
            folder = path.parent if path.exists() else Path.home() / "Downloads"
        try:
            open_path(folder)
        except OSError as exc:
            QMessageBox.warning(self, "Open Failed", str(exc))

    def _clear_list(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear List",
            "Clear the received files list?\n(This does not delete the files on disk.)",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._store.clear()
            self.refresh()
