from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ConfirmWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent

        titlebox = QVBoxLayout()
        layout = QVBoxLayout()
        button_box = QHBoxLayout()
        inner_box = QVBoxLayout()
        image_box = QVBoxLayout()

        label_title = QLabel()
        label_title.setText(
            '<center><font size="5">Confirm before uploading to the database</font></center>'
        )
        label_practice = QLabel()
        label_practice.setText(
            '<center><font size="4" color = "green"> Practice Mode</font></center>'
        )

        Upload_button = QPushButton("&Upload!")
        Upload_button.clicked.connect(self.upload_to_db)
        json_button = QPushButton("&Check json (for expert)")
        json_button.clicked.connect(self.check_json)
        back_button = QPushButton("&Back")
        back_button.clicked.connect(self.back_page)

        titlebox.addWidget(label_title)

        button_box.addWidget(back_button)
        button_box.addStretch()
        button_box.addWidget(json_button)
        button_box.addWidget(Upload_button)

        inner = QScrollArea()
        inner.setFixedWidth(600)
        inner.setFixedHeight(400)
        result_wid = QWidget()
        result_wid.setLayout(self.layout_ModuleQC())

        inner.setWidgetResizable(True)
        inner.setWidget(result_wid)
        inner_box.addWidget(inner)

        self.doppo = str(Path(__file__).resolve().parent / "lib" / "flatness_map.png")
        image = QImage(self.doppo)
        self.width = 470
        self.height = 470
        image = image.scaled(
            self.width, self.height, Qt.KeepAspectRatio, Qt.FastTransformation
        )
        imageLabel = QLabel()
        imageLabel.setPixmap(QPixmap.fromImage(image))
        imageLabel.scaleFactor = 1.0
        image_box.addWidget(imageLabel)

        image_box_h = QHBoxLayout()
        image_box_h.addStretch()
        image_box_h.addLayout(image_box)
        image_box_h.addStretch()

        layout.addLayout(titlebox)
        layout.addLayout(inner_box)
        layout.addLayout(button_box)
        layout.addLayout(image_box_h)

        self.setLayout(layout)

    def back_page(self):
        self.parent.back_to_test()

    def check_json(self):
        self.parent.confirm_json()

    def upload_to_db(self):
        self.parent.upload_to_db()

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
            editor.setText(str(form_text))
            editor.setReadOnly(True)
            editor.setFocusPolicy(Qt.NoFocus)
            editor.setStyleSheet("background-color : linen; color: black;")
        #        editor.setStyleSheet("background-color : azure")

        Form_layout.addRow(label, editor)

    #################################################################

    def layout_ModuleQC(self):
        HBox = QHBoxLayout()

        Form_layout = self.parent.confirm_layout_common(self)

        self.add_info(
            Form_layout,
            "Back-side Flatness (µm):",
            # self.parent.testRun["results"]["Measurements"]["BACKSIDE_FLATNESS"][
            #    "Values"
            # ],
            self.parent.testRun["results"]["Measurements"]["BACKSIDE_FLATNESS"],
        )
        if "ANGLES" in self.parent.testRun["results"]["Measurements"]:
            self.add_info(
                Form_layout,
                "Angles (deg.):",
                # self.parent.testRun["results"]["Measurements"]["ANGLES"]["Values"],
                self.parent.testRun["results"]["Measurements"]["ANGLES"],
            )
        self.add_info(
            Form_layout, "Comment :", self.parent.testRun["results"]["comment"]
        )

        HBox.addLayout(Form_layout)

        return HBox
