from __future__ import annotations

from PyQt5.QtWidgets import QMainWindow

from module_qc_nonelec_gui.dbinterface import localdb_uploader
from module_qc_nonelec_gui.qc_tests.wirebonding_info import initial_Wire_info


class TestWindow(QMainWindow):
    ############################################################################################
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__()
        self.parent = parent
        self.initial_wid = None
        self.test_result_dict = None

        self.setWindowTitle("Wirebonding information")

        self.result_info = {
            "Institutions": self.parent.institute_dict,
            "comment": "",
            "Machine": "",
            "Operator": "",
            "Institution_of_operator": "",
            "batch": "TBA",
            "program": "",
            "program_path": "",
            "jig": "",
            "Temp_value": "",
            "Temp_unit": "degC",
            "Humidity_value": "",
            "Humidity_unit": "%RH",
        }

    def receive_result(self, result):
        self.result_info["Machine"] = result["Machine"]
        self.result_info["Operator"] = result["Operator"]
        self.result_info["Institution_of_operator"] = result["Institution_of_operator"]
        self.result_info["batch"] = result["batch"]
        self.result_info["jig"] = result["jig"]
        self.result_info["program_path"] = result["program_path"]
        self.result_info["Temp_value"] = result["Temp_value"]
        self.result_info["Humidity_value"] = result["Humidity_value"]
        self.result_info["comment"] = result["comment"]

        self.result_info["program"] = str(
            localdb_uploader.jpeg_formatter(
                self.parent.localDB, self.result_info["program_path"]
            )
        )

        self.fill_result()
        self.return_result()

    def fill_result(self):
        self.test_result_dict = {
            "results": {
                "localDB": {
                    "property": {
                        "Machine": self.result_info["Machine"],
                        "Operator_name": self.result_info["Operator"],
                        "Institution_of_operator": self.result_info[
                            "Institution_of_operator"
                        ],
                        "Bond_wire_batch": self.result_info["batch"],
                        "Bond_program": self.result_info["program"],
                        "Bonding_jig": self.result_info["jig"],
                    },
                    "Temperature": self.result_info["Temp_value"],
                    "Temperature_unit": self.result_info["Temp_unit"],
                    "Humidity": self.result_info["Humidity_value"],
                    "Humidity_unit": self.result_info["Humidity_unit"],
                    "comment": self.result_info["comment"],
                },
                "ITkPD": {
                    "property": {
                        "Machine": self.result_info["Machine"],
                        "Operator_name": self.result_info["Operator"],
                        "Institution_of_operator": self.result_info[
                            "Institution_of_operator"
                        ],
                        "Bond_wire_batch": self.result_info["batch"],
                        "Bond_program": self.result_info["program"],
                        "Bonding_jig": self.result_info["jig"],
                    },
                    "Temperature": self.result_info["Temp_value"],
                    "Temperature_unit": self.result_info["Temp_unit"],
                    "Humidity": self.result_info["Humidity_value"],
                    "Humidity_unit": self.result_info["Humidity_unit"],
                    "comment": self.result_info["comment"],
                },
                "summary": {
                    "property": {
                        "Machine": self.result_info["Machine"],
                        "Operator_name": self.result_info["Operator"],
                        "Institution_of_operator": self.result_info[
                            "Institution_of_operator"
                        ],
                        "Bond_wire_batch": self.result_info["batch"],
                        "Bond_program": self.result_info["program"],
                        "Bond_program_path": self.result_info["program_path"],
                        "Bonding_jig": self.result_info["jig"],
                    },
                    "Temperature": self.result_info["Temp_value"],
                    "Temperature_unit": self.result_info["Temp_unit"],
                    "Humidity": self.result_info["Humidity_value"],
                    "Humidity_unit": self.result_info["Humidity_unit"],
                    "comment": self.result_info["comment"],
                },
            }
        }

    ###########################################################################################

    def init_ui(self):
        self.initial_wid = initial_Wire_info.InitialWindow(self)
        self.update_widget(self.initial_wid)

    def scale_window(self, x, y):
        self.setGeometry(0, 0, x, y)

    def update_widget(self, w):
        self.scale_window(480, 360)
        self.setCentralWidget(w)
        self.show()

    def close_and_return(self):
        self.close()
        self.parent.back_from_test()

    def back_page(self):
        self.parent.init_ui()

    def call_another_window(self, window):
        self.hide()
        window.init_ui()

    def return_result(self):
        self.parent.receive_result(self, self.test_result_dict)
