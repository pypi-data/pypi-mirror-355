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
            "Glue name :",
            self.parent.result_dict["localDB"]["results"]["property"]["Glue_name"],
        )
        self.add_info(
            Form_layout,
            "Volume ratio of glue mixture :",
            self.parent.result_dict["localDB"]["results"]["property"][
                "Volume_ratio_of_glue_mixture"
            ],
        )
        self.add_info(
            Form_layout,
            "Glue batch number :",
            self.parent.result_dict["localDB"]["results"]["property"][
                "Glue_batch_number"
            ],
        )

        room_temp = (
            str(self.parent.result_dict["localDB"]["results"]["Room_temperature"])
            + " "
            + self.parent.result_dict["localDB"]["results"]["Temperature_unit"]
        )
        humidity = (
            str(self.parent.result_dict["localDB"]["results"]["Humidity"])
            + " "
            + self.parent.result_dict["localDB"]["results"]["Humidity_unit"]
        )

        #        day    = str( self.parent.result_dict['localDB']['results']['Adhesion_Time']['day'])
        #        hour   = str( self.parent.result_dict['localDB']['results']['Adhesion_Time']['hour'])
        #        minute = str( self.parent.result_dict['localDB']['results']['Adhesion_Time']['minute'])
        #        second = str( self.parent.result_dict['localDB']['results']['Adhesion_Time']['second'])

        #        adhesion_time = day + 'd:' + hour + 'h:' + minute + 'm:' + second + 's'

        self.add_info(Form_layout, "Room temperature :", room_temp)
        self.add_info(Form_layout, "Humidity :", humidity)
        #        self.add_info(Form_layout,'Adhesion time :',  adhesion_time)
        self.add_info(
            Form_layout,
            "Comment :",
            self.parent.result_dict["localDB"]["results"]["comment"],
        )

        return Form_layout
