import can
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QWidget)

from ..utils.validator import Validator


class CanMessageEditor(QWidget):
    send_msg_signal = Signal(can.Message)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_extended_id = False  # Default: Standard ID
        self.radix_type = "dec"
        # main layout
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        # ID (StdID/ExtID)
        self.id_button = QPushButton("StdID")
        self.id_button.setMinimumWidth(50)
        self.id_button.clicked.connect(self.toggle_stdid_extid)
        self._layout.addWidget(self.id_button)

        # ID (Edit)
        self.id_edit = QLineEdit("0")
        self.id_edit.setValidator(QIntValidator())
        self._layout.addWidget(self.id_edit)

        # Label for DataFrame
        self.dataframe_label = QLabel("DataFrame")
        self.dataframe_label.mousePressEvent = lambda event: self.toggle_radix()
        self._layout.addWidget(self.dataframe_label)

        # DataFrame (Edit)
        self.dataframe_edits = []
        for i in range(8):
            edit = QLineEdit("0")
            edit.setContentsMargins(0, 0, 0, 0)
            edit.setValidator(QIntValidator())
            self.dataframe_edits.append(edit)
            self._layout.addWidget(edit)

    def toggle_stdid_extid(self):
        self.is_extended_id = not self.is_extended_id
        if self.is_extended_id:
            self.id_button.setText("ExtID")
        else:
            self.id_button.setText("StdID")

    def get_message(self) -> can.Message:
        dataframe = []
        dlc = 8

        # ID
        id_value = Validator.decimalize(self.id_edit.text(), self.radix_type)
        # TODO: Validate id_value with maximam number(StdID and ExtID)

        # data frame
        for n, edit in enumerate(self.dataframe_edits):
            text = edit.text()
            if text:
                value = Validator.decimalize(text, self.radix_type)
                value = max(0, min(value, 255))
                dataframe.append(value)
            else:
                dlc = n
                break

        if not dataframe:
            print("DataFrame is empty.")
            # TODO: error handling when dataframe is empty

        msg = can.Message(
            arbitration_id=id_value,
            data=dataframe,
            dlc=dlc,
            is_extended_id=self.is_extended_id,
            is_rx=False,
        )

        return msg
