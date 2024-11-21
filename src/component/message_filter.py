from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLineEdit, QPushButton,
                               QTableWidget, QVBoxLayout, QWidget)

from ..utils.validator import Validator


class MessageFilter(QWidget):
    update_filter_id_signal = Signal(list)

    def __init__(self, initial_radix_type="dec"):
        super().__init__()
        self.radix_type = initial_radix_type
        self.ignore_ids = []

        # color style
        self.style_edit_default = ""
        self.style_edit_hex = """color: #0082FF;
                            font-weight: bold;"""

        # Timer for get table data
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ignore_ids)
        self.timer.start(100)

        # layout
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._table = self.FilterTable(initial_radix_type)
        self._table.setRowCount(6)
        self._layout.addWidget(self._table)

        # button layout
        self._button_layout = QHBoxLayout()
        self._layout.addLayout(self._button_layout)

        # Button for add table
        add_button = QPushButton("Add Filter")
        add_button.clicked.connect(self.add_table_row)
        self._button_layout.addWidget(add_button)

        # Button for clear table
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self._table.clear)
        self._button_layout.addWidget(clear_button)

    @Slot(str)
    def update_ignore_ids(self):
        ignore_ids = []
        for row in range(self._table.rowCount()):
            id_edit = self._table.cellWidget(row, 0)
            checkbox = self._table.cellWidget(row, 2)
            if id_edit and checkbox.findChild(QCheckBox).isChecked():
                text = id_edit.text()
                if text:
                    ignore_ids.append(Validator.decimalize(text, self.radix_type))
        self.ignore_ids = ignore_ids
        self.update_filter_id_signal.emit(ignore_ids)

    def get_ignore_ids(self):
        return self.ignore_ids

    def add_table_row(self):
        self._table._add_table_row(radix_type=self.radix_type)

    def update_radix(self, new_radix: str) -> None:
        if self.radix_type == new_radix:
            return
        self.radix_type = new_radix

        self._table.update_radix(new_radix)
        for row in range(self._table.rowCount()):
            id_edit = self._table.cellWidget(row, 0)
            if id_edit:
                if new_radix == "hex":
                    id_edit.setStyleSheet(self.style_edit_hex)
                    id_edit.setValidator(Validator.hex_validator)
                    id_edit.setText(
                        Validator.text_hexadecimalize_from_decimal_text(id_edit.text())
                    )

                elif new_radix == "dec":
                    id_edit.setStyleSheet(self.style_edit_default)
                    id_edit.setValidator(Validator.dec_validator)
                    id_edit.setText(
                        Validator.text_decimalize_from_hex_text(id_edit.text())
                    )

    class FilterTable(QTableWidget):
        def __init__(self, initial_radix_type="hex"):
            super().__init__()

            # Table Style
            self.style_edit_default = """
                QLineEdit {
                    border: none;
                    outline: none;
                    background-color: transparent;
                    padding: 5px;
                }
            """
            self.style_edit_hex = """
                QLineEdit {
                    border: none;
                    outline: none;
                    background-color: transparent;
                    padding: 5px;
                    color: blue;
                    font-weight: bold
                }
            """
            self.setStyleSheet(
                """
                QTableWidget {
                    gridline-color: #a3a3a3;
                }
                """
            )

            # Table Settings
            self.setColumnCount(3)
            self.setHorizontalHeaderLabels(["Ignore ID", "Memo", "Enable"])
            self.horizontalHeader().setStretchLastSection(True)
            self.setColumnWidth(0, 80)
            self.setColumnWidth(1, 110)
            self.setColumnWidth(2, 45)

            for _ in range(6):
                self._add_table_row(radix_type=initial_radix_type)
            self.radix_type = initial_radix_type

        def _add_table_row(self, id_value="", memo="", radix_type="dec"):
            self.setRowCount(self.rowCount() + 1)

            # LineEdit for ID
            id_edit = QLineEdit()
            id_edit.setText(id_value)
            if radix_type == "hex":
                id_edit.setValidator(Validator.hex_validator)
                id_edit.setStyleSheet(self.style_edit_hex)
            elif radix_type == "dec":
                id_edit.setValidator(Validator.dec_validator)
                id_edit.setStyleSheet(self.style_edit_default)

            # LineEdit for Memo
            memo_edit = QLineEdit()
            memo_edit.setText(memo)
            memo_edit.setStyleSheet(self.style_edit_default)

            # Check-Box
            checkbox = QCheckBox()
            checkbox.setCheckState(Qt.Checked)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)

            # set Widget to Table
            self.setCellWidget(self.rowCount() - 1, 0, id_edit)
            self.setCellWidget(self.rowCount() - 1, 1, memo_edit)
            self.setCellWidget(self.rowCount() - 1, 2, checkbox_widget)

        def keyPressEvent(self, event):
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                current_row = self.currentRow()
                current_column = self.currentColumn()

                # チェックボックスがある列（例えば、2列目）かどうかを確認
                if current_column == 2:
                    checkbox_widget = self.cellWidget(current_row, current_column)
                    if checkbox_widget:
                        checkbox = checkbox_widget.findChild(QCheckBox)
                        if checkbox:
                            checkbox.setChecked(not checkbox.isChecked())
                            return

            # それ以外のキーイベントは親クラスに渡す
            super().keyPressEvent(event)

        def clear(self):
            self.setRowCount(0)
            for _ in range(6):
                self._add_table_row(radix_type=self.radix_type)

        def update_radix(self, new_radix: str) -> None:
            if self.radix_type == new_radix:
                return
            self.radix_type = new_radix
