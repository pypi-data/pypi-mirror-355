from __future__ import annotations

import json
import logging
import traceback
from pathlib import Path

import jsonschema
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFileDialog,
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

        ###############################################################
        ########         json schema file path                 ########
        try:
            self.jsonschema_path = str(
                Path(__file__).resolve().parent
                / "example"
                / "jsonschema"
                / "schema.json"
            )
        except Exception as e:
            log.exception(str(e))
            self.jsonschema_path = ""
        ###############################################################

        layout = QVBoxLayout()
        bottom_box = QHBoxLayout()
        grid_layout = QGridLayout()

        HBox1 = QHBoxLayout()
        HBox2 = QHBoxLayout()

        label_title = QLabel()
        label_title.setText('<center><font size="7">Flatness</font></center>')

        File_button = QPushButton("&Choose file")
        File_button.clicked.connect(self.choose_file)

        label_result = QLabel()
        label_result.setText("Result file: ")
        label_comment = QLabel()
        label_comment.setText("Comment : ")

        self.edit_comment = QTextEdit()
        # self.edit_comment.setText(self.parent.result_info["comment"])
        self.edit_result = QLineEdit()
        self.edit_result.setFocusPolicy(Qt.NoFocus)
        self.edit_result.setReadOnly(True)
        if "filename" in self.parent.result_info:
            self.edit_result.setText(self.parent.result_info["filename"])
        else:
            self.edit_result.setText("")

        HBox1.addWidget(self.edit_result)
        HBox1.addWidget(File_button)

        grid_layout.addWidget(label_result, 0, 0)
        grid_layout.addWidget(self.edit_result, 0, 1)
        grid_layout.addWidget(File_button, 0, 2)

        grid_layout.addWidget(label_comment, 1, 0)

        Next_button = QPushButton("&Next")
        Next_button.clicked.connect(self.receive_path)
        Back_button = QPushButton("&Back")
        Back_button.clicked.connect(self.back_page)

        bottom_box.addWidget(Back_button)
        bottom_box.addStretch()
        bottom_box.addWidget(Next_button)

        outer = QScrollArea()
        outer.setWidgetResizable(True)
        outer.setWidget(self.edit_comment)
        HBox2.addWidget(outer)
        grid_layout.addWidget(outer, 1, 1)

        layout.addWidget(label_title)
        layout.addStretch()
        layout.addLayout(grid_layout)
        layout.addLayout(bottom_box)

        self.setLayout(layout)

    def choose_file(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)

        try:
            dlg.exec_()
            filename = dlg.selectedFiles()[0]
            self.edit_result.setText(filename)
        except Exception as e:
            log.exception(str(e))

            log.exception(traceback.format_exc())
            QMessageBox.warning(
                None, "Error", "Please choose correct file", QMessageBox.Ok
            )

    def receive_path(
        self,
    ):
        try:
            self.parent.result_info["filename"] = self.edit_result.text()
            with Path(self.edit_result.text()).open(encoding="utf-8") as f:
                result_dict = json.load(f)

            with Path(self.jsonschema_path).open(encoding="utf-8") as f:
                jsonschema_dict = json.load(f)
            jsonschema.validate(result_dict, jsonschema_dict)

        #            free_comment = self.edit_comment.toPlainText()
        #            self.parent.receive_result(result_dict,free_comment)

        except jsonschema.exceptions.ValidationError:
            log.exception(traceback.format_exc())
            QMessageBox.warning(
                None,
                "Error",
                "JSON File format not correct. \nPlease check the message on CUI.",
                QMessageBox.Ok,
            )
            self.choose_file()
        except Exception as e:
            log.exception(str(e))
            log.exception(traceback.format_exc())
            QMessageBox.warning(None, "Error", "Unexpected Error", QMessageBox.Ok)

        free_comment = self.edit_comment.toPlainText()
        self.parent.receive_result(free_comment)

    def back_page(self):
        self.parent.close_and_return()
