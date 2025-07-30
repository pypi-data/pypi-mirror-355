from __future__ import annotations

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

# from PyQt5.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget
# from PyQt5.QtGUI import *
#

log = logging.getLogger(__name__)


class SummaryWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent

        self.setMinimumWidth(900)
        self.setMinimumHeight(400)

        # layout common
        label_text = QLabel()
        label_text.setText('<center><font size="6"> Inspection Summary</font></center>')

        # layout buttons
        buttons_widget = QWidget()
        layout_buttons = QHBoxLayout()
        button_back = QPushButton("Back")
        button_back.clicked.connect(self.parent.inspection)
        button_write = QPushButton("Checkout Inspection")
        button_write.clicked.connect(self.write_data)

        layout_buttons.addWidget(button_back)
        layout_buttons.addWidget(button_write)

        buttons_widget.setLayout(layout_buttons)

        # layout infotable in a scrollarea
        grid_layout = self.make_infotable()
        layout_infotable = QHBoxLayout()
        layout_infotable.addLayout(grid_layout)

        infotable_widgets = QWidget()
        infotable_widgets.setLayout(layout_infotable)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setWidget(infotable_widgets)

        # layout final
        layout = QVBoxLayout()
        layout.addWidget(label_text)
        layout.addWidget(scroll)
        layout.addWidget(buttons_widget)
        layout.setSpacing(5)
        layout.setContentsMargins(20, 20, 20, 20)

        self.setLayout(layout)

    def get_maximum(self, contents_dict):
        N_char = []
        for key in contents_dict:
            label = QLabel()
            label.setText(contents_dict[key])
            N_char.append(label.sizeHint().width())
        return max(N_char)

    def make_infotable(self):
        log.info(self.parent.parent.info_dict)
        contents = {
            "ATLAS Serial Number:": self.parent.parent.info_dict["component"],
            "Component Type:": self.parent.parent.info_dict["componentType"],
            "Current Stage:": self.parent.parent.info_dict["stage"],
        }

        for tile, anomaly in self.parent.anomaly_dic.items():
            if len(anomaly) == 0:
                continue

            contents.update({f"Defects Tile-{tile}": "\n".join(anomaly)})

        for tile, comment in self.parent.comment_dic.items():
            if len(comment) == 0:
                continue

            contents.update({f"Comment Tile-{tile}": comment})

        form_size = 600

        grid_layout = QGridLayout()
        self.add_infotable(
            grid_layout,
            "ATLAS Serial Number:",
            self.parent.parent.info_dict["component"],
            form_size,
            0,
        )
        self.add_infotable(
            grid_layout,
            "Component Type:",
            self.parent.parent.info_dict["componentType"],
            form_size,
            1,
        )
        self.add_infotable(
            grid_layout,
            "Current Stage:",
            self.parent.parent.info_dict["stage"],
            form_size,
            2,
        )

        nRow = 3

        for tile, anomaly in self.parent.anomaly_dic.items():
            if len(anomaly) == 0:
                continue

            self.add_infotable(
                grid_layout,
                f"Defects Tile-{tile}:",
                ",".join(anomaly),
                form_size,
                nRow,
            )
            nRow = nRow + 1

        for tile, comment in self.parent.comment_dic.items():
            if len(comment) == 0:
                continue

            self.add_infotable(
                grid_layout,
                f"Comments Tile-{tile}:",
                comment,
                form_size,
                nRow,
            )
            nRow = nRow + 1

        return grid_layout

    def add_infotable(self, grid_layout, label_str, info_str, form_size, i):
        label_text = QLabel()
        label_text.setText('<font size="4">' + label_str + "</font>")

        if label_str.find("Comments") == 0:
            info_text = QPlainTextEdit()
            info_text.setPlainText(info_str)
            info_text.setFixedHeight(100)
        else:
            info_text = QLineEdit()
            info_text.setText(info_str)
            info_text.setFixedHeight(label_text.sizeHint().height() + 3)
        info_text.setReadOnly(True)
        info_text.setFocusPolicy(Qt.NoFocus)
        info_text.setStyleSheet("background-color : linen; color: black;;")
        info_text.setFixedWidth(form_size)

        grid_layout.setSpacing(3)
        grid_layout.addWidget(label_text, i, 0)
        grid_layout.addWidget(info_text, i, 1)

    def write_data(self):
        self.parent.make_result()
