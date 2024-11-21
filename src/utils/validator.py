from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QIntValidator, QRegularExpressionValidator
from PySide6.QtWidgets import QLineEdit


class Validator:
    # HEX
    hex_validator = QRegularExpressionValidator(QRegularExpression("^[0-9A-Fa-f]+$"))
    # DEC
    dec_validator = QIntValidator()

    @staticmethod
    def decimalize(value_str: str = "", radix_type="dec") -> int:
        if radix_type == "hex":
            value = int(str(value_str.replace(",", "")).strip(), 16)
        else:
            value = int(value_str.replace(",", "").strip())
        return value

    @staticmethod
    def text_decimalize_from_hex_text(self, hex_text: str) -> str:
        dec_value: int = self.decimalize(hex_text)
        hex_value_text: str = hex(dec_value)[2:].upper()
        return hex_value_text

    @staticmethod
    def text_hexadecimalize_from_decimal_text(self, dec_text: str) -> str:
        hex_value: int = int(dec_text, 16)
        dec_value_text: str = str(hex_value)
        return dec_value_text

    @staticmethod
    def assign_style_on_text_edit_with_radix(
        text_edit: QLineEdit, radix_type: str
    ) -> None:
        if radix_type == "dec":
            pass
        elif radix_type == "hex":
            pass
