from .Functions import read_json_file, remove_duplicates_from_list
from .TranslateDialog import TranslateDialog
from PyQt6.QtWidgets import QApplication
from .Settings import Settings
from PyQt6.QtGui import QIcon
import platform
import pathlib
import json
import os


class Environment:
    def __init__(self, app: QApplication) -> None:
        self.program_dir = os.path.dirname(__file__)
        self.data_dir = self._get_data_path()
        self.app = app

        with open(os.path.join(self.program_dir, "version.txt"), "r", encoding="utf-8") as f:
            self.version = f.read().strip()

        self.icon = QIcon(os.path.join(self.program_dir, "Icon.svg"))

        self.settings = Settings()
        self.settings.load(os.path.join(self.data_dir, "settings.json"))

        self.recent_files: list[str] = read_json_file(os.path.join(self.data_dir, "recentfiles.json"), [])

        self.categories: list[str] = []
        with open(os.path.join(self.program_dir, "data", "categories.txt"), "r", encoding="utf-8") as f:
            for i in f.read().splitlines():
                if i.strip() != "":
                    self.categories.append(i.strip())

        self.template_list: list[str] = []
        self.update_template_list()

        self.translate_dialog = TranslateDialog()

    def _get_data_path(self) -> str:
        if platform.system() == "Windows":
            return os.path.join(os.getenv("APPDATA"), "jdDesktopEntryEdit")
        elif platform.system() == "Darwin":
            return os.path.join(str(pathlib.Path.home()), "Library", "Application Support", "jdDesktopEntryEdit")
        elif platform.system() == "Haiku":
            return os.path.join(str(pathlib.Path.home()), "config", "settings", "jdDesktopEntryEdit")
        else:
            if os.getenv("XDG_DATA_HOME"):
                return os.path.join(os.getenv("XDG_DATA_HOME"), "jdDesktopEntryEdit")
            else:
                return os.path.join(str(pathlib.Path.home()), ".local", "share", "jdDesktopEntryEdit")

    def add_recent_file(self, path: str) -> None:
        self.recent_files: list[str] = read_json_file(os.path.join(self.data_dir, "recentfiles.json"), [])
        self.recent_files.insert(0, path)
        self.save_recent_files()

    def save_recent_files(self) -> None:
        self.recent_files = remove_duplicates_from_list(self.recent_files)[:self.settings.get("recentFilesLength")]

        try:
            os.makedirs(self.data_dir)
        except FileExistsError:
            pass

        with open(os.path.join(self.data_dir, "recentfiles.json"), "w", encoding="utf-8") as f:
            json.dump(self.recent_files, f, ensure_ascii=False, indent=4)

    def clear_recent_files(self) -> None:
        if os.path.isfile(os.path.join(self.data_dir, "recentfiles.json")):
            os.remove(os.path.join(self.data_dir, "recentfiles.json"))

        self.recent_files.clear()

    def update_template_list(self) -> None:
        self.template_list.clear()

        if not os.path.isdir(os.path.join(self.data_dir, "templates")):
            return

        for i in os.listdir(os.path.join(self.data_dir, "templates")):
            if i.endswith(".desktop"):
                self.template_list.append(i.removesuffix(".desktop"))
