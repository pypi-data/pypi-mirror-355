from .ui_compiled.ValidationDialog import Ui_ValidationDialog
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QDialog
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .MainWindow import MainWindow


class ValidationDialog(Ui_ValidationDialog, QDialog):
    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__(main_window)

        self.setupUi(self)

        self._main_window = main_window

    def _get_message_type_name(self, message_type: str) -> str:
        match message_type:
            case "Error":
                return QCoreApplication.translate("ValidationDialog", "Errors:")
            case "FutureError":
                return QCoreApplication.translate("ValidationDialog", "Future errors:")
            case "Warning":
                return QCoreApplication.translate("ValidationDialog", "Warnings:")
            case "Hint":
                return QCoreApplication.translate("ValidationDialog", "Hint:")
            case _:
                return "Unknown type:"

    def open_dialog(self) -> None:
        try:
            messages = self._main_window.get_desktop_entry().get_validation_messages()
        except FileNotFoundError:
            self.output_box.setPlainText(QCoreApplication.translate("ValidationDialog", "desktop-file-validate was not found"))
            self.exec()
            return

        text = ""
        for message_type in ("Error", "FutureError", "Warning", "Hint"):
            text += self._get_message_type_name(message_type) + "\n"
            if len(messages[message_type]) == 0:
                text += QCoreApplication.translate("ValidationDialog", "None") + "\n"
            else:
                for current_message in messages[message_type]:
                    text += current_message + "\n"
            text += "\n"

        self.output_box.setPlainText(text.strip())
        self.exec()
