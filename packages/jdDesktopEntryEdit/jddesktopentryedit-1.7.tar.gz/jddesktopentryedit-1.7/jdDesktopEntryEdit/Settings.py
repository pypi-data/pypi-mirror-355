from typing import Any
import json
import os


class Settings():
    def __init__(self) -> None:
        self._default_settings = {
            "language": "default",
            "recentFilesLength": 10,
            "windowTitleType": "filename",
            "checkSaveBeforeClosing": True,
            "showEditedTitle": True,
            "addCommentSave": True,
            "stripSpaces": True,
            "showWelcomeDialog": True
        }

        self._user_settings = {}

    def get(self, key: str) -> Any:
        """Returns the given setting"""
        if key in self._user_settings:
            return self._user_settings[key]
        elif key in self._default_settings:
            return self._default_settings[key]
        else:
            return None

    def set(self, key: str, value: Any) -> None:
        """Set the value of a setting"""
        self._user_settings[key] = value

    def save(self, path: str) -> None:
        """Save settings into file"""
        if len(self._user_settings) == 0 and not os.path.isfile(path):
            return

        try:
            os.makedirs(os.path.dirname(path))
        except FileExistsError:
            pass

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._user_settings, f, ensure_ascii=False, indent=4)

    def load(self, path: str) -> None:
        """Load settings from file"""
        if not os.path.isfile(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            self._user_settings = json.load(f)

    def reset(self) -> None:
        """Resets all settings to the default values"""
        self._user_settings.clear()
