from __future__ import annotations

import logging
import traceback

import pandas as pd
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
        label_result.setText("LV_HV_TEST file : ")
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
            # Read CSV file
            filepath = self.edit_result.text()
            self.parent.result_info["filename"] = filepath
            flex_data = pd.read_csv(filepath, encoding="latin1")
            free_comment = self.edit_comment.toPlainText()

            # Extract data from CSV
            time_list = flex_data["Unnamed: 0"].tolist()
            vin_minus_list = flex_data.filter(like="VIN-").squeeze().tolist()
            vin_plus_list = flex_data.filter(like="VIN+").squeeze().tolist()
            gnd_minus_list = flex_data.filter(like="GND-").squeeze().tolist()
            gnd_plus_list = flex_data.filter(like="GND+").squeeze().tolist()
            HV_list = flex_data.filter(like="HV").squeeze().tolist()
            NTC_list = flex_data.filter(like="NTC").squeeze().tolist()
            try:
                humidity_list = flex_data.filter(like="Humidity").squeeze().tolist()
            except Exception:
                humidity_list = [10 for _ in range(700)]
            try:
                temperature_list = (
                    flex_data.filter(like="Temperature").squeeze().tolist()
                )
            except Exception:
                temperature_list = [24 for _ in range(700)]

            # Obtain the Value at 10:20
            try:
                time_index = time_list.index("0:10:20")
            except Exception:
                try:
                    time_index = time_list.index("00:10:20")
                except Exception:
                    exit(1)

            # Extract values at the specified time index
            vin_minus_value = vin_minus_list[time_index]
            vin_plus_value = vin_plus_list[time_index]
            gnd_minus_value = gnd_minus_list[time_index]
            gnd_plus_value = gnd_plus_list[time_index]
            HV_value = HV_list[time_index]
            NTC_value = NTC_list[time_index]
            humidity_value = humidity_list[time_index]
            temperature_value = temperature_list[time_index]

            # Calculate Rvin and Rgnd Values
            self.vin_drop = round(vin_plus_value - vin_minus_value, 3)
            self.vin_drop = abs(self.vin_drop)
            self.Rvin = round(self.vin_drop / 10 / 5 * 1000, 3)  # [mΩ]

            self.gnd_drop = round(gnd_plus_value - gnd_minus_value, 3)
            self.gnd_drop = abs(self.gnd_drop)
            self.Rgnd = round(self.gnd_drop / 10 / 5 * 1000, 3)  # [mΩ]

            # self.Reff = round(self.Rvin + self.Rgnd, 3) - 5  # [mΩ]# 5mohm pogo-pin resistance
            self.Reff = (
                round(self.Rvin + self.Rgnd, 3) - 3.7
            )  # [mΩ]# 5mohm pogo-pin resistance

            # Calculate Leakage Current Value
            self.cur = round(HV_value / 10 / 1e6 * 1e9, 3)  # [nA]
            self.hv_leakage = round(HV_value * 1000)  # [mV]

            # Calculate Resistance of NTC
            self.Rntc = round(0.2 * 51 / NTC_value, 3)  # [kΩ]

            # Calculate Humidity
            self.humidity = round(humidity_value * 100, 3)  # [RH%]
            # Calculate temperature
            self.temperature = round(temperature_value * 100, 3)  # [RH%]

            # Create json format
            self.results = {
                "VIN_DROP[V]": self.vin_drop,
                # "VIN_RESISTANCE[mOhm]": self.Rvin,
                "GND_DROP[V]": self.gnd_drop,
                # "GND_RESISTANCE[mOhm]": self.Rgnd,
                "EFFECTIVE_RESISTANCE[mOhm]": self.Reff,
                "HV_LEAKAGE[mV]": self.hv_leakage,
                "LEAKAGE_CURRENT[nA]": self.cur,
                "NTC_VOLTAGE[V]": NTC_value,
                "NTC_VALUE[kOhm]": self.Rntc,
                "HUMIDITY[RH%]": self.humidity,
                "TEST_DURATION[min]": 10,
                "TEMPERATURE": self.temperature,
                "R1_HV_RESISTOR": -1,
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
