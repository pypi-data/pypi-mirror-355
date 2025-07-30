from PyQt6.QtCore import pyqtClassInfo, pyqtSlot, pyqtProperty, pyqtSignal
from PyQt6.QtDBus import QDBusAbstractAdaptor
from PyQt6.QtWidgets import QApplication
from typing import TYPE_CHECKING
import os


if TYPE_CHECKING:
    from ..Environment import Environment
    from ..MainWindow import MainWindow


with open(os.path.join(os.path.dirname(__file__), "jdDesktopEntryEditInterface.xml"), "r", encoding="utf-8") as f:
    interface = f.read()


@pyqtClassInfo("D-Bus Interface", "page.codeberg.JakobDev.jdDesktopEntryEdit")
@pyqtClassInfo("D-Bus Introspection", interface)
class jdDesktopEntryEditInterface(QDBusAbstractAdaptor):
    FileOpened = pyqtSignal("QString")
    FileSaved = pyqtSignal("QString")

    def __init__(self, parent: QApplication, env: "Environment", main_window: "MainWindow") -> None:
        super().__init__(parent)

        self._env = env
        self._main_window = main_window

        main_window.file_opened.connect(lambda path: self.FileOpened.emit(path))
        main_window.file_saved.connect(lambda path: self.FileSaved.emit(path))

    @pyqtSlot(str)
    def OpenFile(self, path: str) -> None:
        self._main_window.open_file(path)

    @pyqtSlot(str)
    def SaveFile(self, path: str) -> None:
        self._main_window.save_file(path)

    @pyqtSlot(result=str)
    def GetDesktopEntry(self) -> None:
        return self._main_window.get_desktop_entry().get_text()

    @pyqtSlot()
    def Reset(self) -> None:
        self._main_window.reset()

    @pyqtSlot()
    def Quit(self) -> None:
        QApplication.quit()

    @pyqtProperty(str)
    def Name(self) -> str:
        return self._main_window.name_edit.text()

    @Name.setter
    def Name(self, name: str) -> None:
        self._main_window.name_edit.setText(name)
        self._main_window.set_file_edited(True)

    @pyqtProperty(str)
    def GenericName(self) -> str:
        return self._main_window.generic_name_edit.text()

    @GenericName.setter
    def GenericName(self, name: str) -> None:
        self._main_window.generic_name_edit.setText(name)
        self._main_window.set_file_edited(True)

    @pyqtProperty(str)
    def Comment(self) -> str:
        return self._main_window.comment_edit.text()

    @Comment.setter
    def Comment(self, comment: str) -> None:
        self._main_window.comment_edit.setText(comment)
        self._main_window.set_file_edited(True)

    @pyqtProperty(str)
    def Icon(self) -> str:
        return self._main_window.icon_edit.text()

    @Icon.setter
    def Icon(self, icon: str) -> None:
        self._main_window.icon_edit.setText(icon)
        self._main_window.set_file_edited(True)

    @pyqtProperty(str)
    def Exec(self) -> str:
        return self._main_window.exec_edit.text()

    @Exec.setter
    def Exec(self, exec: str) -> None:
        self._main_window.exec_edit.setText(exec)
        self._main_window.set_file_edited(True)

    @pyqtProperty(str)
    def TryExec(self) -> str:
        return self._main_window.try_exec_edit.text()

    @TryExec.setter
    def TryExec(self, exec: str) -> None:
        self._main_window.try_exec_edit.setText(exec)
        self._main_window.set_file_edited(True)

    @pyqtProperty(str)
    def Path(self) -> str:
        return self._main_window.path_edit.text()

    @Path.setter
    def Path(self, path: str) -> None:
        self._main_window.path_edit.setText(path)
        self._main_window.set_file_edited(True)

    @pyqtProperty(str)
    def StartupWMClass(self) -> str:
        return self._main_window.startup_wm_class_edit.text()

    @StartupWMClass.setter
    def StartupWMClass(self, wm_class: str) -> None:
        self._main_window.startup_wm_class_edit.setText(wm_class)
        self._main_window.set_file_edited(True)

    @pyqtProperty(str)
    def URL(self) -> str:
        return self._main_window.url_edit.text()

    @URL.setter
    def URL(self, url: str) -> None:
        self._main_window.url_edit.setText(url)
        self._main_window.set_file_edited(True)

    @pyqtProperty(bool)
    def NoDisplay(self) -> bool:
        return self._main_window.no_display_checkbox.isChecked()

    @NoDisplay.setter
    def NoDisplay(self, value: bool) -> None:
        self._main_window.no_display_checkbox.setChecked(value)
        self._main_window.set_file_edited(True)

    @pyqtProperty(bool)
    def Hidden(self) -> bool:
        return self._main_window.hidden_checkbox.isChecked()

    @Hidden.setter
    def Hidden(self, value: bool) -> None:
        self._main_window.hidden_checkbox.setChecked(value)
        self._main_window.set_file_edited(True)

    @pyqtProperty(bool)
    def DBusActivatable(self) -> bool:
        return self._main_window.dbus_activatable_checkbox.isChecked()

    @DBusActivatable.setter
    def DBusActivatable(self, value: bool) -> None:
        self._main_window.dbus_activatable_checkbox.setChecked(value)
        self._main_window.set_file_edited(True)

    @pyqtProperty(bool)
    def Terminal(self) -> bool:
        return self._main_window.terminal_checkbox.isChecked()

    @Terminal.setter
    def Terminal(self, value: bool) -> None:
        self._main_window.terminal_checkbox.setChecked(value)
        self._main_window.set_file_edited(True)

    @pyqtProperty(bool)
    def StartupNotify(self) -> bool:
        return self._main_window.startup_notify_checkbox.isChecked()

    @StartupNotify.setter
    def StartupNotify(self, value: bool) -> None:
        self._main_window.startup_notify_checkbox.setChecked(value)
        self._main_window.set_file_edited(True)

    @pyqtProperty(bool)
    def PrefersNonDefaultGPU(self) -> bool:
        return self._main_window.prefers_non_default_gpu_checkbox.isChecked()

    @PrefersNonDefaultGPU.setter
    def PrefersNonDefaultGPU(self, value: bool) -> None:
        self._main_window.prefers_non_default_gpu_checkbox.setChecked(value)
        self._main_window.set_file_edited(True)

    @pyqtProperty(bool)
    def SingleMainWindow(self) -> bool:
        return self._main_window.prefers_non_default_gpu_checkbox.isChecked()

    @SingleMainWindow.setter
    def SingleMainWindow(self, value: bool) -> None:
        self._main_window.single_main_window_checkbox.setChecked(value)
        self._main_window.set_file_edited(True)

    @pyqtProperty("QStringList")
    def Categories(self) -> list[str]:
        category_list: list[str] = []
        for count in range(self._main_window.categories_list.count()):
            category_list.append(self._main_window.categories_list.item(count).text())
        return category_list

    @Categories.setter
    def Categories(self, category_list: list[str]) -> None:
        self._main_window.categories_list.clear()
        for category in category_list:
            self._main_window.categories_list.addItem(category)

    @pyqtProperty("QStringList")
    def MimeType(self) -> list[str]:
        return self._main_window.edit_mime_type_widget.get_list(False)

    @MimeType.setter
    def MimeType(self, mime_list: list[str]) -> None:
        return self._main_window.edit_mime_type_widget.set_list(mime_list)

    @pyqtProperty("QStringList")
    def Keywords(self) -> list[str]:
        return self._main_window.edit_untranslated_keywords_widget.get_list(False)

    @Keywords.setter
    def Keywords(self, keywords: list[str]) -> None:
        return self._main_window.edit_untranslated_keywords_widget.set_list(keywords)

    @pyqtProperty("QStringList")
    def Implements(self) -> list[str]:
        return self._main_window.edit_implements_widget.get_list(False)

    @Implements.setter
    def Implements(self, implements_list: list[str]) -> None:
        return self._main_window.edit_implements_widget.set_list(implements_list)

    @pyqtProperty("QStringList")
    def OnlyShowIn(self) -> list[str]:
        return self._main_window.edit_only_show_in_widget.get_list(False)

    @OnlyShowIn.setter
    def OnlyShowIn(self, only_show_in_list: list[str]) -> None:
        return self._main_window.edit_only_show_in_widget.set_list(only_show_in_list)

    @pyqtProperty("QStringList")
    def NotShowIn(self) -> list[str]:
        return self._main_window.edit_not_show_in_widget.get_list(False)

    @NotShowIn.setter
    def NotShowIn(self, not_show_in_list: list[str]) -> None:
        return self._main_window.edit_not_show_in_widget.set_list(not_show_in_list)

    @pyqtProperty(str)
    def Version(self) -> str:
        return self._env.version
