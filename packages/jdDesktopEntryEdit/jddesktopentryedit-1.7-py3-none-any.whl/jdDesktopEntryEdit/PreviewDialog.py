from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QIcon
from PyQt6.QtWidgets import QWidget, QDialog, QApplication, QStyle
from .ui_compiled.PreviewDialog import Ui_PreviewDialog
from typing import TYPE_CHECKING
import re


if TYPE_CHECKING:
    from .Environment import Environment


class DesktopEntryHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None) -> None:

        super(DesktopEntryHighlighter, self).__init__(parent)

        self._highlighting_rules: list[tuple[re.Pattern, QTextCharFormat]] = []

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("blue"))
        self._highlighting_rules.append((re.compile("^([A-z]|-)+(?==.)"), keywordFormat))

        sectionHeaderFormat = QTextCharFormat()
        sectionHeaderFormat.setForeground(QColor("darkorange"))
        self._highlighting_rules.append((re.compile(r"^\[.+\]"), sectionHeaderFormat))

        commentFormat = QTextCharFormat()
        commentFormat.setFontItalic(True)
        commentFormat.setForeground(QColor("green"))
        self._highlighting_rules.append((re.compile("#.*$"), commentFormat))

    def highlightBlock(self, text: str) -> None:
        for pattern, format in self._highlighting_rules:
            for i in pattern.finditer(text):
                self.setFormat(i.start(), i.end() - i.start(), format)


class PreviewDialog(Ui_PreviewDialog, QDialog):
    def __init__(self, parent: QWidget, env: "Environment") -> None:
        super().__init__(parent)

        self.setupUi(self)

        self._highlighter = DesktopEntryHighlighter(self.preview_edit.document())

        self.close_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)))

        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(self.preview_edit.toPlainText()))
        self.close_button.clicked.connect(self.close)

    def open_preview(self, text: str) -> None:
        self.preview_edit.setPlainText(text)
        self.exec()
