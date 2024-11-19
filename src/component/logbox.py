from PySide6.QtCore import Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTextEdit


class LogBox(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Menlo", 14))
        self.setLineWrapMode(QTextEdit.NoWrap)

    @Slot(str, str)
    def log(self, message: str, color: str = None):
        if color is None:
            self.append(message)
        else:
            self.append(f"<font color='{color}'>{message}</font>")
