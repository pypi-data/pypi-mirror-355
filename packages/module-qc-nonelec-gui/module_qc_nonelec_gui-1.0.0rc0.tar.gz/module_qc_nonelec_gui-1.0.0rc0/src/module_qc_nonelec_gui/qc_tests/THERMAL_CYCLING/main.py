from __future__ import annotations

from PyQt5.QtWidgets import QMainWindow

from module_qc_nonelec_gui.dbinterface import localdb_uploader
from module_qc_nonelec_gui.qc_tests.THERMAL_CYCLING import initial_Thermal


class TestWindow(QMainWindow):
    ############################################################################################
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__()
        self.parent = parent
        self.test_result_dict = None
        self.initial_wid = None

        self.setWindowTitle("Thermal Cycling")

        self.result_info = {
            "comment": "",
            "Machine": "",
            "Temp_log_path": "",
            "Humi_log_path": "",
            "Temp_min_value": "",
            "Temp_max_value": "",
            "Temp_unit": "degC",
            "N_cycle": "",
            "Cycle_speed_value": "",
            "Cycle_speed_unit": "K/min",
        }

    def receive_result(self, result):
        self.result_info["Machine"] = result["Machine"]
        self.result_info["Temp_log_path"] = result["Temp_log_path"]
        self.result_info["Humi_log_path"] = result["Humi_log_path"]
        self.result_info["Temp_min_value"] = result["Temp_min_value"]
        self.result_info["Temp_max_value"] = result["Temp_max_value"]
        self.result_info["N_cycle"] = result["N_cycle"]
        self.result_info["Cycle_speed_value"] = result["Cycle_speed_value"]
        self.result_info["comment"] = result["comment"]

        self.result_info["Temp_log"] = str(
            localdb_uploader.jpeg_formatter(
                self.parent.localDB, self.result_info["Temp_log_path"]
            )
        )
        self.result_info["Humi_log"] = str(
            localdb_uploader.jpeg_formatter(
                self.parent.localDB, self.result_info["Humi_log_path"]
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
                        "Temp_min_value": self.result_info["Temp_min_value"],
                        "Temp_max_value": self.result_info["Temp_max_value"],
                        "N_cycle": self.result_info["N_cycle"],
                        "Cycle_speed_value": self.result_info["Cycle_speed_value"],
                        "Cycle_speed_unit": self.result_info["Cycle_speed_unit"],
                    },
                    "Temperature_log": self.result_info["Temp_log"],
                    "Humidity_log": self.result_info["Humi_log"],
                    "Temp_unit": self.result_info["Temp_unit"],
                    "comment": self.result_info["comment"],
                },
                "ITkPD": {
                    "property": {
                        "Machine": self.result_info["Machine"],
                        "Temp_min_value": self.result_info["Temp_min_value"],
                        "Temp_max_value": self.result_info["Temp_max_value"],
                        "N_cycle": self.result_info["N_cycle"],
                        "Cycle_speed_value": self.result_info["Cycle_speed_value"],
                        "Cycle_speed_unit": self.result_info["Cycle_speed_unit"],
                    },
                    "Temperature_log": self.result_info["Temp_log"],
                    "Humidity_log": self.result_info["Humi_log"],
                    "Temp_unit": self.result_info["Temp_unit"],
                    "comment": self.result_info["comment"],
                },
                "summary": {
                    "property": {
                        "Machine": self.result_info["Machine"],
                        "Temp_min_value": self.result_info["Temp_min_value"],
                        "Temp_max_value": self.result_info["Temp_max_value"],
                        "N_cycle": self.result_info["N_cycle"],
                        "Cycle_speed_value": self.result_info["Cycle_speed_value"],
                        "Cycle_speed_unit": self.result_info["Cycle_speed_unit"],
                    },
                    "Temperature_log": self.result_info["Temp_log"],
                    "Humidity_log": self.result_info["Humi_log"],
                    "Temp_log_path": self.result_info["Temp_log_path"],
                    "Humi_log_path": self.result_info["Humi_log_path"],
                    "Temp_unit": self.result_info["Temp_unit"],
                    "comment": self.result_info["comment"],
                },
            }
        }

    ###########################################################################################

    def init_ui(self):
        self.initial_wid = initial_Thermal.InitialWindow(self)
        self.parent.update_widget(self.initial_wid)

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
