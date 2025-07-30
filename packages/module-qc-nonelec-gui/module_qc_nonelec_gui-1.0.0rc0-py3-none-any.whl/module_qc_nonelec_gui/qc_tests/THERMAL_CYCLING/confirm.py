from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFormLayout,
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
        if self.parent.isPractice:
            titlebox.addWidget(label_practice)

        button_box.addWidget(back_button)
        button_box.addStretch()
        button_box.addWidget(json_button)
        button_box.addWidget(Upload_button)

        inner = QScrollArea()
        inner.setFixedHeight(400)
        inner.setFixedWidth(600)
        result_wid = QWidget()
        result_wid.setLayout(self.make_layout())

        inner.setWidgetResizable(True)
        inner.setWidget(result_wid)

        layout.addLayout(titlebox)
        layout.addWidget(inner)
        layout.addLayout(button_box)
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
            editor.setText(form_text)
            editor.setReadOnly(True)
            editor.setFocusPolicy(Qt.NoFocus)
            editor.setStyleSheet("background-color : linen; color: black;")
        #        editor.setStyleSheet("background-color : azure")

        Form_layout.addRow(label, editor)

    #################################################################
    def make_layout(self):
        if (
            self.parent.info_dict["componentType"] == "MODULE"
            or self.parent.info_dict["componentType"] == "practice"
        ):
            return self.layout_ModuleQC()
        return self.layout_ModuleQC()

    def layout_ModuleQC(self):
        Form_layout = QFormLayout()
        self.add_info(
            Form_layout,
            "Current Stage :",
            self.parent.result_dict["localDB"]["stage"],
        )
        self.add_info(
            Form_layout, "Test Type :", self.parent.result_dict["localDB"]["testType"]
        )

        self.add_info(
            Form_layout,
            "Machine :",
            self.parent.result_dict["localDB"]["results"]["property"]["Machine"],
        )
        self.add_info(
            Form_layout,
            "# of Thermal Cycle :",
            str(self.parent.result_dict["localDB"]["results"]["property"]["N_cycle"]),
        )

        Cycle_speed = (
            str(
                self.parent.result_dict["localDB"]["results"]["property"][
                    "Cycle_speed_value"
                ]
            )
            + " "
            + self.parent.result_dict["localDB"]["results"]["property"][
                "Cycle_speed_unit"
            ]
        )
        Min_temp = (
            str(
                self.parent.result_dict["localDB"]["results"]["property"][
                    "Temp_min_value"
                ]
            )
            + " "
            + self.parent.result_dict["localDB"]["results"]["Temp_unit"]
        )
        Max_temp = (
            str(
                self.parent.result_dict["localDB"]["results"]["property"][
                    "Temp_max_value"
                ]
            )
            + " "
            + self.parent.result_dict["localDB"]["results"]["Temp_unit"]
        )

        self.add_info(Form_layout, "Thermal Cycling Speed :", Cycle_speed)
        self.add_info(Form_layout, "Minimum Temperature :", Min_temp)
        self.add_info(Form_layout, "Maximum Temperature :", Max_temp)

        self.add_info(
            Form_layout,
            "Temperature log :",
            self.parent.test_result_dict["results"]["summary"]["Temp_log_path"],
        )
        self.add_info(
            Form_layout,
            "Humidity log :",
            self.parent.test_result_dict["results"]["summary"]["Humi_log_path"],
        )

        self.add_info(
            Form_layout,
            "Comment :",
            self.parent.result_dict["localDB"]["results"]["comment"],
        )

        return Form_layout
