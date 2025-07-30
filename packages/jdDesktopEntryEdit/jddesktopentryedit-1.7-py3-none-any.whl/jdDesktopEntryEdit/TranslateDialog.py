from PyQt6.QtWidgets import QWidget, QDialog, QTableWidgetItem, QPushButton, QMessageBox
from .Functions import clear_table_widget, stretch_table_widget_colums_size
from .ui_compiled.TranslateDialog import Ui_TranslateDialog
from PyQt6.QtCore import QCoreApplication
from typing import Optional
import copy


class TranslateDialog(Ui_TranslateDialog, QDialog):
    def __init__(self) -> None:
        super().__init__()

        self.setupUi(self)

        self._translations: dict[str, dict[str, str]] = {}
        self._current_key: str = ""

        stretch_table_widget_colums_size(self.table_widget)

        self.add_button.clicked.connect(self._add_row)
        self.ok_button.clicked.connect(self._ok_button_clicked)
        self.cancel_button.clicked.connect(self.close)

    def _add_row(self, language: Optional[str] = None, text: Optional[str] = None) -> None:
        row = self.table_widget.rowCount()
        self.table_widget.insertRow(row)

        if language is None:
            self.table_widget.setItem(row, 0, QTableWidgetItem())
        else:
            self.table_widget.setItem(row, 0, QTableWidgetItem(language))

        if text is None:
            self.table_widget.setItem(row, 1, QTableWidgetItem())
        else:
            self.table_widget.setItem(row, 1, QTableWidgetItem(text))

        remove_button = QPushButton(QCoreApplication.translate("TranslateDialog", "Remove"))
        remove_button.clicked.connect(self._remove_button_clicked)
        self.table_widget.setCellWidget(row, 2, remove_button)

    def _remove_button_clicked(self) -> None:
        for i in range(self.table_widget.rowCount()):
            if self.table_widget.cellWidget(i, 2) == self.sender():
                self.table_widget.removeRow(i)
                return

    def _check_valid(self) -> bool:
        known_languages: list[str] = []
        for i in range(self.table_widget.rowCount()):
            language = self.table_widget.item(i, 0).text().strip()

            if language == "":
                QMessageBox.critical(self, QCoreApplication.translate("TranslateDialog", "No Language"), QCoreApplication.translate("TranslateDialog", "You had no Language for at least one Item"))
                return False

            if language in known_languages:
                QMessageBox.critical(self, QCoreApplication.translate("TranslateDialog", "Language double"), QCoreApplication.translate("TranslateDialog", "{{Language}} appears twice or more times in the table").replace("{{Language}}", language))
                return False

            known_languages.append(language)

        return True

    def _ok_button_clicked(self) -> None:
        if not self._check_valid():
            return

        current_translations: dict[str, str] = {}
        for i in range(self.table_widget.rowCount()):
            current_translations[self.table_widget.item(i, 0).text()] = self.table_widget.item(i, 1).text()

        self._translations[self._current_key] = current_translations

        self.close()

    def set_translations(self, key: str, translations: dict[str, str]) -> None:
        self._translations[key] = copy.deepcopy(translations)

    def get_translations(self, key: str, strip_spaces: bool) -> dict[str, str]:
        current_translations: dict[str, str] = {}

        for key, value in self._translations.get(key, {}).items():
            if strip_spaces:
                current_translations[key.strip()] = value.strip()
            else:
                current_translations[key] = value

        return current_translations

    def rename_translations(self, old_key: str, new_key: str) -> None:
        if old_key not in self._translations:
            return

        translations = copy.deepcopy(self._translations[old_key])
        self._translations[new_key] = translations
        del self._translations[old_key]

    def delete_translation(self, key: str) -> None:
        if key in self._translations:
            del self._translations[key]

    def open_dialog(self, parent: QWidget, key: str) -> None:
        self.setParent(parent, self.windowFlags())

        clear_table_widget(self.table_widget)

        for language, text in self._translations.get(key, {}).items():
            self._add_row(language=language, text=text)

        self._current_key = key
        self.exec()

    def clear(self) -> None:
        self._translations.clear()
