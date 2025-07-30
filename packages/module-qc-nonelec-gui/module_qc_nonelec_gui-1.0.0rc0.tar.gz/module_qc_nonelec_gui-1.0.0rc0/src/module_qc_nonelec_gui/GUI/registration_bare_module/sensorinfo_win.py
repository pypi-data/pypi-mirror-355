from __future__ import annotations

from PyQt5.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)


class SensorInfoWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__()
        self.parent = parent

        layout = QGridLayout()

        label_title = QLabel()
        label_title.setText("Input Sensor ATLAS Serial Number:")

        label_sensor = QLabel()
        label_sensor.setText("ATLAS Serial Number")

        self.edit_sensor = QLineEdit()

        button_next = QPushButton("&Assemble")
        button_next.clicked.connect(self.next_page)
        button_back = QPushButton("&Back")
        button_back.clicked.connect(self.back_page)
        button_skip = QPushButton("&Skip")
        button_skip.clicked.connect(self.skip_page)

        layout.addWidget(label_title, 0, 0)
        layout.addWidget(label_sensor, 1, 0)
        layout.addWidget(self.edit_sensor, 1, 1)
        layout.addWidget(button_back, 2, 0)
        layout.addWidget(button_skip, 2, 1)
        layout.addWidget(button_next, 2, 2)

        self.setLayout(layout)

    def next_page(self):
        self.parent.sensor_id = self.edit_sensor.text()
        if self.parent.sensor_id != "":
            try:
                doc = self.parent.get_componentinfo(self.parent.sensor_id)
            except Exception:
                QMessageBox.warning(
                    None, "Error", "Cannot get Sensor Tile information", QMessageBox.Ok
                )
            parents_list = doc["parents"]
            isAssembled = False
            if parents_list is not None:
                for parent in parents_list:
                    if (
                        parent["componentType"]["code"] == "BARE_MODULE"
                        and parent["history"][-1]["action"] == "assembly"
                    ):
                        isAssembled = True
                        QMessageBox.critical(
                            None,
                            "Error",
                            self.parent.sensor_id + " is already assembled.",
                            QMessageBox.Ok,
                        )
            else:
                if not isAssembled:
                    self.parent.assemble_sensor()
                    self.parent.choose_menu()
        else:
            QMessageBox.warning(None, "Warning", "Input Sensor ID", QMessageBox.Ok)

    def back_page(self):
        self.parent.feinfo()

    def skip_page(self):
        self.parent.choose_menu()
