"""Main application window."""  # Module docstring: primary PyQt6 GUI for the file transfer app

import socket  # Used to validate peer IP address format
from collections.abc import Callable  # Type hint for callback functions
from pathlib import Path  # Used for file path handling throughout the UI

from PyQt6.QtCore import QObject, Qt, QThread  # Qt core: base object, constants, background threads
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont  # Qt GUI: drag/drop events and font setup
from PyQt6.QtWidgets import (  # Import all Qt widgets used in the main window
    QApplication,  # Main Qt application object (event loop)
    QFileDialog,  # Native file picker dialog
    QFrame,  # Framed container used for cards and drop zone
    QHBoxLayout,  # Horizontal layout manager
    QLabel,  # Text/image display widget
    QLineEdit,  # Single-line text input (Peer IP field)
    QMainWindow,  # Top-level application window
    QMessageBox,  # Popup dialog for info/warning/error messages
    QProgressBar,  # Visual progress indicator during transfer
    QPushButton,  # Clickable button widget
    QVBoxLayout,  # Vertical layout manager
    QWidget,  # Base widget class for containers
)

from file_transfer.network import get_local_ip  # Helper to detect and display this machine's IP
from file_transfer.ui.styles import APP_STYLESHEET  # Global QSS stylesheet for modern UI look
from file_transfer.ui.title_bar import TitleBar  # Custom title bar with min/max/close buttons
from file_transfer.ui.workers import ReceiveWorker, SendWorker  # Background thread workers for transfer

SAVE_DIR = Path.home() / "Downloads"  # Default folder where received files are saved


class DropZone(QFrame):  # Widget where users drag files or click to browse
    """File drop target with click-to-browse."""  # Class docstring

    def __init__(self, on_files_selected: Callable[[list[Path]], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)  # Initialize QFrame with optional parent widget
        self.setObjectName("dropZone")  # CSS object name for drop zone styling
        self.setProperty("active", False)  # Custom property: False = normal, True = drag-over highlight
        self._on_files_selected = on_files_selected  # Callback when user selects or drops files
        self.setAcceptDrops(True)  # Enable drag-and-drop onto this widget
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Show hand cursor to indicate clickability

        layout = QVBoxLayout(self)  # Vertical layout for icon, title, and hint text
        layout.setContentsMargins(20, 18, 20, 18)  # Inner padding inside drop zone
        layout.setSpacing(6)  # Space between stacked labels

        self.icon_label = QLabel("📁")  # Folder emoji icon at top of drop zone
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center icon horizontally
        self.icon_label.setStyleSheet("font-size: 28px; border: none; background: transparent;")  # Large icon, no border

        self.title_label = QLabel("Drop files here")  # Main instruction text
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center text
        self.title_label.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #334155; border: none; background: transparent;"
        )  # Bold dark text, transparent background

        self.hint_label = QLabel("or click to browse")  # Secondary hint below title
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center hint text
        self.hint_label.setStyleSheet(
            "font-size: 12px; color: #94a3b8; border: none; background: transparent;"
        )  # Smaller muted gray text

        layout.addWidget(self.icon_label)  # Add folder icon to layout
        layout.addWidget(self.title_label)  # Add main instruction to layout
        layout.addWidget(self.hint_label)  # Add hint text to layout

    def mousePressEvent(self, event) -> None:  # Called when user clicks inside drop zone
        if event.button() == Qt.MouseButton.LeftButton:  # Only respond to left mouse click
            paths, _ = QFileDialog.getOpenFileNames(self.window(), "Select Files")  # Open native file picker
            if paths:  # If user selected one or more files (didn't cancel)
                self._on_files_selected([Path(p) for p in paths])  # Convert strings to Path and notify main window
        super().mousePressEvent(event)  # Call parent mouse handler

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # Called when drag enters drop zone
        if event.mimeData().hasUrls():  # Check if dragged data contains file URLs
            event.acceptProposedAction()  # Accept the drag operation
            self.setProperty("active", True)  # Set active state for highlighted styling
            self.style().unpolish(self)  # Force Qt to re-read widget properties
            self.style().polish(self)  # Re-apply stylesheet with new active property

    def dragLeaveEvent(self, event) -> None:  # Called when drag leaves drop zone without dropping
        self.setProperty("active", False)  # Remove highlight state
        self.style().unpolish(self)  # Force style refresh
        self.style().polish(self)  # Re-apply normal stylesheet
        super().dragLeaveEvent(event)  # Call parent handler

    def dropEvent(self, event: QDropEvent) -> None:  # Called when user drops files onto drop zone
        paths = []  # List to collect valid dropped file paths
        for url in event.mimeData().urls():  # Loop over each dropped URL
            path = Path(url.toLocalFile())  # Convert URL to local filesystem path
            if path.is_file():  # Only accept actual files (not folders)
                paths.append(path)  # Add valid file to list
        if paths:  # If at least one file was dropped
            self._on_files_selected(paths)  # Notify main window of selected files
        self.setProperty("active", False)  # Remove drag-over highlight
        self.style().unpolish(self)  # Force style refresh
        self.style().polish(self)  # Re-apply normal stylesheet
        event.acceptProposedAction()  # Mark drop as handled

    def set_file_summary(self, count: int, preview: str) -> None:  # Update drop zone text after files are chosen
        if count == 0:  # No files selected — reset to default text
            self.title_label.setText("Drop files here")  # Restore default title
            self.hint_label.setText("or click to browse")  # Restore default hint
            return  # Done resetting
        self.title_label.setText(f"{count} file{'s' if count != 1 else ''} ready")  # Show count (file vs files)
        self.hint_label.setText(preview)  # Show filename preview in hint line


class MainWindow(QMainWindow):  # Main application window containing all UI elements
    def __init__(self) -> None:  # Initialize window, state, and build UI
        super().__init__()  # Call QMainWindow constructor
        self.setWindowTitle("File Transfer")  # Set window title (also shown in taskbar)
        self.setWindowFlags(  # Configure window behavior flags
            Qt.WindowType.Window  # Standard top-level window
            | Qt.WindowType.FramelessWindowHint  # Remove OS title bar; we use custom TitleBar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)  # Solid background (not transparent)
        self.setMinimumSize(520, 660)  # Prevent window from being resized too small
        self.resize(560, 720)  # Default window size on first open

        self._send_thread: QThread | None = None  # Background thread for sending (None when idle)
        self._send_worker: SendWorker | None = None  # Worker object that runs send logic on background thread
        self._receive_thread: QThread | None = None  # Background thread for receiving (None when idle)
        self._receive_worker: ReceiveWorker | None = None  # Worker object that runs receive logic on background thread
        self._selected_files: list[Path] = []  # List of local files user chose to send

        self._build_ui()  # Construct all widgets and layouts
        self._set_status("Ready to send or receive")  # Set initial status message

    def _build_ui(self) -> None:  # Assemble the full window layout
        central = QWidget()  # Root container widget for entire window content
        central.setObjectName("centralWidget")  # CSS object name for styling
        self.setCentralWidget(central)  # Set as the main window's central widget

        root = QVBoxLayout(central)  # Vertical layout: title bar on top, content below
        root.setContentsMargins(0, 0, 0, 0)  # No outer margin (title bar goes edge-to-edge)
        root.setSpacing(0)  # No gap between title bar and content

        self.title_bar = TitleBar(self, "File Transfer")  # Create custom draggable title bar
        root.addWidget(self.title_bar)  # Add title bar at top

        content = QWidget()  # Container for all content below title bar
        content.setObjectName("contentArea")  # CSS object name for content area styling
        content_layout = QVBoxLayout(content)  # Vertical layout for header and cards
        content_layout.setContentsMargins(28, 20, 28, 28)  # Padding around content area
        content_layout.setSpacing(18)  # Space between header and cards

        content_layout.addLayout(self._build_header())  # Add app title and subtitle
        content_layout.addWidget(self._build_connection_card())  # Add IP connection card
        content_layout.addWidget(self._build_files_card())  # Add file selection card
        content_layout.addWidget(self._build_actions_card())  # Add send/receive/progress card
        content_layout.addStretch()  # Push content to top; absorb extra vertical space

        root.addWidget(content)  # Add content area below title bar

    def _build_header(self) -> QVBoxLayout:  # Build app title and subtitle section
        header = QVBoxLayout()  # Vertical stack for title + subtitle
        header.setSpacing(4)  # Small gap between title and subtitle

        title = QLabel("File Transfer")  # Large app name label
        title.setObjectName("appTitle")  # CSS object name for title styling

        subtitle = QLabel("Send files directly between two computers on your network")  # Description text
        subtitle.setObjectName("appSubtitle")  # CSS object name for subtitle styling
        subtitle.setWordWrap(True)  # Wrap long text to multiple lines if needed

        header.addWidget(title)  # Add title to header layout
        header.addWidget(subtitle)  # Add subtitle to header layout
        return header  # Return completed header layout

    def _card(self) -> QFrame:  # Factory method to create a styled white card panel
        card = QFrame()  # Create frame widget
        card.setProperty("class", "card")  # CSS class name "card" for white rounded panel styling
        card.setFrameShape(QFrame.Shape.StyledPanel)  # Use styled panel frame shape
        return card  # Return the empty card (caller adds content)

    def _build_connection_card(self) -> QFrame:  # Build the Connection section card (Your IP + Peer IP)
        card = self._card()  # Create base card frame
        layout = QVBoxLayout(card)  # Vertical layout inside card
        layout.setContentsMargins(20, 18, 20, 18)  # Inner padding
        layout.setSpacing(14)  # Space between rows

        section = QLabel("CONNECTION")  # Section header label
        section.setProperty("class", "sectionTitle")  # CSS class for small caps section title

        local_row = QHBoxLayout()  # Horizontal row for "Your IP" label and value
        local_label = QLabel("Your IP")  # Label text
        local_label.setProperty("class", "fieldLabel")  # CSS class for field labels
        self.local_ip_label = QLabel(get_local_ip())  # Display this machine's detected IP address
        self.local_ip_label.setObjectName("localIpValue")  # CSS object name for IP value styling
        self.local_ip_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)  # Right-align IP
        local_row.addWidget(local_label)  # Add label on left
        local_row.addStretch()  # Spacer pushes IP value to the right
        local_row.addWidget(self.local_ip_label)  # Add IP value on right

        peer_label = QLabel("Peer IP")  # Label for peer IP input
        peer_label.setProperty("class", "fieldLabel")  # CSS class for field labels
        self.peer_ip_edit = QLineEdit()  # Text input for other computer's IP address
        self.peer_ip_edit.setPlaceholderText("Enter the other computer's IP address")  # Gray hint text when empty

        layout.addWidget(section)  # Add "CONNECTION" header
        layout.addLayout(local_row)  # Add Your IP row
        layout.addWidget(peer_label)  # Add Peer IP label
        layout.addWidget(self.peer_ip_edit)  # Add Peer IP input field
        return card  # Return completed connection card

    def _build_files_card(self) -> QFrame:  # Build the Files section card (drop zone + browse button)
        card = self._card()  # Create base card frame
        layout = QVBoxLayout(card)  # Vertical layout inside card
        layout.setContentsMargins(20, 18, 20, 18)  # Inner padding
        layout.setSpacing(12)  # Space between widgets

        section = QLabel("FILES")  # Section header label
        section.setProperty("class", "sectionTitle")  # CSS class for section title

        self.drop_zone = DropZone(self._set_selected_files)  # Create drop zone; callback updates selected files
        self.choose_btn = QPushButton("Browse Files")  # Button to open file picker
        self.choose_btn.setObjectName("chooseBtn")  # CSS object name for browse button styling
        self.choose_btn.clicked.connect(self._pick_files)  # Connect click to file picker handler

        layout.addWidget(section)  # Add "FILES" header
        layout.addWidget(self.drop_zone)  # Add drag-and-drop zone
        layout.addWidget(self.choose_btn, alignment=Qt.AlignmentFlag.AlignLeft)  # Add browse button, left-aligned
        return card  # Return completed files card

    def _build_actions_card(self) -> QFrame:  # Build the Transfer section card (buttons + progress)
        card = self._card()  # Create base card frame
        layout = QVBoxLayout(card)  # Vertical layout inside card
        layout.setContentsMargins(20, 18, 20, 18)  # Inner padding
        layout.setSpacing(14)  # Space between widgets

        section = QLabel("TRANSFER")  # Section header label
        section.setProperty("class", "sectionTitle")  # CSS class for section title

        btn_row = QHBoxLayout()  # Horizontal row for Send and Receive buttons
        btn_row.setSpacing(12)  # Space between buttons

        self.send_btn = QPushButton("Send Files")  # Primary action: send selected files to peer
        self.send_btn.setObjectName("sendBtn")  # CSS object name for send button styling
        self.receive_btn = QPushButton("Receive Files")  # Secondary action: wait for files from peer
        self.receive_btn.setObjectName("receiveBtn")  # CSS object name for receive button styling
        self.send_btn.clicked.connect(self._send_files)  # Connect Send button click handler
        self.receive_btn.clicked.connect(self._receive_files)  # Connect Receive button click handler

        btn_row.addWidget(self.send_btn, stretch=1)  # Add Send button, equal width stretch
        btn_row.addWidget(self.receive_btn, stretch=1)  # Add Receive button, equal width stretch

        self.progress_bar = QProgressBar()  # Progress bar shown during active transfer
        self.progress_bar.setRange(0, 100)  # Progress from 0% to 100%
        self.progress_bar.setValue(0)  # Start at 0%
        self.progress_bar.setTextVisible(False)  # Hide percentage text inside bar (status label shows it)

        self.status_label = QLabel("Ready")  # Text status below progress bar
        self.status_label.setObjectName("statusLabel")  # CSS object name for status text styling

        layout.addWidget(section)  # Add "TRANSFER" header
        layout.addLayout(btn_row)  # Add Send/Receive button row
        layout.addWidget(self.progress_bar)  # Add progress bar
        layout.addWidget(self.status_label)  # Add status label
        return card  # Return completed actions card

    def _set_status(self, message: str) -> None:  # Update the status label text
        self.status_label.setText(message)  # Set new status message

    def _set_selected_files(self, paths: list[Path]) -> None:  # Called when user picks or drops files
        self._selected_files = paths  # Store selected file paths for sending
        if not paths:  # If selection was cleared
            self.drop_zone.set_file_summary(0, "")  # Reset drop zone to default text
            self._set_status("Ready to send or receive")  # Reset status message
            return  # Done handling empty selection

        preview = ", ".join(p.name for p in paths[:2])  # Show names of first 2 files
        if len(paths) > 2:  # If more than 2 files selected
            preview += f" +{len(paths) - 2} more"  # Append count of remaining files
        self.drop_zone.set_file_summary(len(paths), preview)  # Update drop zone with file count and preview
        self._set_status(f"{len(paths)} file(s) selected")  # Update status with selection count

    def _pick_files(self) -> None:  # Open file picker when Browse Files button is clicked
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Files")  # Show native multi-file picker
        self._set_selected_files([Path(p) for p in paths])  # Update selection from picker result

    def _update_progress(self, current: int, total: int) -> None:  # Called from worker thread during transfer
        if total <= 0:  # Guard against invalid total size
            self.progress_bar.setValue(0)  # Reset progress bar
            return  # Nothing to update
        percent = int((current / total) * 100)  # Calculate completion percentage
        self.progress_bar.setValue(percent)  # Update progress bar fill
        self._set_status(f"Transferring… {percent}%")  # Update status text with percentage

    def _validate_peer_ip(self) -> str | None:  # Validate Peer IP input before starting transfer
        if self._is_busy():  # Block if a transfer is already running
            QMessageBox.warning(self, "Busy", "A transfer is already in progress.")  # Show warning popup
            return None  # Return None to signal validation failed

        peer_ip = self.peer_ip_edit.text().strip()  # Get IP text and remove whitespace
        if not peer_ip:  # Empty input
            QMessageBox.warning(self, "Missing IP", "Enter the peer IP address.")  # Show warning popup
            return None  # Validation failed

        try:  # Try to parse IP address format
            socket.inet_aton(peer_ip)  # Validates IPv4 format (raises OSError if invalid)
        except OSError:  # Invalid IP string
            QMessageBox.warning(self, "Invalid IP", "Enter a valid IP address.")  # Show warning popup
            return None  # Validation failed

        return peer_ip  # Return validated IP string

    def _is_busy(self) -> bool:  # Check if send or receive thread is currently running
        send_busy = self._send_thread is not None and self._send_thread.isRunning()  # True if send thread active
        recv_busy = self._receive_thread is not None and self._receive_thread.isRunning()  # True if receive thread active
        return send_busy or recv_busy  # Busy if either thread is running

    def _set_busy(self, busy: bool) -> None:  # Enable/disable UI controls during transfer
        self.choose_btn.setEnabled(not busy)  # Disable browse button while busy
        self.send_btn.setEnabled(not busy)  # Disable send button while busy
        self.receive_btn.setEnabled(not busy)  # Disable receive button while busy
        self.peer_ip_edit.setEnabled(not busy)  # Disable IP input while busy
        self.drop_zone.setEnabled(not busy)  # Disable drop zone while busy

    def _start_worker(self, thread: QThread, worker: QObject, status: str) -> None:  # Start a background transfer worker
        worker.progress.connect(self._update_progress)  # Wire progress signal to UI update handler
        worker.finished.connect(lambda: self._set_busy(False))  # Re-enable UI when worker finishes
        worker.error.connect(self._on_error)  # Wire error signal to error handler
        worker.finished.connect(thread.quit)  # Tell thread to exit when worker finishes
        worker.error.connect(thread.quit)  # Tell thread to exit on error too
        worker.finished.connect(worker.deleteLater)  # Schedule worker for Qt garbage collection
        worker.error.connect(worker.deleteLater)  # Schedule worker cleanup on error as well
        thread.finished.connect(thread.deleteLater)  # Schedule thread for Qt garbage collection
        self._set_busy(True)  # Disable UI controls during transfer
        self.progress_bar.setValue(0)  # Reset progress bar to 0%
        self._set_status(status)  # Show initial status (e.g. "Connecting to peer…")
        thread.start()  # Start the background thread

    def _send_files(self) -> None:  # Handler for Send Files button click
        peer_ip = self._validate_peer_ip()  # Validate peer IP input
        if not peer_ip:  # Validation failed
            return  # Stop — warning already shown
        if not self._selected_files:  # No files chosen
            QMessageBox.warning(self, "No Files", "Choose files to send first.")  # Show warning popup
            return  # Stop — need files to send

        self._send_thread = QThread()  # Create new background thread for sending
        self._send_worker = SendWorker(peer_ip, list(self._selected_files))  # Create worker with IP and file list
        self._send_worker.moveToThread(self._send_thread)  # Move worker to background thread (required by Qt)
        self._send_thread.started.connect(self._send_worker.run)  # Call worker.run() when thread starts
        self._send_worker.finished.connect(self._on_send_finished)  # Show success dialog when send completes
        self._start_worker(self._send_thread, self._send_worker, "Connecting to peer…")  # Start thread and wire signals

    def _receive_files(self) -> None:  # Handler for Receive Files button click
        peer_ip = self._validate_peer_ip()  # Validate peer IP input
        if not peer_ip:  # Validation failed
            return  # Stop — warning already shown

        self._receive_thread = QThread()  # Create new background thread for receiving
        self._receive_worker = ReceiveWorker(peer_ip, SAVE_DIR)  # Create worker with IP and Downloads save path
        self._receive_worker.moveToThread(self._receive_thread)  # Move worker to background thread
        self._receive_thread.started.connect(self._receive_worker.run)  # Call worker.run() when thread starts
        self._receive_worker.file_received.connect(self._on_file_received)  # Show dialog when each file is saved
        self._receive_worker.finished.connect(self._on_receive_finished)  # Update UI when all files received
        self._start_worker(self._receive_thread, self._receive_worker, "Waiting for peer…")  # Start receive thread

    def _on_send_finished(self) -> None:  # Called when send worker completes successfully
        self.progress_bar.setValue(100)  # Fill progress bar to 100%
        self._set_status("Transfer complete")  # Update status text
        QMessageBox.information(self, "Done", "Files sent successfully.")  # Show success popup

    def _on_receive_finished(self) -> None:  # Called when receive worker completes (all files done)
        self.progress_bar.setValue(100)  # Fill progress bar to 100%
        self._set_status("Transfer complete")  # Update status text

    def _on_file_received(self, path: str) -> None:  # Called when each individual file is saved during receive
        self.progress_bar.setValue(100)  # Show full progress for this file
        self._set_status("File received")  # Update status text
        QMessageBox.information(self, "Done", f"Saved to Downloads:\n{Path(path).name}")  # Show saved filename

    def _on_error(self, message: str) -> None:  # Called when worker reports a transfer error
        self._set_busy(False)  # Re-enable UI controls
        self._set_status("Transfer failed")  # Update status text
        QMessageBox.critical(self, "Failed", message)  # Show error popup with message

    def closeEvent(self, event) -> None:  # Called when user closes the window (X button or Alt+F4)
        for thread in (self._send_thread, self._receive_thread):  # Check both send and receive threads
            if thread and thread.isRunning():  # If thread is still active
                thread.quit()  # Request thread to stop its event loop
                thread.wait(2000)  # Wait up to 2 seconds for clean shutdown
        super().closeEvent(event)  # Proceed with normal window close


def run_app() -> None:  # Application entry point: create Qt app, window, and start event loop
    import sys  # Import sys here to get command-line arguments

    app = QApplication(sys.argv)  # Create Qt application with command-line args
    app.setStyle("Fusion")  # Use Fusion style as base (clean cross-platform look)
    app.setStyleSheet(APP_STYLESHEET)  # Apply custom modern stylesheet on top of Fusion

    font = QFont()  # Create application-wide font object
    font.setFamilies(["Segoe UI", "SF Pro Text", "Ubuntu", "Cantarell", "Noto Sans", "sans-serif"])  # Font fallback list
    font.setPointSize(10)  # Default font size for all widgets
    app.setFont(font)  # Apply font to entire application

    window = MainWindow()  # Create main window instance
    window.show()  # Display the window on screen
    sys.exit(app.exec())  # Start Qt event loop; exit with app's return code when window closes
