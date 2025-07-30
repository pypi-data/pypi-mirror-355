from PyQt6.QtCore import QTranslator, QLibraryInfo, QLocale
from PyQt6.QtDBus import QDBusConnection
from PyQt6.QtWidgets import QApplication
from .Environment import Environment
from .MainWindow import MainWindow
import argparse
import sys
import os


def main() -> None:
    if not os.path.isdir(os.path.join(os.path.dirname(__file__), "ui_compiled")):
        print("Could not find compiled ui files. Please run tools/CompileUI.py first.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", help="The path to a file")
    args = parser.parse_known_args()[0]

    app = QApplication(sys.argv)

    env = Environment(app)

    app.setDesktopFileName("page.codeberg.JakobDev.jdDesktopEntryEdit")
    app.setApplicationName("jdDesktopEntryEdit")
    app.setApplicationVersion(env.version)
    app.setWindowIcon(env.icon)

    app_translator = QTranslator()
    qt_translator = QTranslator()
    app_trans_dir = os.path.join(env.program_dir, "translations")
    qt_trans_dir = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    language = env.settings.get("language")
    if language == "default":
        system_language = QLocale.system().name()
        app_translator.load(os.path.join(app_trans_dir, "jdDesktopEntryEdit_" + system_language.split("_")[0] + ".qm"))
        app_translator.load(os.path.join(app_trans_dir, "jdDesktopEntryEdit_" + system_language + ".qm"))
        qt_translator.load(os.path.join(qt_trans_dir, "qt_" + system_language.split("_")[0] + ".qm"))
        qt_translator.load(os.path.join(qt_trans_dir, "qt_" + system_language + ".qm"))
    elif language == "en":
        pass
    else:
        app_translator.load(os.path.join(app_trans_dir, "jdDesktopEntryEdit_" + language + ".qm"))
        qt_translator.load(os.path.join(qt_trans_dir, "qt_" + language.split("_")[0] + ".qm"))
        qt_translator.load(os.path.join(qt_trans_dir, "qt_" + language + ".qm"))
    app.installTranslator(app_translator)
    app.installTranslator(qt_translator)

    main_window = MainWindow(env)
    main_window.show()
    main_window.startup()

    if args.file:
        main_window.open_file(os.path.abspath(args.file))

    conn = QDBusConnection.sessionBus()
    if conn.isConnected():
        if conn.registerService("page.codeberg.JakobDev.jdDesktopEntryEdit"):
            from .dbus.FreedesktopApplicationInterface import FreedesktopApplicationInterface
            from .dbus.jdDesktopEntryEditInterface import jdDesktopEntryEditInterface

            jdDesktopEntryEditInterface(app, env, main_window)
            FreedesktopApplicationInterface(app, main_window)

            conn.registerObject("/page/codeberg/JakobDev/jdDesktopEntryEdit", app)
        else:
            print(conn.lastError().message(), file=sys.stderr)

    sys.exit(app.exec())
