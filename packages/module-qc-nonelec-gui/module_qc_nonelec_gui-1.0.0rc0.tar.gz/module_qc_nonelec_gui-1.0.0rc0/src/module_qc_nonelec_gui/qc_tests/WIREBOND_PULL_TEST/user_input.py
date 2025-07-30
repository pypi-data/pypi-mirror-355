from __future__ import annotations

import csv
import logging
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (
    QComboBox,
    QFileDialog,
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
        comment_layout = QVBoxLayout()

        label_title = QLabel()
        label_title.setText(
            '<center><font size="5">Input the result of wirebond pull test</font></center>'
        )

        Next_button = QPushButton("&Next")
        Next_button.clicked.connect(self.pass_result)
        Back_button = QPushButton("&Back")
        Back_button.clicked.connect(self.back_page)

        bottom_box.addWidget(Back_button)
        bottom_box.addStretch()
        bottom_box.addWidget(Next_button)

        self.pull_strength_fields = []
        self.break_mode_fields = []
        self.properties = []

        layout_properties = QVBoxLayout()
        layout_properties.addLayout(
            self.add_text_input("Operator ID", "OPERATOR_IDENTITY")
        )
        layout_properties.addLayout(self.add_text_input("Instrument", "INSTRUMENT"))

        inner = QScrollArea()
        inner.setFixedWidth(600)
        inner.setFixedHeight(400)
        result_wid = QWidget()
        result_layout = QVBoxLayout()
        for i in range(32):
            result_layout.addLayout(self.create_pull_slot(i))

        result_wid.setLayout(result_layout)
        inner.setWidget(result_wid)

        select_button = QPushButton("Select CSV...")
        select_button.clicked.connect(self.select_file)

        label_comment = QLabel()
        label_comment.setText("Comment : ")

        self.edit_result = QLineEdit()
        self.edit_result.setFocusPolicy(Qt.NoFocus)
        self.edit_result.setReadOnly(True)
        self.edit_result.setFixedWidth(500)

        label_manual = QLabel()
        label_manual.setText("Additional Manual Inputs:")

        self.edit_comment = QTextEdit()
        self.edit_comment.setText(self.parent.result_info["comment"])

        comment_layout.addWidget(label_comment)
        comment_layout.addWidget(self.edit_comment)

        csv_layout = QHBoxLayout()
        csv_layout.addWidget(select_button)
        csv_layout.addWidget(self.edit_result)

        layout.addWidget(label_title)
        layout.addStretch()
        layout.addLayout(layout_properties)
        layout.addLayout(csv_layout)
        layout.addWidget(label_manual)
        layout.addWidget(inner)
        layout.addWidget(label_comment)
        layout.addLayout(comment_layout)
        layout.addLayout(bottom_box)

        self.setLayout(layout)

    def add_text_input(self, title, code):
        layout = QHBoxLayout()
        label = QLabel()
        label.setText(title + ": ")

        property_input = QLineEdit()
        property_input.setFixedWidth(200)

        self.properties += [{"code": code, "field": property_input}]

        layout.addWidget(label)
        layout.addWidget(property_input)
        layout.addStretch()

        return layout

    def create_pull_slot(self, index):
        layout = QHBoxLayout()
        label = QLabel()
        label.setText(f"<b>Wire #{index+1}</b>      ")

        label_strength = QLabel()
        label_strength.setText("Pull Strength [g]: ")

        strength_field = QLineEdit()
        strength_field.setAlignment(Qt.AlignRight)
        strength_field.setValidator(QDoubleValidator(0.0, 20.0, 2))
        strength_field.setFixedWidth(50)
        strength_field.setMaxLength(5)

        layout.addWidget(label)
        layout.addWidget(label_strength)
        layout.addWidget(strength_field)

        self.break_modes = [
            "Heel break on chip",
            "Heel break on hybrid",
            "Midspan break",
            "Bond peel on chip",
            "Bond peel on hybrid",
            "Operator error",
            "other error",
        ]

        combo = QComboBox()
        for mode in self.break_modes:
            combo.addItem(mode)
        combo.setPlaceholderText("Select the breaking mode...")
        combo.setCurrentIndex(-1)

        self.pull_strength_fields += [strength_field]
        self.break_mode_fields += [combo]

        layout.addWidget(combo)

        return layout

    def pass_result(self):
        for prop in self.properties:
            if prop["field"].text() == "":
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"Empty {prop['code']} value!",
                    QMessageBox.Ok,
                )
                return

            self.parent.parent.testRun["results"]["property"][prop["code"]] = prop[
                "field"
            ].text()

        sample_file = self.edit_result.text()

        pull_data = []

        try:
            with Path(sample_file).open(encoding="utf-8") as f:
                reader = csv.reader(f)

                for index, row in enumerate(reader):
                    # validation
                    if len(row) < 2:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Wire #{index+1} info is complete (pull strength and breaking mode need to be specified):\n {row}",
                            QMessageBox.Ok,
                        )
                        return

                    try:
                        strength = float(row[0])

                    except Exception:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Wire #{index+1} strength needs to be a float number (unit: [g])",
                            QMessageBox.Ok,
                        )
                        return

                    if strength <= 0.0:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Wire #{index+1} strength needs to be a positive value",
                            QMessageBox.Ok,
                        )
                        return

                    if row[1] not in self.break_modes:
                        QMessageBox.warning(
                            self,
                            "Warning",
                            f"Wire #{index+1}: breaking mode needs to be one of {self.breaking_modes}",
                            QMessageBox.Ok,
                        )
                        return

                # Validation is done, filling

            with Path(sample_file).open(encoding="utf-8") as f:
                reader = csv.reader(f)

                for index, row in enumerate(reader):
                    if len(row) == 2:
                        if index < 10:
                            pull_data += [
                                {
                                    "strength": float(row[0]),
                                    "break_mode": row[1],
                                    "location": 1,
                                }
                            ]
                        elif index < 15:
                            pull_data += [
                                {
                                    "strength": float(row[0]),
                                    "break_mode": row[1],
                                    "location": 2,
                                }
                            ]
                        elif index < 25:
                            pull_data += [
                                {
                                    "strength": float(row[0]),
                                    "break_mode": row[1],
                                    "location": 3,
                                }
                            ]
                        else:
                            pull_data += [
                                {
                                    "strength": float(row[0]),
                                    "break_mode": row[1],
                                    "location": 4,
                                }
                            ]

                    elif len(row) == 3:
                        pull_data += [
                            {
                                "strength": float(row[0]),
                                "break_mode": row[1],
                                "location": int(row[2]),
                            }
                        ]

        except Exception:
            pass

        for index, fields in enumerate(
            zip(self.pull_strength_fields, self.break_mode_fields, strict=False)
        ):
            strength = fields[0]
            mode = fields[1]
            try:
                pull_data += [
                    {
                        "strength": float(strength.text()),
                        "break_mode": mode.currentText(),
                    }
                ]
            except Exception:
                if strength.text() != "":
                    QMessageBox.warning(
                        self,
                        "Warning",
                        f"Wire #{index+1} has an input error",
                        QMessageBox.Ok,
                    )
                    return

        if len(pull_data) < 8:
            QMessageBox.warning(
                self,
                "Warning",
                f"At least 8 measurements are required (current input: {len(pull_data)})",
                QMessageBox.Ok,
            )
            return

        self.parent.parent.testRun["results"]["Metadata"]["pull_data"] = pull_data

        self.parent.parent.testRun["results"][
            "comment"
        ] = self.edit_comment.toPlainText()

        self.parent.parent.receive_result(self)

    def select_file(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)

        try:
            dlg.exec_()
            filename = dlg.selectedFiles()[0]
            self.edit_result.setText(filename)
        except Exception:
            QMessageBox.warning(
                None, "Warning", "Please select a correct file", QMessageBox.Ok
            )

    def back_page(self):
        self.parent.close_and_return()
