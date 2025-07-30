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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

log = logging.getLogger(__name__)


class ConfirmWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent

        self.setMinimumWidth(900)
        self.setMinimumHeight(400)

        layout = QVBoxLayout()

        label_text = QLabel()
        label_text.setText('<center><font size="6"> Submission Preview</font></center>')

        # layout buttons
        buttons_widget = QWidget()
        layout_buttons = QHBoxLayout()
        button_back = QPushButton("Back")
        button_back.clicked.connect(self.parent.back_to_test)
        button_check = QPushButton("Check JSON")
        button_check.clicked.connect(self.parent.confirm_json)
        button_write = QPushButton("Register to LocalDB")
        button_write.clicked.connect(self.parent.upload_to_db)

        layout_buttons.addWidget(button_back)
        layout_buttons.addWidget(button_check)
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
        log.info(self.parent.info_dict)
        contents = {
            "ATLAS Serial Number:": self.parent.info_dict["component"],
            "Component Type:": self.parent.info_dict["componentType"],
            "Current Stage:": self.parent.info_dict["stage"],
            "Test:": self.parent.info_dict["testType"],
            "TimeStart": int(self.parent.info_dict["date"].timestamp()),
        }

        if "front_defects" in self.parent.testRun["results"]["Metadata"]:
            for tile, defect in self.parent.testRun["results"]["Metadata"][
                "front_defects"
            ].items():
                if len(defect) == 0:
                    continue

                contents.update({f"Defects Tile-{tile}": "\n".join(defect)})

        if "front_comments" in self.parent.testRun["results"]["Metadata"]:
            for tile, comment in self.parent.testRun["results"]["Metadata"][
                "front_comments"
            ].items():
                if len(comment) == 0:
                    continue

                contents.update({f"Comment Tile-{tile}": comment})

        form_size = 600

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
            2,
        )
        self.add_infotable(
            grid_layout,
            "TimeStart:",
            self.parent.info_dict["date"].isoformat(),
            form_size,
            3,
        )

        nRow = 4

        # --------------------------------------------------------------------

        if "front_defects" in self.parent.testRun["results"]["Metadata"]:
            for tile, defect in self.parent.testRun["results"]["Metadata"][
                "front_defects"
            ].items():
                if len(defect) == 0:
                    continue

                self.add_infotable(
                    grid_layout,
                    f"Front-side Defects Tile-{tile}:",
                    ",".join(defect),
                    form_size,
                    nRow,
                )
                nRow = nRow + 1

        for tile, comment in self.parent.testRun["results"]["Metadata"][
            "front_comments"
        ].items():
            if len(comment) == 0:
                continue

            self.add_infotable(
                grid_layout,
                f"Front-side Comments Tile-{tile}:",
                comment,
                form_size,
                nRow,
            )
            nRow = nRow + 1

        if "back_defects" not in self.parent.testRun["results"]["Metadata"]:
            return grid_layout

        # --------------------------------------------------------------------

        for tile, defect in self.parent.testRun["results"]["Metadata"][
            "back_defects"
        ].items():
            if len(defect) == 0:
                continue

            self.add_infotable(
                grid_layout,
                f"Back-side Defects Tile-{tile}:",
                ",".join(defect),
                form_size,
                nRow,
            )
            nRow = nRow + 1

        for tile, comment in self.parent.testRun["results"]["Metadata"][
            "back_comments"
        ].items():
            if len(comment) == 0:
                continue

            self.add_infotable(
                grid_layout,
                f"Back-side Comments Tile-{tile}:",
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
        info_text.setStyleSheet("background-color : linen; color: black;")
        info_text.setFixedWidth(form_size)

        grid_layout.setSpacing(3)
        grid_layout.addWidget(label_text, i, 0)
        grid_layout.addWidget(info_text, i, 1)

    def add_info(self, Form_layout, label_str, form_text):
        label = QLabel()
        label.setText(label_str)

        if label_str == "Comment :":
            inner = QTextEdit()
            inner.setText(form_text)
            inner.setReadOnly(True)
            inner.setFocusPolicy(Qt.NoFocus)
            inner.setStyleSheet("background-color : linen; color: black;")

            editor = QScrollArea()
            editor.setWidgetResizable(True)
            editor.setWidget(inner)

        else:
            editor = QLineEdit()
            editor.setText(form_text)
            editor.setReadOnly(True)
            editor.setFocusPolicy(Qt.NoFocus)
            editor.setStyleSheet("background-color : linen; color: black;")
        #        editor.setStyleSheet("background-color : azure")

        Form_layout.addRow(label, editor)
