from __future__ import annotations

import json
import logging
from pathlib import Path

from PyQt5.QtWidgets import QMainWindow

from module_qc_nonelec_gui.qc_tests.FLATNESS import user_input

log = logging.getLogger(__name__)


class TestWindow(QMainWindow):
    ############################################################################################
    def __init__(self, parent=None):
        #        super(QMainWindow, self).__init__(parent)
        super(QMainWindow, self).__init__()
        self.parent = parent

        self.setGeometry(0, 0, 510, 255)

        self.result_info = {
            "BACKSIDE_FLATNESS": "",
            "ANGLES": "",
            "comment": "",
            "filename": "",
        }

        # self.componentType = "MODULE"
        # self.stage = "MODULE"
        self.componentType = "BARE_MODULE"
        self.stage = "BAREMODULERECEPTION"

        self.init_ui()

    def receive_result(self, comment):
        with Path(self.result_info["filename"]).open(encoding="utf-8") as f:
            result_dict = json.load(f)

        params = [param["code"] for param in self.parent.testRunFormat["parameters"]]

        self.parent.testRun["results"]["Metadata"].update(
            {k: v for k, v in result_dict.items() if k not in params}
        )

        def unitOf(param):
            u = "um"
            if param == "BACKSIDE_FLATNESS":
                u = "um"
            elif param == "ANGLES":
                u = "deg"
            return u

        results = result_dict["results"]
        for param in params:
            if param not in results:
                continue
            self.parent.testRun["results"]["Measurements"][param] = {
                "X": False,
                "Unit": unitOf(param),
                "Values": (
                    results[param]
                    if isinstance(results[param], list)
                    else [results[param]]
                ),
            }

        self.parent.testRun["results"]["comment"] = comment

        self.parent.receive_result(self)

    ############################################################################################
    def init_ui(self):
        self.user_input_wid = user_input.InitialWindow(self)
        self.parent.update_widget(self.user_input_wid)

    def close_and_return(self):
        self.close()
        self.parent.back_from_test()

    def back_page(self):
        self.parent.init_ui()

    def call_another_window(self, window):
        self.hide()
        window.init_ui()
