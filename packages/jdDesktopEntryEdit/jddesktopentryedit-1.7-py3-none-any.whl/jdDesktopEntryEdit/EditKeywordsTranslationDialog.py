from PyQt6.QtWidgets import QDialog, QLineEdit, QPushButton, QLabel, QMessageBox, QApplication, QStyle, QHBoxLayout, QVBoxLayout
from .Functions import list_widget_contains_item
from .ListEditWidget import ListEditWidget
from typing import Optional, TYPE_CHECKING
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QIcon


if TYPE_CHECKING:
    from .MainWindow import MainWindow


class EditKeywordsTranslationDialog(QDialog):
    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__(main_window)

        self._translations: dict[str, list[str]] = {}
        self._main_window = main_window
        self._current_language = ""
        self._ok = False

        self._language_edit = QLineEdit()
        self._list_widget = ListEditWidget(None, "")
        ok_button = QPushButton(QCoreApplication.translate("EditKeywordsTranslationDialog", "OK"))
        cancel_button = QPushButton(QCoreApplication.translate("EditKeywordsTranslationDialog", "Cancel"))

        ok_button.setIcon(QIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogOkButton)))
        cancel_button.setIcon(QIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)))

        ok_button.clicked.connect(self._ok_button_clicked)
        cancel_button.clicked.connect(self.close)

        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel(QCoreApplication.translate("EditKeywordsTranslationDialog", "Language")))
        language_layout.addWidget(self._language_edit)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(language_layout)
        main_layout.addWidget(self._list_widget)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _ok_button_clicked(self) -> None:
        language = self._language_edit.text().strip()

        if language == "":
            QMessageBox.critical(self, QCoreApplication.translate("EditKeywordsTranslationDialog", "No Language"), QCoreApplication.translate("EditKeywordsTranslationDialog", "You have to enter a Language"))
            return

        if language != self._current_language:
            if list_widget_contains_item(self._main_window.keywords_language_list, language):
                QMessageBox.critical(self, QCoreApplication.translate("EditKeywordsTranslationDialog", "Language exists"), QCoreApplication.translate("EditKeywordsTranslationDialog", "This Language already exists"))
                return

            if self._current_language is not None:
                del self._translations[self._current_language]

            self._current_language = language

        self._translations[language] = self._list_widget.get_list(False)

        self._current_language = language
        self._ok = True

        self.close()

    def open_dialog(self, language: Optional[str]) -> Optional[str]:
        self._current_language = language

        if language is None:
            self.setWindowTitle(QCoreApplication.translate("EditKeywordsTranslationDialog", "Add new Keywords translation"))
        else:
            self.setWindowTitle(QCoreApplication.translate("EditKeywordsTranslationDialog", "Edit Keywords for {{language}}").replace("{{language}}", language))

        if language is None:
            self._language_edit.setText("")
            self._list_widget.clear()
        else:
            self._language_edit.setText(language)
            self._list_widget.set_list(self._translations[language])

        self._ok = False

        self.exec()

        if not self._ok:
            return None
        else:
            return self._current_language

    def set_translation(self, language: str, translation: list[str]) -> None:
        self._translations[language] = translation

    def get_translation(self, language: str, strip_spaces: bool) -> list[str]:
        translated_list: list[str] = []
        for i in self._translations[language]:
            if strip_spaces:
                translated_list.append(i.strip())
            else:
                translated_list.append(i)
        return translated_list

    def delete_translation(self, language: str) -> None:
        if language in self._translations:
            del self._translations[language]

    def clear(self) -> None:
        self._translations.clear()
