"""Application stylesheet."""  # Module docstring: Qt Style Sheet (QSS) definitions for the UI look

# Global stylesheet applied to the entire application via app.setStyleSheet()
APP_STYLESHEET = """
/* Main window: light gray background with rounded border */
QMainWindow {
    background-color: #eef2f7;  /* Soft blue-gray window background */
    border: 1px solid #cbd5e1;  /* Subtle outer border */
    border-radius: 12px;  /* Rounded window corners */
}

/* Custom title bar at top of frameless window */
QWidget#titleBar {
    background-color: #ffffff;  /* White title bar background */
    border-bottom: 1px solid #e2e8f0;  /* Separator line below title bar */
    border-top-left-radius: 12px;  /* Round top-left corner */
    border-top-right-radius: 12px;  /* Round top-right corner */
}

/* Title text in the custom title bar */
QLabel#titleBarLabel {
    font-size: 13px;  /* Medium-small font */
    font-weight: 600;  /* Semi-bold */
    color: #334155;  /* Dark slate text color */
}

/* Shared sizing for minimize, maximize, and close buttons */
QPushButton#titleBtnMin,
QPushButton#titleBtnMax,
QPushButton#titleBtnClose {
    min-width: 36px;  /* Fixed button width */
    max-width: 36px;
    min-height: 28px;  /* Fixed button height */
    max-height: 28px;
    padding: 0;  /* No inner padding */
    border-radius: 6px;  /* Slightly rounded button corners */
    font-size: 16px;  /* Symbol size for − □ × */
    font-weight: 400;  /* Normal weight */
    border: none;  /* No default button border */
}

/* Minimize and maximize buttons: transparent until hovered */
QPushButton#titleBtnMin,
QPushButton#titleBtnMax {
    background-color: transparent;  /* No background by default */
    color: #64748b;  /* Muted gray icon color */
}

/* Hover state for minimize and maximize */
QPushButton#titleBtnMin:hover,
QPushButton#titleBtnMax:hover {
    background-color: #f1f5f9;  /* Light gray hover background */
    color: #334155;  /* Darker icon on hover */
}

/* Close button: transparent until hovered */
QPushButton#titleBtnClose {
    background-color: transparent;
    color: #64748b;
}

/* Close button hover: red background like macOS/Windows */
QPushButton#titleBtnClose:hover {
    background-color: #ef4444;  /* Red hover background */
    color: #ffffff;  /* White X on red */
}

/* Central widget wrapping entire window content */
QWidget#centralWidget {
    background-color: #eef2f7;  /* Match main window background */
    border-radius: 12px;  /* Rounded outer corners */
}

/* Content area below title bar */
QWidget#contentArea {
    background-color: #eef2f7;
    border-bottom-left-radius: 12px;  /* Round bottom-left corner */
    border-bottom-right-radius: 12px;  /* Round bottom-right corner */
}

/* Large app title in header section */
QLabel#appTitle {
    font-size: 26px;  /* Large heading */
    font-weight: 700;  /* Bold */
    color: #0f172a;  /* Near-black text */
}

/* Subtitle text under app title */
QLabel#appSubtitle {
    font-size: 13px;
    color: #64748b;  /* Muted gray */
}

/* White card panels (Connection, Files, Transfer sections) */
QFrame.card {
    background-color: #ffffff;  /* White card background */
    border: 1px solid #e2e8f0;  /* Light border */
    border-radius: 14px;  /* Rounded card corners */
}

/* Section headers like "CONNECTION", "FILES" */
QLabel.sectionTitle {
    font-size: 12px;
    font-weight: 600;
    color: #475569;
    letter-spacing: 0.4px;  /* Slightly spaced caps look */
}

/* Field labels like "Your IP", "Peer IP" */
QLabel.fieldLabel {
    font-size: 13px;
    color: #64748b;
}

/* Your IP address value display */
QLabel#localIpValue {
    font-size: 18px;
    font-weight: 700;
    color: #4f46e5;  /* Indigo accent color */
    font-family: "Consolas", "Monaco", monospace;  /* Monospace for IP readability */
}

/* Status text below progress bar */
QLabel#statusLabel {
    font-size: 13px;
    color: #64748b;
}

/* File summary label (if used) */
QLabel#fileSummary {
    font-size: 13px;
    color: #334155;
}

/* Empty file summary state */
QLabel#fileSummary[empty="true"] {
    color: #94a3b8;  /* Lighter gray when no files */
}

/* Drag-and-drop file zone */
QFrame#dropZone {
    background-color: #f8fafc;  /* Very light background */
    border: 2px dashed #cbd5e1;  /* Dashed border indicates drop target */
    border-radius: 12px;
    min-height: 120px;  /* Minimum drop zone height */
}

/* Drop zone when file is dragged over it */
QFrame#dropZone[active="true"] {
    border-color: #818cf8;  /* Indigo dashed border on drag-over */
    background-color: #eef2ff;  /* Light indigo background on drag-over */
}

/* Text input fields (Peer IP) */
QLineEdit {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 14px;
    color: #0f172a;
    selection-background-color: #c7d2fe;  /* Indigo text selection color */
}

/* Text input when focused */
QLineEdit:focus {
    border: 1px solid #6366f1;  /* Indigo focus ring */
    background-color: #ffffff;  /* White background when active */
}

/* Default button styling (base for all buttons) */
QPushButton {
    border-radius: 10px;
    padding: 11px 18px;
    font-size: 13px;
    font-weight: 600;
}

/* Browse Files button */
QPushButton#chooseBtn {
    background-color: #f1f5f9;
    color: #334155;
    border: 1px solid #e2e8f0;
}

QPushButton#chooseBtn:hover {
    background-color: #e2e8f0;
}

QPushButton#chooseBtn:pressed {
    background-color: #cbd5e1;
}

/* Send Files primary button */
QPushButton#sendBtn {
    background-color: #4f46e5;  /* Indigo background */
    color: #ffffff;  /* White text */
    border: none;
}

QPushButton#sendBtn:hover {
    background-color: #4338ca;  /* Darker indigo on hover */
}

QPushButton#sendBtn:pressed {
    background-color: #3730a3;  /* Even darker when clicked */
}

/* Receive Files secondary/outline button */
QPushButton#receiveBtn {
    background-color: #ffffff;
    color: #4f46e5;
    border: 1px solid #c7d2fe;  /* Light indigo border */
}

QPushButton#receiveBtn:hover {
    background-color: #eef2ff;
}

QPushButton#receiveBtn:pressed {
    background-color: #e0e7ff;
}

/* Disabled state for all buttons during transfer */
QPushButton:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
    border: 1px solid #e2e8f0;
}

/* Progress bar track (empty portion) */
QProgressBar {
    background-color: #e2e8f0;
    border: none;
    border-radius: 8px;
    min-height: 10px;
    max-height: 10px;
    text-align: center;
}

/* Progress bar filled portion */
QProgressBar::chunk {
    background-color: #6366f1;  /* Indigo fill color */
    border-radius: 8px;
}
"""
