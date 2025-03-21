from typing import Optional, Tuple, Union

import can
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from ..utils.validator import Validator


class CanMessageEditor(QWidget):
    log_signal = Signal(str, str)
    radix_toggle_signal = Signal()

    def __init__(self, parent=None, initial_radix_type="dec"):
        super().__init__(parent)
        self.is_extended_id = False  # Default: Standard ID
        self.radix_type = initial_radix_type

        # color style
        self.style_edit_default = ""
        self.style_edit_hex = """color: #0082FF;
                            font-weight: bold;"""

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
        self.dataframe_label.mousePressEvent = lambda event: self._toggle_radix()
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
    def update_radix(self, new_radix: str) -> None:
        # check if radix is same as current radix
        if self.radix_type == new_radix:
            return
        self.radix_type = new_radix  # update radix

        # update style and text
        if new_radix == "dec":
            # ID Edit
            self.id_edit.setStyleSheet(self.style_edit_default)
            self.id_edit.setValidator(Validator.dec_validator)
            self.id_edit.setText(
                Validator.text_decimalize_from_hex_text(self.id_edit.text())
            )
            # DataFrame Edits
            for edit in self.dataframe_edits:
                edit.setStyleSheet(self.style_edit_default)
                edit.setValidator(Validator.dec_validator)
                edit.setText(Validator.text_decimalize_from_hex_text(edit.text()))

        elif new_radix == "hex":
            # ID Edit
            self.id_edit.setStyleSheet(self.style_edit_hex)
            self.id_edit.setValidator(Validator.hex_validator)
            self.id_edit.setText(
                Validator.text_hexadecimalize_from_decimal_text(self.id_edit.text())
            )
            # DataFrame Edits
            for edit in self.dataframe_edits:
                edit.setStyleSheet(self.style_edit_hex)
                edit.setValidator(Validator.hex_validator)
                edit.setText(
                    Validator.text_hexadecimalize_from_decimal_text(edit.text())
                )

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
            return None, False  # msg , usable
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
            return None, False  # msg , usable

        msg = can.Message(
            arbitration_id=id_value,
            data=dataframe,
            dlc=dlc,
            is_extended_id=self.is_extended_id,
            is_rx=False,
        )

        return msg, True  # msg , usable

    @Slot()
    def _toggle_radix(self) -> None:
        self.radix_toggle_signal.emit()

    def _log(self, text: str, color: Optional[str] = None) -> None:
        self.log_signal.emit(text, color)
