from PySide6.QtCore import (
    Property,
    QMutex,
    QObject,
    QRegularExpression,
    QSettings,
    Qt,
    QThread,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QAction,
    QFont,
    QIntValidator,
    QKeySequence,
    QRegularExpressionValidator,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..utils.validator import Validator


class CommunicationController(QWidget):

    send_can_msg_trigger_signal = Signal()
    log_clear_signal = Signal()
    log_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.sendable = False
        self.can_connection_status = False

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        # Interval Label
        self._layout.addWidget(QLabel("Interval (ms):"))
        # Interval Text-Box
        self._interval_edit = QLineEdit()
        self._interval_edit.setValidator(QIntValidator())
        self._interval_edit.textChanged.connect(self._on_interval_edit_changed_callback)
        self._layout.addWidget(self._interval_edit)

        # Clear Button
        self._clear_button = QPushButton("Clear")
        self._clear_button.clicked.connect(self._on_clear_pressed_callback)
        self._layout.addWidget(self._clear_button)

        # Send/Start/Stop Button
        self._start_button = QPushButton("Send")
        self._start_button.clicked.connect(self._on_start_stop_pressed_callback)
        self._layout.addWidget(self._start_button)

        # Periodic Callback with Timer
        self.interval_send_timer = QTimer()
        self.interval_send_timer.timeout.connect(self._on_interval_send)

    @Slot(bool)
    def can_connection_change_callback(self, connected: bool) -> None:
        self.can_connection_status = connected

    def _log(self, text: str, color: str = None) -> None:
        self.log_signal.emit(text, color)

    # When the interval text box is edited, this function is called.
    # If the text box is blank or has a value less than or equal to 0, the button text changes to "Send".
    @Slot()
    def _on_interval_edit_changed_callback(self) -> None:
        if (
            self._interval_edit.text() == ""
            or Validator.decimalize(self._interval_edit.text()) <= 0
        ):
            self._start_button.setText("Send")
        else:
            if self.sendable:
                self._start_button.setText("Stop")
            else:
                self._start_button.setText("Start")

    @Slot()
    def _on_clear_pressed_callback(self) -> None:
        self.log_clear_signal.emit()

    # When the start/stop button is pressed, this function is called.
    # If the button text is "Send", the send_can_msg_trigger_signal is emitted.
    # If the button text is "Start", the 'interval_send_timer' is started with the interval value from the text box, and the button text is changed to "Stop".
    @Slot()
    def _on_start_stop_pressed_callback(self) -> None:
        if self.can_connection_status == False:
            self._log("No connection!! Please connect to CAN device", color="red")
            return

        if self.sendable:
            self.interval_send_timer.stop()
            self.sendable = False
            self._start_button.setText("Start")
            self._log("Stopped sending data")
        else:
            interval_text: str = self._interval_edit.text()
            if interval_text == "" or Validator.decimalize(interval_text) <= 0:
                self.send_can_msg_trigger_signal.emit()
                # self._log("Sent data once")
            else:
                interval_value = Validator.decimalize(interval_text)
                self.interval_send_timer.start(interval_value)
                self._start_button.setText("Stop")
                self.sendable = True
                self._log(f"Started sending data every {interval_value}ms")

    @Slot()
    def _on_interval_send(self) -> None:
        self.send_can_msg_trigger_signal.emit()
