from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QIntValidator, QRegularExpressionValidator


class Validator:
    hex_validator = QRegularExpressionValidator(
        QRegularExpression("^[0-9A-Fa-f]+$")
    )  # HEX
    dec_validator = QIntValidator()  # DEC

    @staticmethod
    def decimalize(value_str: str = "", radix_type="dec") -> int:
        if radix_type == "hex":
            value = int(str(value_str.replace(",", "")).strip(), 16)
        else:
            value = int(value_str.replace(",", "").strip())
        return value

    # @staticmethod
    # def decimalize_hex_to_str