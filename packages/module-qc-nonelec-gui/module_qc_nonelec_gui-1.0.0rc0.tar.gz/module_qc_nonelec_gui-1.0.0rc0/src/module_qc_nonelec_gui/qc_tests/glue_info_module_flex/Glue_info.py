from __future__ import annotations

import logging

from PyQt5.QtWidgets import QMainWindow

from module_qc_nonelec_gui.qc_tests.glue_info_module_flex import initial_Glue_info

log = logging.getLogger(__name__)


class TestWindow(QMainWindow):
    ############################################################################################
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__()
        self.parent = parent
        self.test_result_dict = None
        self.initial_wid = None

        self.setWindowTitle("Glue information Module Flex Attach")

        self.result_info = {
            "comment": "",
            "glue_name": "Araldite 2011",
            "ratio": "A:1,B:1",
            "batch": "TBA",
            "Temp_value": "",
            "Temp_unit": "degC",
            "Humidity_value": "",
            "Humidity_unit": "%RH",
            "adhesion": {"day": 0, "hour": 10, "minute": 0, "second": 0},
        }

    def receive_result(self, result):
        self.result_info["glue_name"] = result["glue_name"]
        self.result_info["ratio"] = result["ratio"]
        self.result_info["batch"] = result["batch"]
        self.result_info["Temp_value"] = result["Temp_value"]
        self.result_info["Humidity_value"] = result["Humidity_value"]
        #        self.result_info['adhesion']['day']    = result['adhesion']['day']
        #        self.result_info['adhesion']['hour']   = result['adhesion']['hour']
        #        self.result_info['adhesion']['minute'] = result['adhesion']['minute']
        #        self.result_info['adhesion']['second'] = result['adhesion']['second']
        self.result_info["comment"] = result["comment"]

        self.fill_result()
        self.return_result()

    def fill_result(self):
        self.test_result_dict = {
            "results": {
                "localDB": {
                    "property": {
                        "Glue_name": self.result_info["glue_name"],
                        "Volume_ratio_of_glue_mixture": self.result_info["ratio"],
                        "Glue_batch_number": self.result_info["batch"],
                    },
                    "Room_temperature": self.result_info["Temp_value"],
                    "Temperature_unit": self.result_info["Temp_unit"],
                    "Humidity": self.result_info["Humidity_value"],
                    "Humidity_unit": self.result_info["Humidity_unit"],
                    #                    'Adhesion_Time'    :self.result_info['adhesion'],
                    "comment": self.result_info["comment"],
                },
                "ITkPD": {
                    "property": {
                        "Glue_name": self.result_info["glue_name"],
                        "Volume_ratio_of_glue_mixture": self.result_info["ratio"],
                        "Glue_batch_number": self.result_info["batch"],
                    },
                    "Room_temperature": self.result_info["Temp_value"],
                    "Temperature_unit": self.result_info["Temp_unit"],
                    "Humidity": self.result_info["Humidity_value"],
                    "Humidity_unit": self.result_info["Humidity_unit"],
                    #                    'Adhesion_Time'    :self.result_info['adhesion'],
                    "comment": self.result_info["comment"],
                },
                "summary": {
                    "property": {
                        "Glue_name": self.result_info["glue_name"],
                        "Volume_ratio_of_glue_mixture": self.result_info["ratio"],
                        "Glue_batch_number": self.result_info["batch"],
                    },
                    "Room_temperature": self.result_info["Temp_value"],
                    "Temperature_unit": self.result_info["Temp_unit"],
                    "Humidity": self.result_info["Humidity_value"],
                    "Humidity_unit": self.result_info["Humidity_unit"],
                    #                    'Adhesion_Time'    :self.result_info['adhesion'],
                    "comment": self.result_info["comment"],
                },
            }
        }
        log.info(
            "[Test Result]  "
            + str(self.test_result_dict["results"]["localDB"]["property"]["Glue_name"])
        )

    ###########################################################################################

    def init_ui(self):
        self.initial_wid = initial_Glue_info.InitialWindow(self)
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
