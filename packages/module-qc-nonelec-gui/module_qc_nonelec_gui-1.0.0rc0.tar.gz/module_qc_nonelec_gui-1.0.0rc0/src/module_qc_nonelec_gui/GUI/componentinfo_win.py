from __future__ import annotations

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

log = logging.getLogger(__name__)


class ComponentInfoWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent

        layout = QVBoxLayout()

        label_text = QLabel()
        label_text.setText(
            '<center><font size="5">Component Information</font></center>'
        )

        Next_button = QPushButton("&Next")
        Next_button.clicked.connect(self.go_to_qc)
        Back_button = QPushButton("&Back")
        Back_button.clicked.connect(self.back_page)

        layout.addWidget(label_text)

        grid_layout = self.make_infotable()
        hbox = QHBoxLayout()
        hbox.addLayout(grid_layout)

        layout.addStretch()
        layout.addLayout(hbox)
        layout.addStretch()
        self.add_button(layout, Back_button, Next_button)
        self.setLayout(layout)

    def add_button(self, vlayout, back_button, next_button):
        hbox = QHBoxLayout()

        hbox.addWidget(back_button)
        hbox.addStretch()
        hbox.addWidget(next_button)

        vlayout.addLayout(hbox)

    def add_infotable(self, grid_layout, label_str, info_str, form_size, i):
        label_text = QLabel()
        label_text.setText('<font size="4">' + label_str + "</font>")

        info_text = QLineEdit()
        info_text.setText(info_str)
        info_text.setReadOnly(True)
        info_text.setFocusPolicy(Qt.NoFocus)
        info_text.setStyleSheet("background-color : linen;")
        info_text.setFixedHeight(label_text.sizeHint().height() + 3)
        info_text.setFixedWidth(form_size)

        grid_layout.setSpacing(3)
        grid_layout.addWidget(label_text, i, 0)
        grid_layout.addWidget(info_text, i, 1)

    def get_maximum(self, contents_dict):
        N_char = []
        for key in contents_dict:
            label = QLabel()
            label.setText(contents_dict[key])
            N_char.append(label.sizeHint().width())
        return max(N_char)

    def make_infotable(self):
        log.info(self.parent.info_dict)
        contents = {
            "ATLAS Serial Number:": self.parent.info_dict["component"],
            "Component Type:": self.parent.info_dict["componentType"],
            "Current Stage:": self.parent.info_dict["stage"],
        }

        form_size = max([170, self.get_maximum(contents) + 10])

        grid_layout = QGridLayout()
        self.add_infotable(
            grid_layout,
            "ATLAS Serial Number:",
            self.parent.info_dict["component"],
            form_size,
            0,
        )
        self.add_infotable(
            grid_layout,
            "Component Type:",
            self.parent.info_dict["componentType"],
            form_size,
            1,
        )
        self.add_infotable(
            grid_layout,
            "Current Stage:",
            self.parent.info_dict["stage"],
            form_size,
            5,
        )

        return grid_layout

    def go_to_qc(self):
        self.parent.moduleQC_choose_test()

    def back_page(self):
        self.parent.back_from_componentinfo()
