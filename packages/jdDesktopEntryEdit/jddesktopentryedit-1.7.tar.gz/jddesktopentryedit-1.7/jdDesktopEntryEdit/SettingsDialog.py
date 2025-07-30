from .ui_compiled.SettingsDialog import Ui_SettingsDialog
from PyQt6.QtCore import Qt, QCoreApplication
from .Functions import select_combo_box_data
from PyQt6.QtWidgets import QDialog, QStyle
from .Languages import get_language_names
from typing import TYPE_CHECKING
from PyQt6.QtGui import QIcon
import sys
import os


if TYPE_CHECKING:
    from .Environment import Environment
    from .MainWindow import MainWindow


class SettingsDialog(Ui_SettingsDialog, QDialog):
    def __init__(self, main_window: "MainWindow", env: "Environment") -> None:
        super().__init__(main_window)

        self.setupUi(self)

        self._env = env
        self._main_window = main_window

        language_names = get_language_names()
        self.language_box.addItem(language_names["en"], "en")
        translations_found = False
        for i in os.listdir(os.path.join(env.program_dir, "translations")):
            if i.endswith(".qm"):
                language = i.removeprefix("jdDesktopEntryEdit_").removesuffix(".qm")
                self.language_box.addItem(language_names.get(language, language), language)
                translations_found = True

        self.language_box.model().sort(0, Qt.SortOrder.AscendingOrder)
        self.language_box.insertItem(0, QCoreApplication.translate("SettingsDialog", "System language"), "default")

        if not translations_found:
            print("No translations where found. make sure you run the BuildTranslations script", file=sys.stderr)

        self.window_title_box.addItem(QCoreApplication.translate("SettingsDialog", "Nothing"), "none")
        self.window_title_box.addItem(QCoreApplication.translate("SettingsDialog", "Filename"), "filename")
        self.window_title_box.addItem(QCoreApplication.translate("SettingsDialog", "Path"), "path")

        self.reset_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)))
        self.ok_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogOkButton)))
        self.cancel_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)))

        self.reset_button.clicked.connect(self._reset_button_clicked)
        self.ok_button.clicked.connect(self._ok_button_clicked)
        self.cancel_button.clicked.connect(self.close)

    def _update_widgets(self) -> None:
        index = self.language_box.findData(self._env.settings.get("language"))
        if index == -1:
            self.language_box.setCurrentIndex(0)
        else:
            self.language_box.setCurrentIndex(index)

        self.recent_files_spin_box.setValue(self._env.settings.get("recentFilesLength"))
        select_combo_box_data(self.window_title_box, self._env.settings.get("windowTitleType"))
        self.check_save_check_box.setChecked(self._env.settings.get("checkSaveBeforeClosing"))
        self.title_edited_check_box.setChecked(self._env.settings.get("showEditedTitle"))
        self.add_comment_check_box.setChecked(self._env.settings.get("addCommentSave"))
        self.strip_spaces_check_box.setChecked(self._env.settings.get("stripSpaces"))

    def _reset_button_clicked(self) -> None:
        self._env.settings.reset()
        self._update_widgets()

    def _ok_button_clicked(self) -> None:
        self._env.settings.set("language", self.language_box.currentData())
        self._env.settings.set("recentFilesLength", self.recent_files_spin_box.value())
        self._env.settings.set("windowTitleType", self.window_title_box.currentData())
        self._env.settings.set("checkSaveBeforeClosing", self.check_save_check_box.isChecked())
        self._env.settings.set("showEditedTitle", self.title_edited_check_box.isChecked())
        self._env.settings.set("addCommentSave", self.add_comment_check_box.isChecked())
        self._env.settings.set("stripSpaces", self.strip_spaces_check_box.isChecked())

        self._env.save_recent_files()

        self._main_window.update_window_title()

        self._env.settings.save(os.path.join(self._env.data_dir, "settings.json"))
        self.close()

    def open_dialog(self) -> None:
        self._update_widgets()
        self.exec()
