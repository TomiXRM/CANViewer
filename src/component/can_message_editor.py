from typing import Tuple, Union

import can
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from ..utils.validator import Validator


class CanMessageEditor(QWidget):
    log_signal = Signal(str, str)

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

    @Slot(str)
    def update_radix(self, radix: str) -> None:
        self.radix_type = radix

    @Slot()
    def toggle_stdid_extid(self) -> None:
        self.is_extended_id = not self.is_extended_id
        if self.is_extended_id:
            self.id_button.setText("ExtID")
        else:
            self.id_button.setText("StdID")

    # returns message and usable(True/False)
    def get_message(self) -> Tuple[Union[can.Message, None], bool]:
        dataframe = []
        dlc = 8

        # ID
        id_text = self.id_edit.text()
        if not id_text:
            print("ID is empty.")
            self._log("ID is empty.", "red")
            return [None, False]  # msg , usable
        id_value = Validator.decimalize(id_text, self.radix_type)
        # TODO: Validate id_value with maximam number(StdID and ExtID)

        # data frame
        for n, data_edit in enumerate(self.dataframe_edits):
            data_text: str = data_edit.text()
            if data_text:
                value = Validator.decimalize(data_text, self.radix_type)
                value = max(0, min(value, 255))
                dataframe.append(value)
            else:
                dlc = n
                break

        if not dataframe:
            print("DataFrame is empty.")
            self._log("DataFrame is empty.", "red")
            return [None, False]  # msg , usable
            # TODO: error handling when dataframe is empty

        msg = can.Message(
            arbitration_id=id_value,
            data=dataframe,
            dlc=dlc,
            is_extended_id=self.is_extended_id,
            is_rx=False,
        )

        return [msg, True]  # msg , usable

    def _log(self, text: str, color: str = None) -> None:
        self.log_signal.emit(text, color)
