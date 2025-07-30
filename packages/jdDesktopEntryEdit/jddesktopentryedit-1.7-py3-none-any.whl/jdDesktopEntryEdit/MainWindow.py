from .Functions import clear_table_widget, stretch_table_widget_colums_size, string_not_none, none_if_empty_string, boolean_not_none, none_if_false, list_widget_contains_item, get_sender_table_row, get_logical_table_row_list, check_optional_module, get_requests_response, is_flatpak, get_document_portal_version, get_real_path
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QInputDialog, QMessageBox, QTableWidgetItem, QPushButton, QLineEdit, QCheckBox, QRadioButton, QApplication
from PyQt6.QtGui import QAction, QDragEnterEvent, QDropEvent, QCloseEvent, QKeySequence
from .EditKeywordsTranslationDialog import EditKeywordsTranslationDialog
from .ManageTemplatesWindow import ManageTemplatesWindow
from PyQt6.QtCore import QCoreApplication, pyqtSignal
from .ui_compiled.MainWindow import Ui_MainWindow
from .ValidationDialog import ValidationDialog
from .EditActionDialog import EditActionDialog
from .ListEditWidget import ListEditWidget
from .SettingsDialog import SettingsDialog
from .PreviewDialog import PreviewDialog
from .WelcomeDialog import WelcomeDialog
from .AboutDialog import AboutDialog
from .Environment import Environment
from typing import Optional
import desktop_entry_lib
import webbrowser
import traceback
import copy
import sys
import os


class MainWindow(Ui_MainWindow, QMainWindow):
    file_opened = pyqtSignal("QString")
    file_saved = pyqtSignal("QString")

    def __init__(self, env: Environment) -> None:
        super().__init__()

        self.setupUi(self)

        self._env = env
        self._is_modified = False

        self._edit_keywords_translation_dialog = EditKeywordsTranslationDialog(self)
        self._manage_templates_window = ManageTemplatesWindow(self, env)
        self._edit_action_dialog = EditActionDialog(self, env)
        self._current_entry = desktop_entry_lib.DesktopEntry()
        self._settings_dialog = SettingsDialog(self, env)
        self._validation_dialog = ValidationDialog(self)
        self._welcome_dialog = WelcomeDialog(self, env)
        self._preview_dialog = PreviewDialog(self, env)
        self._about_dialog = AboutDialog(self, env)
        self._current_path: Optional[str] = None

        self.edit_mime_type_widget = ListEditWidget(self, QCoreApplication.translate("MainWindow", "A list of MimeTypes that this Application can open"))
        self.edit_untranslated_keywords_widget = ListEditWidget(self, QCoreApplication.translate("MainWindow", "The untranslated Keywords"))
        self.edit_implements_widget = ListEditWidget(self, QCoreApplication.translate("MainWindow", "A list of interfaces that this application implements. If you don't know what this means, you probably won't need it."))
        self.edit_only_show_in_widget = ListEditWidget(self, QCoreApplication.translate("MainWindow", "If set, the Application is only visible when using this Desktop Environments"))
        self.edit_not_show_in_widget = ListEditWidget(self, QCoreApplication.translate("MainWindow", "The Application is not visible when using this Desktop Environments"))

        self.mime_type_layout.addWidget(self.edit_mime_type_widget)
        self.untranslated_keywords_layout.addWidget(self.edit_untranslated_keywords_widget)
        self.implements_layout.addWidget(self.edit_implements_widget)
        self.only_show_in_layout.addWidget(self.edit_only_show_in_widget)
        self.not_show_in_layout.addWidget(self.edit_not_show_in_widget)

        self.new_action.setShortcut(QKeySequence(QKeySequence.StandardKey.New))
        self.open_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Open))
        self.save_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Save))
        self.save_as_action.setShortcut(QKeySequence(QKeySequence.StandardKey.SaveAs))
        self.exit_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit))

        self.settings_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Preferences))

        self.new_action.triggered.connect(self._new_action_clicked)
        self.open_action.triggered.connect(self._open_action_clicked)
        self.open_url_action.triggered.connect(self._open_url_action_clicked)
        self.save_action.triggered.connect(self._save_action_clicked)
        self.save_as_action.triggered.connect(self._save_as_action_clicked)
        self.exit_action.triggered.connect(self._exit_action_clicked)

        self.settings_action.triggered.connect(self._settings_dialog.open_dialog)
        self.manage_templates_action.triggered.connect(self._manage_templates_window.open_dialog)

        self.validate_action.triggered.connect(self._validation_dialog.open_dialog)
        self.preview_action.triggered.connect(lambda: self._preview_dialog.open_preview(self.get_desktop_entry().get_text()))

        self.welcome_dialog_action.triggered.connect(self._welcome_dialog.open_dialog)
        self.specification_action.triggered.connect(lambda: webbrowser.open("https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html"))
        self.view_source_action.triggered.connect(lambda: webbrowser.open("https://codeberg.org/JakobDev/jdDesktopEntryEdit"))
        self.report_bug_action.triggered.connect(lambda: webbrowser.open("https://codeberg.org/JakobDev/jdDesktopEntryEdit/issues"))
        self.translate_action.triggered.connect(lambda: webbrowser.open("https://translate.codeberg.org/projects/jdDesktopEntryEdit"))
        self.donate_action.triggered.connect(lambda: webbrowser.open("https://ko-fi.com/jakobdev"))
        self.about_action.triggered.connect(self._about_dialog.exec)
        self.about_qt_action.triggered.connect(QApplication.instance().aboutQt)

        self.translate_name_button.clicked.connect(lambda: self._env.translate_dialog.open_dialog(self, "Name"))
        self.translate_generic_name_button.clicked.connect(lambda: self._env.translate_dialog.open_dialog(self, "GenericName"))
        self.translate_comment_button.clicked.connect(lambda: self._env.translate_dialog.open_dialog(self, "Comment"))

        self.browse_icon_button.clicked.connect(self._browse_icon_button_clicked)
        self.browse_exec_button.clicked.connect(self._browse_exec_button_clicked)
        self.browse_try_exec_button.clicked.connect(self._browse_try_exec_button_clicked)
        self.browse_path_button.clicked.connect(self._browse_path_button_clicked)

        self.categories_list.itemSelectionChanged.connect(self._update_categorie_remove_button_enabled)
        self.add_categorie_button.clicked.connect(self._add_categorie_button_clicked)
        self.remove_categorie_button.clicked.connect(self._remove_categorie_button_clicked)

        self.keywords_language_list.itemSelectionChanged.connect(self._update_keywords_langauge_buttons_enabled)
        self.add_keywords_language_button.clicked.connect(self._add_keywords_language_button_clicked)
        self.edit_keywords_language_button.clicked.connect(self._edit_keywords_language_button_clicked)
        self.remove_keywords_language_button.clicked.connect(self._edit_keywords_language_button_clicked)

        self.actions_list.itemSelectionChanged.connect(self._update_action_buttons_enabled)
        self.add_action_button.clicked.connect(self._add_action_button_clicked)
        self.edit_action_button.clicked.connect(self._edit_action_button_clicked)
        self.delete_action_button.clicked.connect(self._delete_action_button_clicked)

        self.add_custom_button.pressed.connect(self._add_custom_row)
        self.check_custom_button.clicked.connect(self._check_custom_button_clicked)

        self.keywords_tab_widget.tabBar().setDocumentMode(True)
        self.keywords_tab_widget.tabBar().setExpanding(True)

        self.main_tab_widget.setCurrentIndex(0)
        self.keywords_tab_widget.setCurrentIndex(0)

        stretch_table_widget_colums_size(self.custom_table)

        for widget in vars(self).values():
            if isinstance(widget, QLineEdit):
                widget.textEdited.connect(lambda: self.set_file_edited(True))
            elif isinstance(widget, QCheckBox):
                widget.stateChanged.connect(lambda: self.set_file_edited(True))
            elif isinstance(widget, QRadioButton):
                widget.clicked.connect(lambda: self.set_file_edited(True))

        if is_flatpak() and get_document_portal_version() < 5:
            self.browse_icon_button.setVisible(False)
            self.browse_exec_button.setVisible(False)
            self.browse_try_exec_button.setVisible(False)
            self.browse_path_button.setVisible(False)

        self._new_action_clicked()

        self.update_window_title()
        self.update_template_file_menu()
        self._update_recent_files_menu()

        self._update_categorie_remove_button_enabled()
        self._update_keywords_langauge_buttons_enabled()
        self._update_action_buttons_enabled()

        self.setAcceptDrops(True)

    def startup(self) -> None:
        if self._env.settings.get("showWelcomeDialog"):
            self._welcome_dialog.open_dialog()

    def _ask_for_save(self) -> bool:
        if not self._is_modified:
            return True

        if not self._env.settings.get("checkSaveBeforeClosing"):
            return True

        match QMessageBox.warning(self, QCoreApplication.translate("MainWindow", "Unsaved changes"), QCoreApplication.translate("MainWindow", "You have unsaved changes. Do you want to save now?"), QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel):
            case QMessageBox.StandardButton.Save:
                self._save_action_clicked()
                return True
            case QMessageBox.StandardButton.Discard:
                return True
            case QMessageBox.StandardButton.Cancel:
                return False

    def update_window_title(self) -> None:
        untitled = QCoreApplication.translate("MainWindow", "Untitled")

        match self._env.settings.get("windowTitleType"):
            case "none":
                title = "jdDesktopEntryEdit"
            case "filename":
                if self._current_path is None:
                    title = untitled + " - jdDesktopEntryEdit"
                else:
                    title = os.path.basename(self._current_path) + " - jdDesktopEntryEdit"
            case "path":
                if self._current_path is None:
                    title = untitled + " - jdDesktopEntryEdit"
                else:
                    title = get_real_path(self._current_path) + " - jdDesktopEntryEdit"
            case _:
                title = QCoreApplication.translate("MainWindow", "Error")

        if self._is_modified and self._env.settings.get("showEditedTitle"):
            title = "*" + title

        self.setWindowTitle(title)

    def set_file_edited(self, edited: bool) -> None:
        self._is_modified = edited
        self.update_window_title()

    def update_template_file_menu(self) -> None:
        self.new_template_file_menu.clear()

        if len(self._env.template_list) == 0:
            empty_action = QAction(QCoreApplication.translate("MainWindow", "No templates found"), self)
            empty_action.setEnabled(False)
            self.new_template_file_menu.addAction(empty_action)
        else:
            for i in self._env.template_list:
                template_action = QAction(i, self)
                template_action.setData(i)
                template_action.triggered.connect(self._new_template_file_clicked)
                self.new_template_file_menu.addAction(template_action)

    def _new_template_file_clicked(self) -> None:
        if not self._ask_for_save():
            return

        action = self.sender()
        if action:
            self._load_desktop_enty(desktop_entry_lib.DesktopEntry.from_file(os.path.join(self._env.data_dir, "templates", action.data() + ".desktop")))
            self.set_file_edited(False)

    def _update_recent_files_menu(self) -> None:
        self.recent_files_menu.clear()

        if len(self._env.recent_files) == 0:
            empty_action = QAction(QCoreApplication.translate("MainWindow", "No recent files"), self)
            empty_action.setEnabled(False)
            self.recent_files_menu.addAction(empty_action)
            return

        for i in self._env.recent_files:
            file_action = QAction(get_real_path(i), self)
            file_action.setData(i)
            file_action.triggered.connect(self._open_recent_file)
            self.recent_files_menu.addAction(file_action)

        self.recent_files_menu.addSeparator()

        clear_action = QAction(QCoreApplication.translate("MainWindow", "Clear"), self)
        clear_action.triggered.connect(self._clear_recent_files)
        self.recent_files_menu.addAction(clear_action)

    def _open_recent_file(self) -> None:
        action = self.sender()
        if action:
            self.open_file(action.data(), ask=True)

    def _clear_recent_files(self) -> None:
        self._env.clear_recent_files()
        self._update_recent_files_menu()

    def _new_action_clicked(self) -> None:
        if not self._ask_for_save():
            return

        self.reset()

    def _open_action_clicked(self) -> None:
        if not self._ask_for_save():
            return

        filter = QCoreApplication.translate("MainWindow", "Desktop Entries") + " (*.desktop);;" + QCoreApplication.translate("MainWindow", "All Files") + " (*)"
        path = QFileDialog.getOpenFileName(self, filter=filter)[0]

        if path != "":
            self.open_file(path)

    def _open_url_action_clicked(self) -> None:
        if not check_optional_module("requests", self):
            return

        if not self._ask_for_save():
            return

        url = QInputDialog.getText(self, QCoreApplication.translate("MainWindow", "Open URL"), QCoreApplication.translate("MainWindow", "Please enter the URL to the Desktop Entry"))[0].strip()

        if url == "":
            return

        self.open_url(url)

    def _save_action_clicked(self) -> None:
        if self._current_path is None:
            self._save_as_action_clicked()
        else:
            self.save_file(self._current_path)

    def _save_as_action_clicked(self) -> None:
        filter = QCoreApplication.translate("MainWindow", "Desktop Entries") + " (*.desktop);;" + QCoreApplication.translate("MainWindow", "All Files") + " (*)"
        path = QFileDialog.getSaveFileName(self, filter=filter)[0]

        if path != "":
            self.save_file(path)

    def _exit_action_clicked(self) -> None:
        if self._ask_for_save():
            sys.exit(0)

    # General

    def _browse_icon_button_clicked(self) -> None:
        filter = QCoreApplication.translate("MainWindow", "All Images") + " (*.png *.svg *xpm);;"
        filter += QCoreApplication.translate("MainWindow", "PNG Images") + " (*.png);;"
        filter += QCoreApplication.translate("MainWindow", "SVG Images") + " (*.svg);;"
        filter += QCoreApplication.translate("MainWindow", "XPM Images") + " (*.xpm);;"
        filter += QCoreApplication.translate("MainWindow", "All Files") + " (*)"

        path = QFileDialog.getOpenFileName(self, directory=os.path.expanduser("~"), filter=filter)[0]

        if path == "":
            return

        self.icon_edit.setText(get_real_path(path))

    def _browse_exec_button_clicked(self) -> None:
        path = QFileDialog.getOpenFileName(self, directory=os.path.expanduser("~"))[0]

        if path == "":
            return

        self.exec_edit.setText(get_real_path(path))

    def _browse_try_exec_button_clicked(self) -> None:
        path = QFileDialog.getOpenFileName(self, directory=os.path.expanduser("~"))[0]

        if path == "":
            return

        self.try_exec_edit.setText(get_real_path(path))

    def _browse_path_button_clicked(self) -> None:
        path = QFileDialog.getExistingDirectory(self, directory=os.path.expanduser("~"))

        if path == "":
            return

        self.path_edit.setText(get_real_path(path))

    # Categories

    def _update_categorie_remove_button_enabled(self) -> None:
        self.remove_categorie_button.setEnabled(self.categories_list.currentRow() != -1)

    def _add_categorie_button_clicked(self) -> None:
        categorie, ok = QInputDialog.getItem(self, QCoreApplication.translate("MainWindow", "Add a Categorie"), QCoreApplication.translate("MainWindow", "Please select a Categorie from the list below"), self._env.categories, 0, False)
        if not ok:
            return
        if list_widget_contains_item(self.categories_list, categorie):
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Categorie already added"), QCoreApplication.translate("MainWindow", "You can't add the same Categorie twice"))
        else:
            self.categories_list.addItem(categorie)
            self._update_categorie_remove_button_enabled()
            self.set_file_edited(True)

    def _remove_categorie_button_clicked(self) -> None:
        row = self.categories_list.currentRow()
        if row == -1:
            return
        self.categories_list.takeItem(row)
        self._update_categorie_remove_button_enabled()
        self.set_file_edited(True)

    # Keywords

    def _update_keywords_langauge_buttons_enabled(self) -> None:
        enabled = self.keywords_language_list.currentRow() != -1
        self.edit_keywords_language_button.setEnabled(enabled)
        self.remove_keywords_language_button.setEnabled(enabled)

    def _add_keywords_language_button_clicked(self) -> None:
        language = self._edit_keywords_translation_dialog.open_dialog(None)

        if language is None:
            return

        self.keywords_language_list.addItem(language)
        self._update_keywords_langauge_buttons_enabled()
        self.set_file_edited(True)

    def _edit_keywords_language_button_clicked(self) -> None:
        item = self.keywords_language_list.currentItem()
        langauge = self._edit_keywords_translation_dialog.open_dialog(item.text())
        if langauge:
            self.set_file_edited(True)
            item.setText(langauge)
        self._update_keywords_langauge_buttons_enabled()

    def _remove_keywords_button_clicked(self) -> None:
        item = self.keywords_language_list.currentItem()

        if QMessageBox.question(self, QCoreApplication.translate("MainWindow", "Delete Keywords translation"), QCoreApplication.translate("MainWindow", "Are you really want to delete {{language}}?").replace("{{language}}", item.text())) != QMessageBox.StandardButton.Yes:
            return

        self._edit_keywords_translation_dialog.delete_translation(item.text())

        self.keywords_language_list.takeItem(self.keywords_language_list.currentRow())
        self._update_keywords_langauge_buttons_enabled()
        self.set_file_edited(True)

    # Actions

    def _update_action_buttons_enabled(self) -> None:
        enabled = self.actions_list.currentRow() != -1
        self.edit_action_button.setEnabled(enabled)
        self.delete_action_button.setEnabled(enabled)

    def _add_action_button_clicked(self) -> None:
        identifier = QInputDialog.getText(self, QCoreApplication.translate("MainWindow", "Add Action"), QCoreApplication.translate("MainWindow", "Please enter the identifier for the new Action"))[0].strip()

        if identifier == "":
            return

        if not desktop_entry_lib.is_action_identifier_valid(identifier):
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Invalid Identifier"), QCoreApplication.translate("MainWindow", "This Identifier is not valid"))
            return

        if list_widget_contains_item(self.actions_list, identifier):
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Identifier exists"), QCoreApplication.translate("MainWindow", "This Identifier already exists"))
            return

        identifier, ok = self._edit_action_dialog.open_dialog(identifier)

        if not ok:
            return

        self.actions_list.addItem(identifier)

        self.set_file_edited(True)
        self._update_action_buttons_enabled()

    def _edit_action_button_clicked(self) -> None:
        item = self.actions_list.currentItem()
        identifier, ok = self._edit_action_dialog.open_dialog(item.text())
        if ok:
            self.set_file_edited(True)
            item.setText(identifier)
        self._update_action_buttons_enabled()

    def _delete_action_button_clicked(self) -> None:
        item = self.actions_list.currentItem()

        if QMessageBox.question(self, QCoreApplication.translate("MainWindow", "Delete Action"), QCoreApplication.translate("MainWindow", "Are you really want to delete {{identifier}}?").replace("{{identifier}}", item.text())) != QMessageBox.StandardButton.Yes:
            return

        self._edit_action_dialog.delete_action(item.text())

        self.actions_list.takeItem(self.actions_list.currentRow())
        self._update_action_buttons_enabled()
        self.set_file_edited(True)

    # Custom

    def _add_custom_row(self, key: Optional[str] = None, value: Optional[str] = None) -> None:
        row = self.custom_table.rowCount()
        self.custom_table.insertRow(row)

        key_item = QTableWidgetItem()
        if key is not None:
            key_item.setText(key)
        self.custom_table.setItem(row, 0, key_item)

        value_item = QTableWidgetItem()
        if value is not None:
            value_item.setText(value)
        self.custom_table.setItem(row, 1, value_item)

        remove_button = QPushButton(QCoreApplication.translate("MainWindow", "Remove"))
        remove_button.clicked.connect(self._remove_custom_clicked)
        self.custom_table.setCellWidget(row, 2, remove_button)

    def _remove_custom_clicked(self) -> None:
        row = get_sender_table_row(self.custom_table, 2, self.sender())
        self.custom_table.removeRow(row)
        self.set_file_edited(True)

    def _check_custom_button_clicked(self) -> None:
        valid = True

        for i in get_logical_table_row_list(self.custom_table):
            key = self.custom_table.item(i, 0).text()

            if key.strip() == "":
                continue

            if not desktop_entry_lib.is_custom_key_name_valid(key):
                QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Invalid Key"), QCoreApplication.translate("MainWindow", "{{key}} is not a valid custom Key").replace("{{key}}", key))
                valid = False

        if valid:
            QMessageBox.information(self, QCoreApplication.translate("MainWindow", "Everything valid"), QCoreApplication.translate("MainWindow", "No issues found"))

    # Functions

    def reset(self) -> None:
        self._load_desktop_enty(desktop_entry_lib.DesktopEntry())
        self._current_path = None

        self.set_file_edited(False)

    def open_file(self, path: str, ask: bool = False) -> None:
        if ask and not self._ask_for_save():
            return

        path = os.path.abspath(path)

        try:
            self._load_desktop_enty(desktop_entry_lib.DesktopEntry.from_file(path))
        except FileNotFoundError:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "File not found"), QCoreApplication.translate("MainWindow", "{{path}} was not found").replace("{{path}}", get_real_path(path)))
            return
        except Exception:
            print(traceback.format_exc(), end="", file=sys.stderr)
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Error loading Desktop Entry"), QCoreApplication.translate("MainWindow", "This Desktop Entry couldn't be loaded. Make sure, it is in the right format."))
            return

        self._env.add_recent_file(path)
        self._update_recent_files_menu()

        self._current_path = path
        self.set_file_edited(False)

        self.file_opened.emit(path)

    def open_url(self, url: str, ask: bool = False) -> None:
        if not check_optional_module("requests", self):
            return

        if ask and not self._ask_for_save():
            return

        r = get_requests_response(url)

        if r is None:
            return

        try:
            self._load_desktop_enty(desktop_entry_lib.DesktopEntry.from_string(r.text))
        except Exception:
            print(traceback.format_exc(), end="", file=sys.stderr)
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Error loading Desktop Entry"), QCoreApplication.translate("MainWindow", "This Desktop Entry couldn't be loaded. Make sure, it is in the right format."))
            return

        self._current_path = None
        self.set_file_edited(False)

    def _load_desktop_enty(self, entry: desktop_entry_lib.DesktopEntry) -> None:
        match entry.Type:
            case "Application":
                self.application_type_rad.setChecked(True)
            case "Link":
                self.link_type_rad.setChecked(True)
            case "Directory":
                self.directory_type_rad.setChecked(True)

        self._env.translate_dialog.clear()

        self.name_edit.setText(entry.Name.default_text)
        self._env.translate_dialog.set_translations("Name", entry.Name.translations)

        self.generic_name_edit.setText(entry.GenericName.default_text)
        self._env.translate_dialog.set_translations("GenericName", entry.GenericName.translations)

        self.comment_edit.setText(entry.Comment.default_text)
        self._env.translate_dialog.set_translations("Comment", entry.Comment.translations)

        self.icon_edit.setText(string_not_none(entry.Icon))
        self.exec_edit.setText(string_not_none(entry.Exec))
        self.try_exec_edit.setText(string_not_none(entry.TryExec))
        self.path_edit.setText(string_not_none(entry.Path))
        self.startup_wm_class_edit.setText(string_not_none(entry.StartupWMClass))
        self.url_edit.setText(string_not_none(entry.URL))

        self.no_display_checkbox.setChecked(boolean_not_none(entry.NoDisplay))
        self.hidden_checkbox.setChecked(boolean_not_none(entry.Hidden))
        self.dbus_activatable_checkbox.setChecked(boolean_not_none(entry.DBusActivatable))
        self.terminal_checkbox.setChecked(boolean_not_none(entry.Terminal))
        self.startup_notify_checkbox.setChecked(boolean_not_none(entry.StartupNotify))
        self.prefers_non_default_gpu_checkbox.setChecked(boolean_not_none(entry.PrefersNonDefaultGPU))
        self.single_main_window_checkbox.setChecked(boolean_not_none(entry.SingleMainWindow))

        self.categories_list.clear()
        for i in entry.Categories:
            self.categories_list.addItem(i)

        self.edit_mime_type_widget.set_list(entry.MimeType)

        self._edit_keywords_translation_dialog.clear()
        self.edit_untranslated_keywords_widget.set_list(entry.Keywords.default_list)
        for language, translation in entry.Keywords.translations.items():
            self._edit_keywords_translation_dialog.set_translation(language, translation)
            self.keywords_language_list.addItem(language)

        self._edit_action_dialog.clear()
        for key, value in entry.Actions.items():
            self._edit_action_dialog.load_desktop_action(key, value)
            self.actions_list.addItem(key)

        self.edit_implements_widget.set_list(entry.Implements)
        self.edit_only_show_in_widget.set_list(entry.OnlyShowIn)
        self.edit_not_show_in_widget.set_list(entry.NotShowIn)

        clear_table_widget(self.custom_table)
        for custom_key, custom_value in entry.CustomKeys.items():
            self._add_custom_row(key=custom_key, value=custom_value)

        self._current_entry = entry

    def _strip_spaces(self, string: str) -> str:
        if self._env.settings.get("stripSpaces"):
            return string.strip()
        else:
            return string

    def get_desktop_entry(self) -> desktop_entry_lib.DesktopEntry:
        entry = copy.deepcopy(self._current_entry)

        if self.application_type_rad.isChecked():
            entry.Type = "Application"
        elif self.link_type_rad.isChecked():
            entry.Type = "Link"
        elif self.directory_type_rad.isChecked():
            entry.Type = "Directory"

        entry.Name.default_text = self._strip_spaces(self.name_edit.text())
        entry.Name.translations = self._env.translate_dialog.get_translations("Name", self._env.settings.get("stripSpaces"))

        entry.GenericName.default_text = self._strip_spaces(self.generic_name_edit.text())
        entry.GenericName.translations = self._env.translate_dialog.get_translations("GenericName", self._env.settings.get("stripSpaces"))

        entry.Comment.default_text = self._strip_spaces(self.comment_edit.text())
        entry.Comment.translations = self._env.translate_dialog.get_translations("Comment", self._env.settings.get("stripSpaces"))

        entry.Icon = none_if_empty_string(self.icon_edit.text(), self._env.settings.get("stripSpaces"))
        entry.Exec = none_if_empty_string(self.exec_edit.text(), self._env.settings.get("stripSpaces"))
        entry.TryExec = none_if_empty_string(self.try_exec_edit.text(), self._env.settings.get("stripSpaces"))
        entry.Path = none_if_empty_string(self.path_edit.text(), self._env.settings.get("stripSpaces"))
        entry.StartupWMClass = none_if_empty_string(self.startup_wm_class_edit.text(), self._env.settings.get("stripSpaces"))
        entry.URL = none_if_empty_string(self.url_edit.text(), self._env.settings.get("stripSpaces"))

        entry.NoDisplay = none_if_false(self.no_display_checkbox.isChecked())
        entry.Hidden = none_if_false(self.hidden_checkbox.isChecked())
        entry.DBusActivatable = none_if_false(self.dbus_activatable_checkbox.isChecked())
        entry.Terminal = none_if_false(self.terminal_checkbox.isChecked())
        entry.StartupNotify = none_if_false(self.startup_notify_checkbox.isChecked())
        entry.PrefersNonDefaultGPU = none_if_false(self.prefers_non_default_gpu_checkbox.isChecked())
        entry.SingleMainWindow = none_if_false(self.single_main_window_checkbox.isChecked())

        entry.Categories.clear()
        for i in range(self.categories_list.count()):
            entry.Categories.append(self._strip_spaces(self.categories_list.item(i).text()))

        entry.MimeType = self.edit_mime_type_widget.get_list(self._env.settings.get("stripSpaces"))

        entry.Keywords.clear()
        entry.Keywords.default_list = self.edit_untranslated_keywords_widget.get_list(self._env.settings.get("stripSpaces"))
        for i in range(self.keywords_language_list.count()):
            language = self._strip_spaces(self.keywords_language_list.item(i).text())
            entry.Keywords.translations[language] = self._edit_keywords_translation_dialog.get_translation(language, self._env.settings.get("stripSpaces"))

        entry.Actions.clear()
        for i in range(self.actions_list.count()):
            action_name = self._strip_spaces(self.actions_list.item(i).text())
            entry.Actions[action_name] = self._edit_action_dialog.get_desktop_action(action_name)

        entry.Implements = self.edit_implements_widget.get_list(self._env.settings.get("stripSpaces"))
        entry.OnlyShowIn = self.edit_only_show_in_widget.get_list(self._env.settings.get("stripSpaces"))
        entry.NotShowIn = self.edit_not_show_in_widget.get_list(self._env.settings.get("stripSpaces"))

        entry.CustomKeys.clear()
        for i in get_logical_table_row_list(self.custom_table):
            key = self.custom_table.item(i, 0).text()
            if desktop_entry_lib.is_custom_key_name_valid(key):
                entry.CustomKeys[key] = self._strip_spaces(self.custom_table.item(i, 1).text())

        if self._env.settings.get("addCommentSave"):
            entry.leading_comment = f"Created with jdDesktopEntryEdit {self._env.version}"

        return entry

    def save_file(self, path: str) -> None:
        self.get_desktop_entry().write_file(path)

        self._current_path = path

        self._env.add_recent_file(path)
        self._update_recent_files_menu()

        self.set_file_edited(False)

        self.file_saved.emit(path)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and len(event.mimeData().urls()) == 1:
            url = event.mimeData().urls()[0]

            if url.isLocalFile() or url.scheme() in ("http", "https"):
                event.accept()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if len(event.mimeData().urls()) != 1:
            return

        url = event.mimeData().urls()[0]

        if url.isLocalFile():
            self.open_file(url.toLocalFile(), ask=True)
        elif url.scheme() in ("http", "https"):
            self.open_url(url.toString(), ask=True)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._ask_for_save():
            event.accept()
        else:
            event.ignore()
