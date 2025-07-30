from PyQt6.QtCore import QUrl, pyqtClassInfo, pyqtSlot
from PyQt6.QtDBus import QDBusAbstractAdaptor
from PyQt6.QtWidgets import QApplication
from typing import TYPE_CHECKING
import os


if TYPE_CHECKING:
    from ..MainWindow import MainWindow


with open(os.path.join(os.path.dirname(__file__), "FreedesktopApplicationInterface.xml"), "r", encoding="utf-8") as f:
    interface = f.read()


@pyqtClassInfo("D-Bus Interface", "org.freedesktop.Application")
@pyqtClassInfo("D-Bus Introspection", interface)
class FreedesktopApplicationInterface(QDBusAbstractAdaptor):
    def __init__(self, app: QApplication, main_window: "MainWindow") -> None:
        super().__init__(app)

        self._main_window = main_window

    @pyqtSlot("QVariantMap")
    def Activate(self, platform_data: dict) -> None:
        pass

    @pyqtSlot("QStringList", "QVariantMap")
    def Open(self, uris: list[str], platform_data: dict) -> None:
        if len(uris) != 0:
            self._main_window.open_file(QUrl(uris[0]).toLocalFile())

    @pyqtSlot("QString", "QVariant", "QVariantMap")
    def ActivateAction(self, action_name: str, parameter: list, platform_data: dict) -> None:
        pass
