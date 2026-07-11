"""Custom window title bar with minimize, maximize, and close controls."""  # Module docstring

from PyQt6.QtCore import QPoint, Qt  # QPoint for drag math, Qt for mouse button and alignment constants
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QWidget  # UI widgets for title bar


class TitleBar(QWidget):  # Custom title bar widget replacing the OS window frame
    """Draggable title bar with window control buttons."""  # Class docstring

    def __init__(self, window: QMainWindow, title: str = "File Transfer") -> None:  # Build title bar for a window
        super().__init__(window)  # Initialize QWidget; parent is the main window
        self._window = window  # Reference to main window for move/minimize/maximize/close
        self._drag_start: QPoint | None = None  # Stores mouse offset when dragging starts (None = not dragging)

        self.setObjectName("titleBar")  # CSS object name used by stylesheet for styling
        self.setFixedHeight(44)  # Fixed height in pixels for consistent title bar size

        layout = QHBoxLayout(self)  # Horizontal layout: title on left, buttons on right
        layout.setContentsMargins(16, 0, 8, 0)  # Padding: left 16px, right 8px, top/bottom 0
        layout.setSpacing(8)  # Space between widgets in the layout

        self.title_label = QLabel(title)  # Label showing the window title text
        self.title_label.setObjectName("titleBarLabel")  # CSS object name for title label styling

        self.min_btn = QPushButton("−")  # Minimize button with minus symbol
        self.min_btn.setObjectName("titleBtnMin")  # CSS object name for minimize button styling
        self.min_btn.setToolTip("Minimize")  # Hover tooltip text
        self.min_btn.clicked.connect(window.showMinimized)  # Click minimizes the main window

        self.max_btn = QPushButton("□")  # Maximize button with square symbol
        self.max_btn.setObjectName("titleBtnMax")  # CSS object name for maximize button styling
        self.max_btn.setToolTip("Maximize")  # Hover tooltip text
        self.max_btn.clicked.connect(self._toggle_maximize)  # Click toggles maximize/restore

        self.close_btn = QPushButton("×")  # Close button with X symbol
        self.close_btn.setObjectName("titleBtnClose")  # CSS object name for close button styling
        self.close_btn.setToolTip("Close")  # Hover tooltip text
        self.close_btn.clicked.connect(window.close)  # Click closes the main window

        layout.addWidget(self.title_label)  # Add title label to left side of layout
        layout.addStretch()  # Flexible spacer pushes buttons to the right
        layout.addWidget(self.min_btn)  # Add minimize button
        layout.addWidget(self.max_btn)  # Add maximize button
        layout.addWidget(self.close_btn)  # Add close button

        window.installEventFilter(self)  # Listen for window state changes (e.g. maximized) on main window

    def eventFilter(self, obj, event) -> bool:  # Qt event filter to watch main window state changes
        if obj is self._window and event.type() == event.Type.WindowStateChange:  # Window was maximized/restored
            self._update_maximize_button()  # Update maximize button icon and tooltip
        return super().eventFilter(obj, event)  # Pass event to default handler; return False to not block it

    def _toggle_maximize(self) -> None:  # Toggle between maximized and normal window size
        if self._window.isMaximized():  # If currently maximized
            self._window.showNormal()  # Restore to previous window size
        else:  # If currently normal size
            self._window.showMaximized()  # Expand window to fill screen
        self._update_maximize_button()  # Update button text after state change

    def _update_maximize_button(self) -> None:  # Update maximize button appearance based on window state
        if self._window.isMaximized():  # Window is maximized
            self.max_btn.setText("❐")  # Show restore icon (overlapping squares)
            self.max_btn.setToolTip("Restore")  # Tooltip says Restore
        else:  # Window is normal size
            self.max_btn.setText("□")  # Show maximize icon (single square)
            self.max_btn.setToolTip("Maximize")  # Tooltip says Maximize

    def mousePressEvent(self, event) -> None:  # Called when mouse button is pressed on title bar
        if event.button() == Qt.MouseButton.LeftButton:  # Only start drag on left click
            self._drag_start = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()  # Store drag offset
            event.accept()  # Mark event as handled
        super().mousePressEvent(event)  # Call parent implementation

    def mouseMoveEvent(self, event) -> None:  # Called when mouse moves while over title bar
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_start is not None:  # Left button held while dragging
            if self._window.isMaximized():  # If dragging while maximized
                self._window.showNormal()  # Restore window first so it can be moved
                self._update_maximize_button()  # Update maximize button icon
                self._drag_start = QPoint(self._window.width() // 2, self.height() // 2)  # Reset drag point to center
            self._window.move(event.globalPosition().toPoint() - self._drag_start)  # Move window to follow mouse
            event.accept()  # Mark event as handled
        super().mouseMoveEvent(event)  # Call parent implementation

    def mouseReleaseEvent(self, event) -> None:  # Called when mouse button is released
        self._drag_start = None  # Stop dragging
        super().mouseReleaseEvent(event)  # Call parent implementation

    def mouseDoubleClickEvent(self, event) -> None:  # Called on double-click on title bar
        if event.button() == Qt.MouseButton.LeftButton:  # Left double-click toggles maximize
            self._toggle_maximize()  # Maximize or restore window
            event.accept()  # Mark event as handled
        super().mouseDoubleClickEvent(event)  # Call parent implementation
