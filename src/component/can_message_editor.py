from PySide6.QtCore import (QMutex, QRegularExpression, QSettings, Qt, QThread,
                            QTimer, Signal, Slot)
from PySide6.QtGui import (QAction, QFont, QIntValidator, QKeySequence,
                           QRegularExpressionValidator, QTextCursor)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QHBoxLayout,
                               QLabel, QLineEdit, QMainWindow, QPushButton,
                               QTableWidget, QTextEdit, QVBoxLayout, QWidget)


class CanMessageEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_extended_id = False  # Default: Standard ID
        # main layout
        self._layout = QHBoxLayout()
        self.setLayout(self._layout)

        # ID (StdID/ExtID)
        self.id_button = QPushButton("StdID")
        self.id_button.setMinimumWidth(50)
        self.id_button.clicked.connect(self.toggle_stdid_extid)
        self._layout.addWidget(self.id_button)

        # ID (Edit)
        self.id_edit = QLineEdit('0')
        self.id_edit.setValidator(QIntValidator())
        self._layout.addWidget(self.id_edit)

        # Label for DataFrame
        self.dataframe_label = QLabel('DataFrame')
        self.dataframe_label.mousePressEvent = lambda event: self.toggle_radix()
        self._layout.addWidget(self.dataframe_label)

        # DataFrame (Edit)
        self.dataframe_edit = []
        for i in range(8):
            edit = QLineEdit('0')
            edit.setValidator(QIntValidator())
            self.dataframe_edit.append(edit)
            self._layout.addWidget(edit)

    def toggle_stdid_extid(self):
        self.is_extended_id = not self.is_extended_id  # モードを切り替え
        if self.is_extended_id:
            self.id_button.setText("ExtID")
        else:
            self.id_button.setText("StdID")

    def get_message(self):
        pass
        # id = int(self.id_edit.text())
        # dataframe = [int(edit.text()) for edit in self.dataframe_edit]
        # return id, dataframe
