"""Application stylesheet — Windows-friendly native window look."""

APP_STYLESHEET = """
QMainWindow {
    background-color: #f3f4f6;
}

QWidget#centralWidget {
    background-color: #f3f4f6;
}

QLabel#appTitle {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
}

QLabel#appSubtitle {
    font-size: 13px;
    color: #6b7280;
}

QFrame#card {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}

QLabel#sectionTitle {
    font-size: 11px;
    font-weight: 700;
    color: #6b7280;
}

QLabel#fieldLabel {
    font-size: 13px;
    color: #4b5563;
}

QLabel#localIpValue {
    font-size: 16px;
    font-weight: 700;
    color: #2563eb;
    font-family: Consolas, "Courier New", monospace;
}

QLabel#statusLabel {
    font-size: 13px;
    color: #6b7280;
}

QLabel#readyLabel {
    font-size: 12px;
    color: #059669;
}

QFrame#dropZone {
    background-color: #f9fafb;
    border: 2px dashed #d1d5db;
    border-radius: 8px;
    min-height: 100px;
}

QFrame#dropZone[active="true"] {
    border-color: #60a5fa;
    background-color: #eff6ff;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    color: #111827;
    min-height: 20px;
}

QLineEdit:focus {
    border: 1px solid #2563eb;
}

QPushButton {
    border-radius: 6px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
    min-height: 20px;
}

QPushButton#chooseBtn {
    background-color: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
}

QPushButton#chooseBtn:hover {
    background-color: #e5e7eb;
}

QPushButton#sendBtn {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    min-height: 36px;
    font-size: 14px;
}

QPushButton#sendBtn:hover {
    background-color: #1d4ed8;
}

QPushButton#sendBtn:pressed {
    background-color: #1e40af;
}

QPushButton:disabled {
    background-color: #e5e7eb;
    color: #9ca3af;
    border: 1px solid #e5e7eb;
}

QProgressBar {
    background-color: #e5e7eb;
    border: none;
    border-radius: 4px;
    min-height: 8px;
    max-height: 8px;
}

QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 4px;
}

QListWidget#receivedList {
    background-color: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 4px;
    font-size: 12px;
    color: #111827;
    outline: none;
}

QListWidget#receivedList::item {
    padding: 8px 6px;
    border-radius: 4px;
}

QListWidget#receivedList::item:selected {
    background-color: #dbeafe;
    color: #1e3a8a;
}

QListWidget#receivedList::item:hover {
    background-color: #eff6ff;
}
"""
