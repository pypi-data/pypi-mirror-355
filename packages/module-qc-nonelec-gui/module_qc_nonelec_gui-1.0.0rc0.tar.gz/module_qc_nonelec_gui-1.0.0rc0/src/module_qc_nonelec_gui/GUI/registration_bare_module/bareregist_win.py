from __future__ import annotations

from PyQt5.QtWidgets import QComboBox, QGridLayout, QLabel, QPushButton, QWidget


class BareRegistWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__()
        self.parent = parent

        layout = QGridLayout()
        list_baretype = [""]
        list_FE_chipversion = [""]
        list_FE_thickness = [""]
        list_sensortype = [""]

        for bare_type in self.parent.baremodule_doc["types"]:
            list_baretype.append(bare_type["name"])

        property_SENSORTYPE = [
            prop
            for prop in self.parent.baremodule_doc["properties"]
            if prop["code"] == "SENSOR_TYPE"
        ]
        self.codeTable_SENSORTYPE = property_SENSORTYPE[0]["codeTable"]

        property_FECHIPVERSION = [
            prop
            for prop in self.parent.baremodule_doc["properties"]
            if prop["code"] == "FECHIP_VERSION"
        ]
        self.codeTable_FECHIPVERSION = property_FECHIPVERSION[0]["codeTable"]

        property_FETHICKNESS = [
            prop
            for prop in self.parent.baremodule_doc["properties"]
            if prop["code"] == "THICKNESS"
        ]
        self.codeTable_FETHICKNESS = property_FETHICKNESS[0]["codeTable"]

        for sensortype in self.codeTable_SENSORTYPE:
            list_sensortype.append(sensortype["value"])

        for fechipversion in self.codeTable_FECHIPVERSION:
            list_FE_chipversion.append(fechipversion["value"])

        for fethickness in self.codeTable_FETHICKNESS:
            list_FE_thickness.append(fethickness["value"])

        self.cb_baretype = QComboBox()
        self.cb_baretype.addItems(list_baretype)
        self.cb_FE_chipversion = QComboBox()
        self.cb_FE_chipversion.addItems(list_FE_chipversion)
        self.cb_FE_thickness = QComboBox()
        self.cb_FE_thickness.addItems(list_FE_thickness)
        self.cb_sensortype = QComboBox()
        self.cb_sensortype.addItems(list_sensortype)

        self.cb_baretype.activated[str].connect(self.onActivated_baretype)
        self.cb_FE_chipversion.activated[str].connect(self.onActivated_FE_chipversion)
        self.cb_FE_thickness.activated[str].connect(self.onActivated_FE_thickness)
        self.cb_sensortype.activated[str].connect(self.onActivated_sensortype)

        label_title = QLabel()
        label_title.setText("Select Bare Module Information")
        label_baretype = QLabel()
        label_baretype.setText("Bare Module Type")
        label_FE_chipversion = QLabel()
        label_FE_chipversion.setText("FE chip version")
        label_FE_thickness = QLabel()
        label_FE_thickness.setText("FE chip thickness")
        label_sensortype = QLabel()
        label_sensortype.setText("Sensor Type")

        button_next = QPushButton("&Register")
        button_next.clicked.connect(self.next_page)

        button_back = QPushButton("&Back")
        button_back.clicked.connect(self.back_page)

        layout.addWidget(label_title, 0, 0)
        layout.addWidget(label_baretype, 1, 0)
        layout.addWidget(self.cb_baretype, 1, 1)
        layout.addWidget(label_FE_chipversion, 2, 0)
        layout.addWidget(self.cb_FE_chipversion, 2, 1)
        layout.addWidget(label_FE_thickness, 3, 0)
        layout.addWidget(self.cb_FE_thickness, 3, 1)
        layout.addWidget(label_sensortype, 4, 0)
        layout.addWidget(self.cb_sensortype, 4, 1)
        layout.addWidget(button_next, 5, 1)
        layout.addWidget(button_back, 5, 0)
        self.setLayout(layout)

    def next_page(self):
        self.parent.register_baremodule()
        self.parent.feinfo()

    def back_page(self):
        self.parent.choose_menu()

    def onActivated_baretype(self, text):
        for bare_type in self.parent.baremodule_doc["types"]:
            if bare_type["name"] == text:
                self.parent.baremodule_info["type"] = bare_type["code"]

    def onActivated_FE_chipversion(self, text):
        for fechipversion in self.codeTable_FECHIPVERSION:
            if fechipversion["value"] == text:
                self.parent.baremodule_info["properties"]["FECHIP_VERSION"] = (
                    fechipversion["code"]
                )

    def onActivated_FE_thickness(self, text):
        for fethickness in self.codeTable_FETHICKNESS:
            if fethickness["value"] == text:
                self.parent.baremodule_info["properties"]["THICKNESS"] = fethickness[
                    "code"
                ]

    def onActivated_sensortype(self, text):
        for sensortype in self.codeTable_SENSORTYPE:
            if sensortype["value"] == text:
                self.parent.baremodule_info["properties"]["SENSOR_TYPE"] = sensortype[
                    "code"
                ]
