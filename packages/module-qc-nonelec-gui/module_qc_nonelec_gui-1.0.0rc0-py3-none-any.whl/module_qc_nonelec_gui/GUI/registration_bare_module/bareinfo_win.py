from __future__ import annotations

import logging

from PyQt5.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

log = logging.getLogger(__name__)


class BareInfoWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__()
        self.parent = parent

        layout = QGridLayout()

        label_title = QLabel()
        label_title.setText("Input Bare Module ATLAS Serial Number:")

        label_bare = QLabel()
        label_bare.setText("ATLAS Serial Number")

        self.edit_bare = QLineEdit()

        button_next = QPushButton("&Next")
        button_next.clicked.connect(self.next_page)
        button_back = QPushButton("&Back")
        button_back.clicked.connect(self.back_page)

        layout.addWidget(label_title, 0, 0)
        layout.addWidget(label_bare, 1, 0)
        layout.addWidget(self.edit_bare, 1, 1)
        layout.addWidget(button_back, 2, 0)
        layout.addWidget(button_next, 2, 1)

        self.setLayout(layout)

    def next_page(self):
        try:
            self.parent.get_bareinfo(self.edit_bare.text())
        except Exception:
            QMessageBox.warning(
                None, "Warning", "Cannot get bare module information", QMessageBox.Ok
            )
            self.parent.bareupdate()
        # log.info(self.parent.bare_doc)
        children_list = self.parent.bare_doc["children"]
        # isSensor = False
        # isFEChip = False
        for child in children_list:
            if (
                child["componentType"]["code"] == "FE_CHIP"
                and child["component"] is not None
            ):
                # isFEChip = True
                # msgBox = QMessageBox.warning(None, 'Warning',"FE chip is already assembled.", QMessageBox.Ok)
                QMessageBox.warning(
                    None,
                    "Warning",
                    "FE chip "
                    + child["component"]["serialNumber"]
                    + " is already assembled.",
                    QMessageBox.Ok,
                )
                log.info(child["component"])
            elif (
                child["componentType"]["code"] == "SENSOR_TILE"
                and child["component"] is not None
            ):
                # isSensor = True
                # msgBox = QMessageBox.warning(None, 'Warning',"Sensor tile is already assembled.", QMessageBox.Ok)
                QMessageBox.warning(
                    None,
                    "Warning",
                    "Sensor tile "
                    + child["component"]["serialNumber"]
                    + " is already assembled.",
                    QMessageBox.Ok,
                )
        self.parent.feinfo()

    def back_page(self):
        self.parent.choose_menu()
