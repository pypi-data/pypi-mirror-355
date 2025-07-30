from __future__ import annotations

import logging

from PyQt5.QtWidgets import QMainWindow

from module_qc_nonelec_gui.qc_tests.parylene_properties import initial_Parylene_prop

log = logging.getLogger(__name__)


class TestWindow(QMainWindow):
    ############################################################################################
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__()
        self.parent = parent
        self.initial_wid = None
        self.test_result_dict = None

        self.setWindowTitle("Parylene properties")

        self.result_info = {
            "Parylene_type_list": ["Type-N", "Type-C"],
            "Institution": self.parent.institute_dict,
            "comment": "",
            "batch": "TBA",
            "Parylene_type": "Type-N",
            "Name_of_Masking_Operator": "",
            "Institution_of_Masking_Operator": "",
            "Name_of_Operator_Removing_Mask": "",
            "Institution_of_Operator_Removing_Mask": "",
            "Parylene_thickness_measured_by_vendor": "",
            "Parylene_thickness_measured_by_ITk_Institute": "",
            "Thickness_unit": "um",
        }

    def receive_result(self, result):
        self.result_info["Parylene_type"] = result["Parylene_type"]
        self.result_info["batch"] = result["batch"]
        self.result_info["Name_of_Masking_Operator"] = result[
            "Name_of_Masking_Operator"
        ]
        self.result_info["Name_of_Operator_Removing_Mask"] = result[
            "Name_of_Operator_Removing_Mask"
        ]
        self.result_info["Institution_of_Masking_Operator"] = result[
            "Institution_of_Masking_Operator"
        ]
        self.result_info["Institution_of_Operator_Removing_Mask"] = result[
            "Institution_of_Operator_Removing_Mask"
        ]
        self.result_info["Parylene_thickness_measured_by_vendor"] = result[
            "Parylene_thickness_measured_by_vendor"
        ]
        self.result_info["Parylene_thickness_measured_by_ITk_Institute"] = result[
            "Parylene_thickness_measured_by_ITk_Institute"
        ]
        self.result_info["comment"] = result["comment"]

        self.fill_result()
        self.return_result()

    def fill_result(self):
        self.test_result_dict = {
            "results": {
                "localDB": {
                    "property": {
                        "Parylene_Type": self.result_info["Parylene_type"],
                        "Name_of_Masking_Operator": self.result_info[
                            "Name_of_Masking_Operator"
                        ],
                        "Name_of_Operator_Removing_Mask": self.result_info[
                            "Name_of_Operator_Removing_Mask"
                        ],
                        "Institution_of_Masking_Operator": self.result_info[
                            "Institution_of_Masking_Operator"
                        ],
                        "Institution_of_Operator_Removing_Mask": self.result_info[
                            "Institution_of_Operator_Removing_Mask"
                        ],
                        "Parylene_Batch_Number": self.result_info["batch"],
                    },
                    "Parylene_thickness_measured_by_vendor": self.result_info[
                        "Parylene_thickness_measured_by_vendor"
                    ],
                    "Parylene_thickness_measured_by_ITk_Institute": self.result_info[
                        "Parylene_thickness_measured_by_ITk_Institute"
                    ],
                    "Thickness_unit": self.result_info["Thickness_unit"],
                    "comment": self.result_info["comment"],
                },
                "ITkPD": {
                    "property": {
                        "Parylene_Type": self.result_info["Parylene_type"],
                        "Name_of_Masking_Operator": self.result_info[
                            "Name_of_Masking_Operator"
                        ],
                        "Name_of_Operator_Removing_Mask": self.result_info[
                            "Name_of_Operator_Removing_Mask"
                        ],
                        "Institution_of_Masking_Operator": self.result_info[
                            "Institution_of_Masking_Operator"
                        ],
                        "Institution_of_Operator_Removing_Mask": self.result_info[
                            "Institution_of_Operator_Removing_Mask"
                        ],
                        "Parylene_Batch_Number": self.result_info["batch"],
                    },
                    "Parylene_thickness_measured_by_vendor": self.result_info[
                        "Parylene_thickness_measured_by_vendor"
                    ],
                    "Parylene_thickness_measured_by_ITk_Institute": self.result_info[
                        "Parylene_thickness_measured_by_ITk_Institute"
                    ],
                    "Thickness_unit": self.result_info["Thickness_unit"],
                    "comment": self.result_info["comment"],
                },
                "summary": {
                    "property": {
                        "Parylene_Type": self.result_info["Parylene_type"],
                        "Name_of_Masking_Operator": self.result_info[
                            "Name_of_Masking_Operator"
                        ],
                        "Name_of_Operator_Removing_Mask": self.result_info[
                            "Name_of_Operator_Removing_Mask"
                        ],
                        "Institution_of_Masking_Operator": self.result_info[
                            "Institution_of_Masking_Operator"
                        ],
                        "Institution_of_Operator_Removing_Mask": self.result_info[
                            "Institution_of_Operator_Removing_Mask"
                        ],
                        "Parylene_Batch_Number": self.result_info["batch"],
                    },
                    "Parylene_thickness_measured_by_vendor": self.result_info[
                        "Parylene_thickness_measured_by_vendor"
                    ],
                    "Parylene_thickness_measured_by_ITk_Institute": self.result_info[
                        "Parylene_thickness_measured_by_ITk_Institute"
                    ],
                    "Thickness_unit": self.result_info["Thickness_unit"],
                    "comment": self.result_info["comment"],
                },
            }
        }
        log.info(
            "[Test Result]  "
            + str(
                self.test_result_dict["results"]["localDB"]["property"]["Parylene_Type"]
            )
        )

    ###########################################################################################

    def init_ui(self):
        self.initial_wid = initial_Parylene_prop.InitialWindow(self)
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
