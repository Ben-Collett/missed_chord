from qt_notification_data import QtNotificationData
from PySide6 import QtCore, QtWidgets
from typing import Callable


PADDING = 15
WINDOW_GAP = 5
TICK_MS = 30


class QtNotification(QtWidgets.QWidget):
    def __init__(
        self,
        data: QtNotificationData,
        on_close: Callable = lambda _: None,
    ):
        super().__init__()
        self.on_close = on_close
        self.data = data
        self.elapsed_ms = 0

        # Translucent background
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Frameless + always on top
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )

        # ---------------- CONTAINER ----------------
        self.container = QtWidgets.QWidget(self)
        self.container.setObjectName("container")
        self.container.setGeometry(0, 0, data.width, data.height)

        self.container.setStyleSheet("""
            #container {
                background-color: rgba(0, 0, 0, 200);
                color: white;
                border-radius: 10px;
            }
            QLabel {
                background-color: transparent;
            }
            QPushButton#closeButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 18px;
                padding: 0px;
            }
            QPushButton#closeButton:hover {
                color: #ff6666;
            }
            QProgressBar {
                border: none;
                background: rgba(255, 255, 255, 40);
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: rgba(255, 255, 255, 180);
                border-radius: 2px;
            }
        """)

        # ---------------- TITLE ----------------
        self.title_label = QtWidgets.QLabel(self.data.title, self.container)
        self.title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color:white;"
        )

        # ---------------- CONTENT ----------------
        self.content_label = QtWidgets.QLabel(
            self.data.content, self.container)
        self.content_label.setStyleSheet(
            "font-size: 18px;color:white;"
        )

        # ---------------- CLOSE BUTTON ----------------
        self.close_button = QtWidgets.QPushButton("✕", self.container)
        self.close_button.setObjectName("closeButton")
        self.close_button.clicked.connect(self.close)

        # ---------------- PROGRESS BAR ----------------
        self.progress = QtWidgets.QProgressBar(self.container)
        self.progress.setRange(0, 1000)
        self.progress.setValue(1000)
        self.progress.setTextVisible(False)

        # ---------------- TIMER ----------------
        self.timer = None
        if data.duration_ms > 0:
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self._on_tick)
            self.timer.start(TICK_MS)

    # ---------------- TIMER LOGIC ----------------
    def _on_tick(self):
        self.elapsed_ms += TICK_MS
        remaining = max(0, self.data.duration_ms - self.elapsed_ms)

        progress = int((remaining / self.data.duration_ms) * 1000)
        self.progress.setValue(progress)

        if remaining <= 0:
            self.close()

    # ---------------- CLOSE ----------------
    def close(self):
        if self.timer:
            self.timer.stop()
        self.on_close(self)
        return super().close()

    # ---------------- LAYOUT ----------------
    def resizeEvent(self, event):
        self.container.setGeometry(0, 0, self.width(), self.height())

        self.title_label.setGeometry(
            PADDING,
            PADDING,
            self.width() - 2 * PADDING - 30,
            30
        )

        self.content_label.setGeometry(
            PADDING,
            PADDING + 35,
            self.width() - 2 * PADDING - 30,
            30
        )

        self.close_button.setGeometry(
            self.width() - PADDING - 24,
            (self.height() - 24) // 2,
            24,
            24
        )

        self.progress.setGeometry(
            PADDING,
            self.height() - self.data.duration_height - 6,
            self.width() - 2 * PADDING,
            self.data.duration_height
        )

        super().resizeEvent(event)

    # ---------------- POSITIONING ----------------
    def update_position(self, number_before=0):
        screen = QtWidgets.QApplication.primaryScreen()
        geometry = screen.availableGeometry()

        margin = 2
        width = self.data.width
        height = self.data.height
        x = geometry.right() - width - margin
        top = geometry.top()
        y = top + margin + number_before * (height + WINDOW_GAP)

        self.move(x, y)
