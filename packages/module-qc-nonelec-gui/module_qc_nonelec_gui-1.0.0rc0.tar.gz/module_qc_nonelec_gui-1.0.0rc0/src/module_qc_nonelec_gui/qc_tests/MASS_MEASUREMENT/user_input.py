from __future__ import annotations

import logging
import traceback

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

log = logging.getLogger(__name__)


class InitialWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent

        layout = QVBoxLayout()
        bottom_box = QHBoxLayout()
        grid_edit = QGridLayout()

        label_title = QLabel()
        label_title.setText('<center><font size="7">Input mass value</font></center>')

        Next_button = QPushButton("&Next")
        Next_button.clicked.connect(self.pass_result)
        Back_button = QPushButton("&Back")
        Back_button.clicked.connect(self.back_page)

        bottom_box.addWidget(Back_button)
        bottom_box.addStretch()
        bottom_box.addWidget(Next_button)

        label_text = QLabel()
        label_text.setText("Total weight : ")
        label_acu = QLabel()
        label_acu.setText("Scale Accuracy : ")
        label_unit = QLabel()
        label_unit.setText(self.parent.result_info["mass_unit"])
        label_acu_unit = QLabel()
        label_acu_unit.setText(self.parent.result_info["Scale_accuracy_unit"])
        label_comment = QLabel()
        label_comment.setText("comment : ")

        self.edit_comment = QTextEdit()
        self.edit_comment.setText(self.parent.result_info["comment"])
        self.edit_mass = QLineEdit()
        self.edit_mass.setAlignment(Qt.AlignRight)
        self.edit_mass.setValidator(QDoubleValidator())
        self.edit_mass.setFixedWidth(100)
        self.edit_mass.setMaxLength(8)
        if self.parent.result_info["mass_value"] != "":
            self.edit_mass.setText(self.parent.result_info["mass_value"])
        else:
            self.edit_mass.setText("")

        self.edit_acu = QLineEdit()
        self.edit_acu.setAlignment(Qt.AlignRight)
        self.edit_acu.setValidator(QDoubleValidator())
        self.edit_acu.setFixedWidth(100)
        self.edit_acu.setMaxLength(8)
        if self.parent.result_info["Scale_accuracy_value"] != "":
            self.edit_mass.setText(self.parent.result_info["Scale_accuracy_value"])
        else:
            self.edit_mass.setText("")

        grid_edit.addWidget(label_text, 0, 0)
        grid_edit.addWidget(self.edit_mass, 0, 1, Qt.AlignRight)
        grid_edit.addWidget(label_unit, 0, 2)

        grid_edit.addWidget(label_acu, 1, 0)
        grid_edit.addWidget(self.edit_acu, 1, 1, Qt.AlignRight)
        grid_edit.addWidget(label_acu_unit, 1, 2)

        grid_edit.addWidget(label_comment, 2, 0)

        outer = QScrollArea()
        outer.setWidgetResizable(True)
        outer.setWidget(self.edit_comment)
        grid_edit.addWidget(outer, 2, 1)

        layout.addWidget(label_title)
        layout.addStretch()
        layout.addLayout(grid_edit)
        layout.addLayout(bottom_box)

        self.setLayout(layout)

    def pass_result(self):
        try:
            mass_value = self.edit_mass.text()
            acu_value = self.edit_acu.text()
            free_comment = self.edit_comment.toPlainText()
        except Exception:
            log.exception(traceback.format_exc())
            QMessageBox.warning(
                None, "Warning", "Please input target weight.", QMessageBox.Ok
            )

        if self.validator(mass_value) == 0:
            QMessageBox.warning(
                None, "Warning", "Please input target weight.", QMessageBox.Ok
            )
        if self.validator(acu_value) == 0:
            QMessageBox.warning(
                None, "Warning", "Please input scale accuracy.", QMessageBox.Ok
            )
        if (self.validator(mass_value) == -1) or (self.validator(acu_value) == -1):
            valid_msg = QMessageBox.warning(
                None, "Warning", "Negative value is not supported", QMessageBox.Ok
            )
        elif (self.validator(mass_value) == -2) or (self.validator(acu_value) == -2):
            valid_msg = QMessageBox.warning(
                None,
                "Warning",
                "your input looks too large. Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if valid_msg == QMessageBox.Yes:
                self.parent.receive_mass(mass_value, acu_value, free_comment)  # changed
            elif valid_msg == QMessageBox.No:
                pass
        elif (self.validator(mass_value) == 1) and (self.validator(acu_value) == 1):
            self.parent.receive_mass(mass_value, acu_value, free_comment)

    def back_page(self):
        self.parent.close_and_return()

    def validator(self, number_text):
        mode = 0

        try:
            float_number = float(number_text)
        except Exception:
            return mode

        if float_number < 0:
            mode = -1
        elif float_number > 10000:
            mode = -2
        else:
            mode = 1

        return mode
