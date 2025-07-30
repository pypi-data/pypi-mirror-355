from .Functions import string_not_none, none_if_empty_string, list_widget_contains_item
from .ui_compiled.EditActionDialog import Ui_EditActionDialog
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import QCoreApplication
from typing import Literal, TYPE_CHECKING
import desktop_entry_lib


if TYPE_CHECKING:
    from .Environment import Environment
    from .MainWindow import MainWindow


class EditActionDialog(Ui_EditActionDialog, QDialog):
    def __init__(self, main_window: "MainWindow", env: "Environment") -> None:
        super().__init__(main_window)

        self.setupUi(self)

        self._action_data: dict[str, dict[Literal["name", "icon", "exec"], str]] = {}
        self._main_window = main_window
        self._current_identifier = ""
        self._ok = False
        self._env = env

        self.translate_name_button.clicked.connect(lambda: self._env.translate_dialog.open_dialog(self, f"Action.{self._current_identifier}.Name"))

        self.button_box.accepted.connect(self._ok_button_clicked)
        self.button_box.rejected.connect(self.close)

    def _ok_button_clicked(self) -> None:
        identifier = self.edit_identifier.text().strip()

        if identifier == "":
            QMessageBox.critical(self, QCoreApplication.translate("EditActionDialog", "Identifier empty"), QCoreApplication.translate("EditActionDialog", "The Identifier can't be empty"))
            return

        if identifier != self._current_identifier:
            if not desktop_entry_lib.is_action_identifier_valid(identifier):
                QMessageBox.critical(self, QCoreApplication.translate("EditActionDialog", "Invalid Identifier"), QCoreApplication.translate("EditActionDialog", "This Identifier is not valid"))
                return

            if list_widget_contains_item(self._main_window.actions_list, identifier):
                QMessageBox.critical(self, QCoreApplication.translate("EditActionDialog", "Identifier exists"), QCoreApplication.translate("EditActionDialog", "This Identifier already exists"))
                return

            if self._current_identifier in self._action_data:
                del self._action_data[self._current_identifier]

            self._env.translate_dialog.rename_translations(f"Action.{self._current_identifier}.Name", f"Action.{identifier}.Name")
            self._current_identifier = identifier

        self._action_data[identifier] = {}
        self._action_data[identifier]["name"] = self.name_edit.text()
        self._action_data[identifier]["icon"] = self.icon_edit.text()
        self._action_data[identifier]["exec"] = self.exec_edit.text()

        self._ok = True
        self.close()

    def open_dialog(self, identifier: str) -> tuple[str, bool]:
        self._current_identifier = identifier

        self.setWindowTitle(QCoreApplication.translate("EditActionDialog", "Edit {{identifier}}".replace("{{identifier}}", identifier)))

        self.edit_identifier.setText(identifier)

        if identifier in self._action_data:
            self.name_edit.setText(self._action_data[identifier]["name"])
            self.icon_edit.setText(self._action_data[identifier]["icon"])
            self.exec_edit.setText(self._action_data[identifier]["exec"])
        else:
            self.name_edit.setText("")
            self.icon_edit.setText("")
            self.exec_edit.setText("")

        self._ok = False

        self.exec()

        return (self._current_identifier, self._ok)

    def load_desktop_action(self, identifier: str, action: desktop_entry_lib.DesktopAction) -> None:
        self._action_data[identifier] = {}
        self._action_data[identifier]["name"] = action.Name.default_text
        self._env.translate_dialog.set_translations(f"Action.{identifier}.Name", action.Name.translations)
        self._action_data[identifier]["icon"] = string_not_none(action.Icon)
        self._action_data[identifier]["exec"] = string_not_none(action.Exec)

    def get_desktop_action(self, identifier: str) -> desktop_entry_lib.DesktopAction:
        action = desktop_entry_lib.DesktopAction()
        if self._env.settings.get("stripSpaces"):
            action.Name.default_text = self._action_data[identifier]["name"].strip()
        else:
            action.Name.default_text = self._action_data[identifier]["name"]
        action.Name.translations = self._env.translate_dialog.get_translations(f"Action.{identifier}.Name", self._env.settings.get("stripSpaces"))
        action.Icon = none_if_empty_string(self._action_data[identifier]["icon"], self._env.settings.get("stripSpaces"))
        action.Exec = none_if_empty_string(self._action_data[identifier]["exec"], self._env.settings.get("stripSpaces"))
        return action

    def delete_action(self, identifier: str) -> None:
        self._env.translate_dialog.delete_translation(f"Action.{identifier}.Name")
        if identifier in self._action_data:
            del self._action_data[identifier]

    def clear(self) -> None:
        self._action_data.clear()
