from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
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


class InitialWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent

        layout = QVBoxLayout()
        bottom_box = QHBoxLayout()
        grid_edit = QGridLayout()

        label_title = QLabel()
        label_title.setText(
            '<center><font size="7">Input thermal cycling information</font></center>'
        )

        Next_button = QPushButton("&Next")
        Next_button.clicked.connect(self.pass_result)
        Back_button = QPushButton("&Back")
        Back_button.clicked.connect(self.back_page)

        bottom_box.addWidget(Back_button)
        bottom_box.addStretch()
        bottom_box.addWidget(Next_button)

        label_comment = QLabel()
        label_comment.setText("comment : ")
        label_Ncycle = QLabel()
        label_Ncycle.setText("# of Thermal Cycle  : ")
        label_cycle_speed = QLabel()
        label_cycle_speed.setText("Thermal Cycling Speed : ")
        label_Temp_min = QLabel()
        label_Temp_min.setText("Minimum Temperature : ")
        label_Temp_max = QLabel()
        label_Temp_max.setText("Maximum Temperature : ")

        self.edit_comment = QTextEdit()
        self.edit_comment.setText(self.parent.result_info["comment"])

        self.edit_machine = self.make_textform(
            "Machine : ", self.parent.result_info["Machine"], grid_edit, 0
        )
        #        self.edit_Ncycle   = self.make_textform('Number of cycle : ',self.parent.result_info['N_cycle'],grid_edit,1)

        grid_edit.addWidget(label_Ncycle, 1, 0)
        grid_edit.addLayout(self.make_Ncycle_layout(), 1, 1)

        grid_edit.addWidget(label_cycle_speed, 2, 0)
        grid_edit.addLayout(self.make_cycle_speed_layout(), 2, 1)

        grid_edit.addWidget(label_Temp_min, 3, 0)
        grid_edit.addLayout(self.make_Temp_min_layout(), 3, 1)

        grid_edit.addWidget(label_Temp_max, 4, 0)
        grid_edit.addLayout(self.make_Temp_max_layout(), 4, 1)

        self.temp_log = self.select_file_layout(
            "Temperature log : ", self.parent.result_info["Temp_log_path"], grid_edit, 5
        )
        self.humi_log = self.select_file_layout(
            "Humidity log : ", self.parent.result_info["Temp_log_path"], grid_edit, 6
        )

        grid_edit.addWidget(label_comment, 7, 0)

        outer = QScrollArea()
        outer.setWidgetResizable(True)
        outer.setWidget(self.edit_comment)
        grid_edit.addWidget(outer, 7, 1)

        layout.addWidget(label_title)
        layout.addStretch()
        layout.addLayout(grid_edit)
        layout.addLayout(bottom_box)

        self.setLayout(layout)

    def make_Temp_min_layout(self):
        grid_layout, self.edit_Temp_min = self.make_value_unit_layout(
            str(self.parent.result_info["Temp_min_value"]),
            self.parent.result_info["Temp_unit"],
        )

        return grid_layout

    def make_Temp_max_layout(self):
        grid_layout, self.edit_Temp_max = self.make_value_unit_layout(
            str(self.parent.result_info["Temp_max_value"]),
            self.parent.result_info["Temp_unit"],
        )

        return grid_layout

    def make_Ncycle_layout(self):
        #        grid_layout, self.edit_Ncycle =  self.make_value_unit_layout( str(self.parent.result_info['N_cycle']), '' )

        self.edit_Ncycle = QLineEdit()
        self.edit_Ncycle.setValidator(QIntValidator())
        self.edit_Ncycle.setAlignment(Qt.AlignRight)
        self.edit_Ncycle.setText(str(self.parent.result_info["N_cycle"]))

        layout = QHBoxLayout()
        layout.addWidget(self.edit_Ncycle)

        return layout

    def make_cycle_speed_layout(self):
        grid_layout, self.edit_cycle_speed = self.make_value_unit_layout(
            str(self.parent.result_info["Cycle_speed_value"]),
            self.parent.result_info["Cycle_speed_unit"],
        )

        return grid_layout

    def make_value_unit_layout(self, value_str, unit_str):
        grid_layout = QGridLayout()

        label = QLabel()
        label.setText(unit_str)

        edit_value = QLineEdit()
        edit_value.setValidator(QDoubleValidator())
        edit_value.setAlignment(Qt.AlignRight)
        edit_value.setText(value_str)

        grid_layout.addWidget(edit_value, 0, 0)
        grid_layout.addWidget(label, 0, 1)

        return grid_layout, edit_value

    def make_textform(self, label, initial, layout, i):
        label_text = QLabel()
        label_text.setText(label)
        edit_text = QLineEdit()
        edit_text.setText(initial)

        if initial == "TBA":
            edit_text.setStyleSheet("color: black; background-color:linen;")
            edit_text.setReadOnly(True)
            edit_text.setFocusPolicy(Qt.NoFocus)

        layout.addWidget(label_text, i, 0)
        layout.addWidget(edit_text, i, 1)

        return edit_text

    def select_file_layout(self, label, initial, layout, i):
        label_text = QLabel()
        label_text.setText(label)
        edit_text = QLineEdit()
        edit_text.setText(initial)
        edit_text.setFocusPolicy(Qt.NoFocus)
        edit_text.setReadOnly(True)

        Choose_button = QPushButton("Choose file")
        Choose_button.clicked.connect(lambda: self.get_path(edit_text))

        box = QHBoxLayout()
        box.addWidget(edit_text)
        box.addWidget(Choose_button)

        layout.addWidget(label_text, i, 0)
        layout.addLayout(box, i, 1)

        return edit_text

    def get_path(self, lineedit):
        lineedit.setText(self.choose_file())

    def choose_file(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)

        try:
            dlg.exec_()
            return dlg.selectedFiles()[0]
        except Exception:
            QMessageBox.warning(
                None, "Warning", "Please choose correct file", QMessageBox.Ok
            )
        return None

    def pass_result(self):
        token = 0
        try:
            result_dict = {
                "comment": self.edit_comment.toPlainText(),
                "Machine": self.edit_machine.text(),
                "Temp_log_path": self.temp_log.text(),
                "Humi_log_path": self.humi_log.text(),
                "Temp_min_value": float(self.edit_Temp_min.text()),
                "Temp_max_value": float(self.edit_Temp_max.text()),
                "N_cycle": int(self.edit_Ncycle.text()),
                "Cycle_speed_value": float(self.edit_cycle_speed.text()),
            }
            token = 1
        except Exception:
            #            import traceback
            #            print (traceback.format_exc() )
            QMessageBox.warning(
                None, "Warning", "Please fill these form.", QMessageBox.Ok
            )

        if token == 1:
            if int(self.edit_Ncycle.text()) < 0:
                QMessageBox.warning(
                    None,
                    "Warning",
                    "Negative value is not supported for the number of cycles.",
                    QMessageBox.Ok,
                )
            else:
                if (
                    Path(self.temp_log.text()).is_file()
                    and Path(self.humi_log.text()).is_file()
                ):
                    self.parent.receive_result(result_dict)
                else:
                    QMessageBox.critical(
                        None, "Warning", "Log file not exist.", QMessageBox.Ok
                    )

    def back_page(self):
        self.parent.close_and_return()
