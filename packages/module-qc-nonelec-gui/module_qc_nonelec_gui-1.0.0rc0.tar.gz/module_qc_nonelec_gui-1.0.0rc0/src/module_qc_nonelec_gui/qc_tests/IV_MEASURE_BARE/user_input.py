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

from module_qc_nonelec_gui.qc_tests.IV_MEASURE_BARE import function

log = logging.getLogger(__name__)


class InitialWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        ###############################################################
        ########         json schema file path                 ########
        try:
            self.jsonschema_path = Path(__file__).parent.joinpath(
                "example", "jsonschema", "validation_schema.json"
            )
        except Exception:
            self.jsonschema_path = ""
        ###############################################################

        layout = QVBoxLayout()
        bottom_box = QHBoxLayout()
        grid_edit = QGridLayout()

        HBox1 = QHBoxLayout()
        HBox2 = QHBoxLayout()

        label_title = QLabel()
        label_title.setText('<center><font size="7">Choose result file</font></center>')

        Next_button = QPushButton("&Next")
        Next_button.clicked.connect(self.pass_result)
        Back_button = QPushButton("&Back")
        Back_button.clicked.connect(self.back_page)

        Choose_button = QPushButton("Choose file")
        Choose_button.clicked.connect(self.choose_file)

        bottom_box.addWidget(Back_button)
        bottom_box.addStretch()
        bottom_box.addWidget(Next_button)

        label_result = QLabel()
        label_result.setText("I-V scan Result file : ")
        label_comment = QLabel()
        label_comment.setText("Comment : ")

        self.edit_comment = QTextEdit()
        self.edit_comment.setText(self.parent.result_info["comment"])
        self.edit_result = QLineEdit()
        self.edit_result.setFocusPolicy(Qt.NoFocus)
        self.edit_result.setReadOnly(True)
        self.edit_result.setFixedWidth(500)
        if self.parent.result_info["filename"] != "":
            self.edit_result.setText(self.parent.result_info["filename"])
        else:
            self.edit_result.setText("")

        HBox1.addWidget(self.edit_result)
        HBox1.addWidget(Choose_button)

        grid_edit.addWidget(label_result, 0, 0)
        grid_edit.addLayout(HBox1, 0, 1)

        grid_edit.addWidget(label_comment, 1, 0)

        outer = QScrollArea()
        outer.setWidgetResizable(True)
        outer.setWidget(self.edit_comment)
        HBox2.addWidget(outer)
        grid_edit.addWidget(outer, 1, 1)

        layout.addWidget(label_title)
        layout.addStretch()
        layout.addLayout(grid_edit)
        layout.addLayout(bottom_box)

        self.setLayout(layout)

        self.parent.parent.atlsn_sen = function.get_sensor(
            self.parent.parent, self.parent.parent.info_dict["component"]
        )
        self.parent.parent.dict_sen = function.fill_info_sensor(
            self.parent.parent,
            self.parent.parent.atlsn_sen,
            self.parent.parent.info_dict,
        )
        self.parent.parent.testRun_sen = function.get_testRun(
            self.parent.parent,
            self.parent.parent.dict_sen["component"],
            self.parent.parent.version,
            self.parent.parent.atlsn_sen,
        )

    def choose_file(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)

        try:
            dlg.exec_()
            filename = dlg.selectedFiles()[0]
            self.edit_result.setText(filename)
        except Exception:
            log.exception(traceback.format_exc())
            QMessageBox.warning(
                None, "Warning", "Please choose correct file", QMessageBox.Ok
            )

    def pass_result(self):
        try:
            self.parent.result_info["filename"] = self.edit_result.text()
            if ".dat" in self.edit_result.text():
                get_data = function.read_data(self.edit_result.text())

                result_dict = {
                    "IV_ARRAY": {
                        "time": get_data.get("time"),
                        "voltage": get_data.get("voltage"),
                        "current": get_data.get("current"),
                        "sigma current": get_data.get("sigma"),
                        "temperature": get_data.get("temp"),
                        "humidity": get_data.get("hum"),
                    }
                }
            else:
                with Path(self.edit_result.text()).open(encoding="utf-8") as f:
                    result_dict = json.load(f)

                with Path(self.jsonschema_path).open(encoding="utf-8") as f:
                    jsonschema_dict = json.load(f)
                jsonschema.validate(result_dict, jsonschema_dict)

            if result_dict["IV_ARRAY"].get("humidity") is None:
                result_dict["IV_ARRAY"]["humidity"] = [0] * len(
                    result_dict["IV_ARRAY"]["voltage"]
                )
            if result_dict["IV_ARRAY"]["sigma current"] is None:
                result_dict["IV_ARRAY"]["sigma current"] = [0] * len(
                    result_dict["IV_ARRAY"]["voltage"]
                )
            free_comment = self.edit_comment.toPlainText()

            self.parent.parent.testRun_sen["results"]["IV_ARRAY"] = result_dict[
                "IV_ARRAY"
            ]

            nElems = [
                len(result_dict["IV_ARRAY"][v])
                for v in [
                    "voltage",
                    "current",
                    "temperature",
                    "sigma current",
                    "humidity",
                    "time",
                ]
            ]

            if sum(int(nElems[0] == v) for v in nElems) < len(nElems):
                msg = "Format error: array sizes do not match each other in IV_ARRAY"
                raise Exception(msg)

            if "properties" in result_dict:
                for var in ["TEMP", "HUM"]:
                    self.parent.parent.testRun_sen["results"]["property"][var] = (
                        result_dict["properties"].get(var)
                    )

            self.parent.parent.testRun_sen["results"]["comment"] = str(free_comment)

            self.hide()

            # self.parent.parent.receive_result_IV(self)
            function.receive_result_IV(self.parent.parent, self)

        except jsonschema.exceptions.ValidationError:
            log.exception(traceback.format_exc())
            QMessageBox.warning(
                None, "Warning", "File format not correct", QMessageBox.Ok
            )
        except FileNotFoundError:
            log.exception(traceback.format_exc())
            QMessageBox.warning(None, "Warning", "File not found", QMessageBox.Ok)
        except Exception:
            log.exception(traceback.format_exc())
            QMessageBox.warning(None, "Warning", "Unexpected Error", QMessageBox.Ok)

    def back_page(self):
        self.parent.close_and_return()
