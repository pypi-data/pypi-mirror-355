from __future__ import annotations

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QWidget,
)

log = logging.getLogger(__name__)


class FEInfoWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__()
        self.parent = parent

        self.layout = QGridLayout()

        self.FE_CHIP_COMMON = "20UPGFC"
        self.inputtype = "NULL"

        label_title = QLabel()
        label_title.setText("Input FE chips Information")
        label_exp = QLabel()
        label_exp.setText(
            "input as ATLAS Serial Number or hex 0xBWWXY, B: batch number, WW: wafer number in batch, X: row, Y: col"
        )
        self.rb_hex = QRadioButton("Hex")
        self.rb_atlsn = QRadioButton("ATLAS Serial Number")

        self.rb_hex.toggled.connect(self.onClicked)
        self.rb_atlsn.toggled.connect(self.onClicked)

        label_chip1 = QLabel()
        label_chip1.setText("chip1:")
        label_chip2 = QLabel()
        label_chip2.setText("chip2:")
        label_chip3 = QLabel()
        label_chip3.setText("chip3:")
        label_chip4 = QLabel()
        label_chip4.setText("chip4:")

        self.edit_chip1 = QLineEdit()
        self.edit_chip2 = QLineEdit()
        self.edit_chip3 = QLineEdit()
        self.edit_chip4 = QLineEdit()

        button_quad = QPushButton("&quad reference")
        button_quad.clicked.connect(self.show_reference)

        button_next = QPushButton("&Assemble")
        button_next.clicked.connect(self.next_page)
        button_skip = QPushButton("&Skip")
        button_skip.clicked.connect(self.skip_page)
        button_back = QPushButton("&Back")
        button_back.clicked.connect(self.back_page)

        # self.img = QLabel(self)
        # pixmap = QPixmap("img/baremodule.jpg")
        # self.img.setPixmap(pixmap)

        self.layout.addWidget(label_title, 0, 0)
        self.layout.addWidget(label_exp, 1, 0, 1, 3)
        self.layout.addWidget(self.rb_hex, 2, 0)
        self.layout.addWidget(self.rb_atlsn, 3, 0)

        self.layout.addWidget(button_quad, 4, 2)

        self.layout.addWidget(label_chip1, 5, 0)
        self.layout.addWidget(self.edit_chip1, 5, 1)
        self.layout.addWidget(label_chip2, 6, 0)
        self.layout.addWidget(self.edit_chip2, 6, 1)
        self.layout.addWidget(label_chip3, 7, 0)
        self.layout.addWidget(self.edit_chip3, 7, 1)
        self.layout.addWidget(label_chip4, 8, 0)
        self.layout.addWidget(self.edit_chip4, 8, 1)

        self.layout.addWidget(button_next, 9, 2)
        self.layout.addWidget(button_skip, 9, 1)
        self.layout.addWidget(button_back, 9, 0)

        self.setLayout(self.layout)

    def show_reference(self):
        self.parent.refwindow = ReferenceWindow(self.parent)
        self.parent.refwindow.show()
        # self.layout.addWidget(self.img,5,2,4,1)

    def onClicked(self):
        radiobtn = self.sender()
        if radiobtn.isChecked():
            if radiobtn.text() == "Hex":
                self.inputtype = "hex"
            elif radiobtn.text() == "ATLAS Serial Number":
                self.inputtype = "atlsn"

    def next_page(self):
        if self.inputtype == "hex":
            try:
                chip1_decimal = int(self.edit_chip1.text(), 16)
                chip2_decimal = int(self.edit_chip2.text(), 16)
                chip3_decimal = int(self.edit_chip3.text(), 16)
                chip4_decimal = int(self.edit_chip4.text(), 16)

                str_chip1_decimal = self.add_zero(str(chip1_decimal))
                str_chip2_decimal = self.add_zero(str(chip2_decimal))
                str_chip3_decimal = self.add_zero(str(chip3_decimal))
                str_chip4_decimal = self.add_zero(str(chip4_decimal))

                chip1_str = self.FE_CHIP_COMMON + str_chip1_decimal
                chip2_str = self.FE_CHIP_COMMON + str_chip2_decimal
                chip3_str = self.FE_CHIP_COMMON + str_chip3_decimal
                chip4_str = self.FE_CHIP_COMMON + str_chip4_decimal

                self.parent.baremodule_info["child"]["FE_CHIP"].append(chip1_str)
                self.parent.baremodule_info["child"]["FE_CHIP"].append(chip2_str)
                self.parent.baremodule_info["child"]["FE_CHIP"].append(chip3_str)
                self.parent.baremodule_info["child"]["FE_CHIP"].append(chip4_str)
            except Exception:
                log.exception("no FE chips info!!")
        elif self.inputtype == "atlsn":
            self.check_and_assemble(self.edit_chip1.text())
            self.check_and_assemble(self.edit_chip2.text())
            self.check_and_assemble(self.edit_chip3.text())
            self.check_and_assemble(self.edit_chip4.text())
        else:
            QMessageBox.warning(
                None, "Warning", "Choose input style option", QMessageBox.Ok
            )

        self.parent.assemble_fechip()
        self.parent.sensorinfo()

    def check_and_assemble(self, fe_serial):
        if fe_serial != "":
            try:
                doc = self.parent.get_componentinfo(fe_serial)
            except Exception:
                QMessageBox.warning(
                    None, "Error", "Cannot get FE chip information", QMessageBox.Ok
                )
                return 1
            parents_list = doc["parents"]
            isAssembled = False
            if parents_list is not None:
                for parent in parents_list:
                    if (
                        parent["componentType"]["code"] == "BARE_MODULE"
                        and parent["history"][-1]["action"] == "assembly"
                    ):
                        isAssembled = True
                        QMessageBox.critical(
                            None,
                            "Error",
                            fe_serial + " is already assembled.",
                            QMessageBox.Ok,
                        )
                return None

            if not isAssembled:
                self.parent.baremodule_info["child"]["FE_CHIP"].append(fe_serial)
                return None
            return None
        return None

    def back_page(self):
        self.parent.bareregist()

    def skip_page(self):
        self.parent.sensorinfo()

    def add_zero(self, chip_str):
        while len(chip_str) < 7:
            chip_str = "0" + chip_str
        return chip_str


class ReferenceWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.refbox = QDialog(parent)
        self.parent = parent

        layout = QGridLayout()

        self.img = QLabel(self)
        # pixmap = QPixmap("img/baremodule.jpg")
        pixmap = QPixmap("img/assembledmodule.jpg")
        self.img.setPixmap(pixmap)

        layout.addWidget(self.img, 0, 0)
        self.refbox.setLayout(layout)

    def show(self):
        self.setWindowModality(Qt.NonModal)
        self.refbox.show()
