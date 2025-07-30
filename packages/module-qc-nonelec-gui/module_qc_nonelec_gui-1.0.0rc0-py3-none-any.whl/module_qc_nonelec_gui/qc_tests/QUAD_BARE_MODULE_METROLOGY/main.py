from __future__ import annotations

import logging

from PyQt5.QtWidgets import QMainWindow

from module_qc_nonelec_gui.qc_tests.QUAD_BARE_MODULE_METROLOGY import initial_metrology

log = logging.getLogger(__name__)


class TestWindow(QMainWindow):
    ############################################################################################
    def __init__(self, parent=None):
        #        super(QMainWindow, self).__init__(parent)
        super(QMainWindow, self).__init__()
        self.parent = parent

        self.setGeometry(0, 0, 510, 255)

        self.result_info = {
            "comment": "",
            "filename": "",
        }

        self.componentType = "BARE_MODULE"
        self.stage = "BAREMODULERECEPTION"

        self.init_ui()

    def receive_result(self, _results):
        params = [param["code"] for param in self.parent.testRunFormat["parameters"]]

        self.parent.testRun["results"]["Metadata"].update(
            {k: v for k, v in _results.items() if k not in params}
        )
        for k, v in _results.get("results").items():
            self.parent.testRun.get("results").get("Measurements").update({k: v})

        results = _results["results"]
        for param in params:
            if param not in results:
                continue
            unit = "mm"
            if param.find("THICKNESS") >= 0:
                unit = "um"
            self.parent.testRun["results"]["Measurements"][param] = {
                "X": False,
                "Unit": unit,
                "Values": (
                    [round(x, 1) for x in results[param]]
                    if isinstance(results[param], list)
                    else [round(results[param], 1)]
                ),
            }
        self.parent.receive_result(self)

    ############################################################################################
    def init_ui(self):
        self.initial_bare_wid = initial_metrology.InitialWindow(self)
        self.parent.update_widget(self.initial_bare_wid)

    def close_and_return(self):
        self.close()
        self.parent.back_from_test()

    def back_page(self):
        self.parent.init_ui()

    def call_another_window(self, window):
        self.hide()
        window.init_ui()
