from typing import Optional, Tuple, Union

import can
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIntValidator, QMouseEvent
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..utils.validator import Validator


class ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        self.clicked.emit()
        super().mousePressEvent(ev)


class CanMessageEditor(QWidget):
    log_signal = Signal(str, str)
    radix_toggle_signal = Signal()

    def __init__(self, parent=None, initial_radix_type="dec"):
        super().__init__(parent)
        self.is_extended_id = False  # Default: Standard ID
        self.radix_type = initial_radix_type
        self.can_fd_enabled = False
        self._row_size = 8
        self._max_data_bytes = 8

        # color style
        self.style_edit_default = ""
        self.style_edit_hex = """color: #0082FF;
                            font-weight: bold;"""

        # main layout
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self.setLayout(self._layout)

        self._left_container = QWidget()
        self._grid_layout = QGridLayout()
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setHorizontalSpacing(4)
        self._grid_layout.setVerticalSpacing(2)
        self._left_container.setLayout(self._grid_layout)
        self._layout.addWidget(self._left_container)
        self._layout.setAlignment(self._left_container, Qt.AlignmentFlag.AlignTop)

        # ID (StdID/ExtID)
        self.id_button = QPushButton("StdID")
        self.id_button.setMinimumWidth(50)
        self.id_button.clicked.connect(self.toggle_stdid_extid)
        self._grid_layout.addWidget(self.id_button, 0, 0, Qt.AlignmentFlag.AlignBottom)

        # ID (Edit)
        self.id_edit = QLineEdit("0")
        self.id_edit.setValidator(QIntValidator())
        self.id_edit.setMinimumWidth(50)
        self._grid_layout.addWidget(self.id_edit, 0, 1, Qt.AlignmentFlag.AlignBottom)

        # Label for DataFrame
        self.dataframe_label = ClickableLabel("DataFrame")
        self.dataframe_label.clicked.connect(self._toggle_radix)
        self.dataframe_label.setFixedHeight(self.id_edit.sizeHint().height())
        self.dataframe_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._grid_layout.addWidget(
            self.dataframe_label, 0, 2, Qt.AlignmentFlag.AlignBottom
        )

        self._dataframe_button_layout = QVBoxLayout()
        self._dataframe_button_layout.setContentsMargins(0, 0, 0, 0)
        self._dataframe_button_layout.setSpacing(2)

        self.dataframe_add_button = QPushButton("Add 8")
        self.dataframe_add_button.clicked.connect(self._on_add_dataframe_row_clicked)
        self._dataframe_button_layout.addWidget(self.dataframe_add_button)

        self.dataframe_remove_button = QPushButton("Remove 8")
        self.dataframe_remove_button.clicked.connect(
            self._on_remove_dataframe_row_clicked
        )
        self._dataframe_button_layout.addWidget(self.dataframe_remove_button)
        self._layout.addLayout(self._dataframe_button_layout)
        self._layout.setAlignment(
            self._dataframe_button_layout, Qt.AlignmentFlag.AlignTop
        )

        # DataFrame (Edit)
        self.dataframe_edits = []
        self._dataframe_rows = []
        self._add_dataframe_row()
        self._update_dataframe_button_state()

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
        self._update_dataframe_button_state()

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

        # ID
        id_text = self.id_edit.text()
        if not id_text:
            print("ID is empty.")
            self._log("ID is empty.", "red")
            return None, False  # msg , usable
        id_value = Validator.decimalize(id_text, self.radix_type)
        # TODO: Validate id_value with maximam number(StdID and ExtID)

        # data frame
        if self.can_fd_enabled:
            for data_edit in self.dataframe_edits:
                fd_data_text: str = data_edit.text()
                if fd_data_text:
                    value = Validator.decimalize(fd_data_text, self.radix_type)
                    value = max(0, min(value, 255))
                else:
                    value = 0
                dataframe.append(value)
        else:
            for data_edit in self.dataframe_edits:
                can_data_text: str = data_edit.text()
                if can_data_text:
                    value = Validator.decimalize(can_data_text, self.radix_type)
                    value = max(0, min(value, 255))
                    dataframe.append(value)
                else:
                    break

        if not dataframe:
            print("DataFrame is empty.")
            self._log("DataFrame is empty.", "red")
            return None, False  # msg , usable
        dlc = len(dataframe)

        msg = can.Message(
            arbitration_id=id_value,
            data=dataframe,
            dlc=dlc,
            is_extended_id=self.is_extended_id,
            is_fd=self.can_fd_enabled,
            is_rx=False,
        )

        return msg, True  # msg , usable

    @Slot()
    def _toggle_radix(self) -> None:
        self.radix_toggle_signal.emit()

    def _log(self, text: str, color: Optional[str] = None) -> None:
        self.log_signal.emit(text, color)

    def set_can_fd_mode(self, enabled: bool) -> None:
        if self.can_fd_enabled == enabled:
            return

        self.can_fd_enabled = enabled
        self._max_data_bytes = 64 if enabled else 8
        if not enabled:
            self._trim_dataframe_rows(8)
        self._update_dataframe_button_state()

    def _update_dataframe_button_state(self) -> None:
        can_add = (
            self.can_fd_enabled and len(self.dataframe_edits) < self._max_data_bytes
        )
        can_remove = self.can_fd_enabled and len(self.dataframe_edits) > self._row_size
        self.dataframe_add_button.setVisible(self.can_fd_enabled)
        self.dataframe_add_button.setEnabled(can_add)
        self.dataframe_remove_button.setVisible(can_remove)
        self.dataframe_remove_button.setEnabled(can_remove)

    def _create_data_edit(self) -> QLineEdit:
        edit = QLineEdit("0")
        edit.setContentsMargins(0, 0, 0, 0)
        if self.radix_type == "hex":
            edit.setStyleSheet(self.style_edit_hex)
            edit.setValidator(Validator.hex_validator)
        else:
            edit.setStyleSheet(self.style_edit_default)
            edit.setValidator(Validator.dec_validator)
        return edit

    def _add_dataframe_row(self) -> None:
        if len(self.dataframe_edits) >= self._max_data_bytes:
            return

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(2)
        row_edits = []
        for _ in range(self._row_size):
            if len(self.dataframe_edits) >= self._max_data_bytes:
                break
            edit = self._create_data_edit()
            row_edits.append(edit)
            self.dataframe_edits.append(edit)
            row_layout.addWidget(edit)

        self._grid_layout.addLayout(
            row_layout,
            len(self._dataframe_rows),
            3,
            1,
            1,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
        )
        self._dataframe_rows.append((row_layout, row_edits))
        self._update_dataframe_button_state()

    def _trim_dataframe_rows(self, target_total: int) -> None:
        while len(self.dataframe_edits) > target_total and self._dataframe_rows:
            row_layout, row_edits = self._dataframe_rows.pop()
            self._grid_layout.removeItem(row_layout)
            for edit in row_edits:
                self.dataframe_edits.remove(edit)
                edit.setParent(None)
                edit.deleteLater()
            row_layout.setParent(None)
        self._update_dataframe_button_state()

    @Slot()
    def _on_add_dataframe_row_clicked(self) -> None:
        self._add_dataframe_row()

    @Slot()
    def _on_remove_dataframe_row_clicked(self) -> None:
        target_total = max(self._row_size, len(self.dataframe_edits) - self._row_size)
        self._trim_dataframe_rows(target_total)
