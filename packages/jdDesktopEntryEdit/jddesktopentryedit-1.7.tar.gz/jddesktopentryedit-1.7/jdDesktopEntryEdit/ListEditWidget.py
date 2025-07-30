from PyQt6.QtWidgets import QWidget, QLabel, QListWidget, QPushButton, QHBoxLayout, QVBoxLayout, QInputDialog, QMessageBox, QAbstractItemView
from .Functions import list_widget_contains_item
from PyQt6.QtCore import Qt, QCoreApplication
from typing import Optional, TYPE_CHECKING
from PyQt6.QtGui import QIcon


if TYPE_CHECKING:
    from .MainWindow import MainWindow


class ListEditWidget(QWidget):
    def __init__(self, main_window: Optional["MainWindow"], label_text: str) -> None:
        super().__init__()

        self._main_window = main_window

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._list_widget = QListWidget()

        add_button = QPushButton(QCoreApplication.translate("ListEditWidget", "Add"))
        self._edit_button = QPushButton(QCoreApplication.translate("ListEditWidget", "Edit"))
        self._remove_button = QPushButton(QCoreApplication.translate("ListEditWidget", "Remove"))

        self._list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        add_button.setIcon(QIcon.fromTheme("list-add"))
        self._edit_button.setIcon(QIcon.fromTheme("document-edit"))
        self._remove_button.setIcon(QIcon.fromTheme("list-remove"))

        self._list_widget.itemSelectionChanged.connect(self._update_buttons_enabled)

        add_button.clicked.connect(self._add_button_clicked)
        self._edit_button.clicked.connect(self._edit_button_clicked)
        self._remove_button.clicked.connect(self._remove_button_clicked)

        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(self._edit_button)
        button_layout.addWidget(self._remove_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(label)
        main_layout.addWidget(self._list_widget)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self._update_buttons_enabled()

    def _update_buttons_enabled(self) -> None:
        enabled = self._list_widget.currentRow() != -1
        self._edit_button.setEnabled(enabled)
        self._remove_button.setEnabled(enabled)

    def _add_button_clicked(self) -> None:
        item = QInputDialog.getText(self, QCoreApplication.translate("ListEditWidget", "Add Item"), QCoreApplication.translate("ListEditWidget", "Please enter a new Item"))[0]

        if item == "":
            return

        if list_widget_contains_item(self._list_widget, item):
            QMessageBox.critical(QCoreApplication.translate("ListEditWidget", "Item in List"), QCoreApplication.translate("ListEditWidget", "This Item is already in the List"))
            return

        self._list_widget.addItem(item)
        self._update_buttons_enabled()

        if self._main_window is not None:
            self._main_window.set_file_edited(True)

    def _edit_button_clicked(self) -> None:
        old_item = self._list_widget.currentItem().text()

        new_item = QInputDialog.getText(self, QCoreApplication.translate("ListEditWidget", "Edit Item"), QCoreApplication.translate("ListEditWidget", "Please edit the Item"), text=old_item)[0].strip()

        if new_item == "" or new_item == old_item:
            return

        if list_widget_contains_item(self._list_widget, new_item):
            QMessageBox.critical(QCoreApplication.translate("ListEditWidget", "Item in List"), QCoreApplication.translate("ListEditWidget", "This Item is already in the List"))
            return

        self._list_widget.currentItem().setText(new_item)
        self._update_buttons_enabled()

        if self._main_window is not None:
            self._main_window.set_file_edited(True)

    def _remove_button_clicked(self) -> None:
        row = self._list_widget.currentRow()

        if row == -1:
            return

        self._list_widget.takeItem(row)
        self._update_buttons_enabled()

        if self._main_window is not None:
            self._main_window.set_file_edited(True)

    def set_list(self, item_list: list[str]) -> None:
        self._list_widget.clear()
        for i in item_list:
            self._list_widget.addItem(i)

    def get_list(self, strip_spaces: bool) -> list[str]:
        item_list = []
        for i in range(self._list_widget.count()):
            if strip_spaces:
                item_list.append(self._list_widget.item(i).text().strip())
            else:
                item_list.append(self._list_widget.item(i).text())
        return item_list

    def clear(self) -> None:
        self._list_widget.clear()
