from __future__ import annotations

import logging
import traceback
from pathlib import Path

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

        layout = QVBoxLayout()
        bottom_box = QHBoxLayout()
        grid_edit = QGridLayout()

        HBox1 = QHBoxLayout()
        HBox2 = QHBoxLayout()

        label_title = QLabel()
        label_title.setText(
            '<center><font size="7">Choose result csv file</font></center>'
        )

        # Create Button Widget
        Next_button = QPushButton("&Next")
        Next_button.clicked.connect(self.pass_result)

        Back_button = QPushButton("&Back")
        Back_button.clicked.connect(self.back_page)

        Choose_button = QPushButton("Choose file")
        Choose_button.clicked.connect(self.choose_file)

        # layout Screen
        bottom_box.addWidget(Back_button)
        bottom_box.addStretch()
        bottom_box.addWidget(Next_button)

        label_result = QLabel()
        label_result.setText("LAYER_THICKNESS file : ")
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

    def choose_file(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)

        try:
            dlg.exec_()
            pathname = dlg.selectedFiles()[0]
            self.edit_result.setText(pathname)
            # self.pass_result(str(pathname))
        except Exception:
            log.exception(traceback.format_exc())
            QMessageBox.warning(
                None, "Warning", "Please choose correct file", QMessageBox.Ok
            )

    def pass_result(self):
        try:
            # Read txt file
            filepath = self.edit_result.text()
            self.parent.result_info["filename"] = filepath
            free_comment = self.edit_comment.toPlainText()
            with Path(filepath).open(encoding="utf-8") as f:
                data = []
                mm = 1000

                for line in f.readlines():
                    rawdata = line.split(" ")
                    data.append(float(rawdata[2]) * mm)

                if len(data) != 15:
                    QMessageBox.warning(
                        None,
                        "Warning",
                        "Data size is Wrong!! Please choose correct file",
                        QMessageBox.Ok,
                    )
                    exit(1)

                else:
                    corr = [
                        -5.8,
                        -0.2,
                        3.7,
                        6.1,
                        10.5,
                        12.5,
                        13.4,
                        13.5,
                        11.5,
                        11.9,
                        9.2,
                        5.7,
                        4.7,
                        0,
                        0,
                    ]

                    for x in range(len(corr)):
                        data[x] = data[x] - corr[x]

                bottom_thickness = round(data[5] - data[2], 5)
                coverlay = round(data[13] - data[11], 5)
                dielectric_thickness = round(data[11], 5)
                inner_thickness = round(data[2] - data[11], 5)
                soldermask_thickness = round(data[8] - data[9] + 4, 5)
                thickness = round(data[8], 5)
                top_thickness = round(data[1] - data[11], 5)

            # Create json format
            self.results = {
                "BOTTOM_LAYER_THICKNESS": bottom_thickness,
                "COVERLAY_WITH_ADHESIVE_THICKNESS": coverlay,
                "DIELECTRIC_THICKNESS": dielectric_thickness,
                "INNER_LAYER_THICKNESS": inner_thickness,
                "SOLDERMASK_THICKNESS": soldermask_thickness,
                "THICKNESS": thickness,
                "TOP_LAYER_THICKNESS": top_thickness,
            }

            # Display the filename in the edit_result widget
            # self.edit_result.setText(filepath)
            self.parent.parent.testRun["results"]["comment"] = str(free_comment)
            self.parent.parent.testRun["results"]["Metadata"][
                "Measurement"
            ] = self.results
            self.hide()
            self.parent.parent.receive_result(self)

        except Exception as e:
            log.exception(f"Error processing file: {e}")
            log.exception(traceback.format_exc())
            QMessageBox.warning(
                None,
                "Warning",
                "Error processing file. Please choose a correct file.",
                QMessageBox.Ok,
            )
            return

    def back_page(self):
        self.parent.back_to_test()

    def upload_to_db(self):
        self.parent.upload_to_db()


"""
    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        return file_path
"""
