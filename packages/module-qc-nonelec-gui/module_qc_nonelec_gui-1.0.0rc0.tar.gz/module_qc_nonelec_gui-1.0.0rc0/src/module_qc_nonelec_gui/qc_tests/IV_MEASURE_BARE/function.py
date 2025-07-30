from __future__ import annotations

import copy
import json
import logging
import pprint
import sys
import traceback
from datetime import datetime
from importlib import machinery
from pathlib import Path

import pymongo
import requests
from bson.objectid import ObjectId
from PyQt5.QtWidgets import QMessageBox

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)


def get_sensor(self, component):
    ID = self.localDB.component.find_one({"serialNumber": component}, {"_id": 1})
    SN = None
    for i in self.localDB.childParentRelation.find({"parent": str(ID["_id"])}):
        child_id = i["child"]
        SN = self.localDB.component.find_one(
            {"componentType": "sensor_tile", "_id": ObjectId(child_id)},
            {"serialNumber": 1, "_id": 0},
        )
        if SN:
            return SN["serialNumber"]
    return None


def fill_info_sensor(self, number, info_dict_bare):
    info_dict_sen = copy.copy(info_dict_bare)
    component = self.localDB.component.find_one({"serialNumber": number})
    qcStatus = self.localDB.QC.module.status.find_one(
        {"component": str(component["_id"])}
    )
    qcStages = self.localDBtools.QC.stages.find_one({"code": "SENSOR_TILE"})

    info_dict_sen["component"] = number
    info_dict_sen["componentType"] = "SENSOR_TILE"
    info_dict_sen["FE_version"] = None
    info_dict_sen["stage"] = qcStatus["stage"]
    info_dict_sen["stageCode"] = qcStages["stages"].get(qcStatus["stage"])
    return info_dict_sen


def read_data(filename):
    volt = []
    curr = []
    cap = []
    D = []
    temp = []
    time = []
    with Path(filename).open(encoding="utf-8") as f:
        isDataLine = False
        isNew_dat = False
        lines = f.readlines()
        # for line in lines:
        #    if line[39:43] == "temp":
        #        isNew_dat = True
        for line in lines:
            if line[0:10] == "voltage[V]":
                isDataLine = True
                continue
            if isDataLine:
                rawdata = line.split(" ")
                if len(rawdata) == 7:
                    volt.append(float(rawdata[0]) * (-1))
                    curr.append(float(rawdata[1]) * (10**6) * (-1))
                    cap.append(float(rawdata[2]))
                    D.append(float(rawdata[3]))
                    temp.append(float(rawdata[4]))
                    timedata = rawdata[6].split()
                    time.append(timedata[0])
                elif len(rawdata) == 6:
                    volt.append(float(rawdata[0]) * (-1))
                    curr.append(float(rawdata[1]) * (10**6) * (-1))
                    cap.append(float(rawdata[2]))
                    D.append(float(rawdata[3]))
                    timedata = rawdata[5].split()
                    time.append(timedata[0])
            # if isDataLine and isNew_dat:
            #    rawdata = line.split(" ")
            #    volt.append(float(rawdata[0]) * (-1))
            #    curr.append(float(rawdata[1]) * (10**6) * (-1))
            #    cap.append(float(rawdata[2]))
            #    D.append(float(rawdata[3]))
            #    temp.append(float(rawdata[4]))
            #    timedata = rawdata[6].replace(":", "")
            #    time.append(float(timedata))

            # elif isDataLine and (not isNew_dat):
            #    rawdata = line.split(" ")
            #    volt.append(float(rawdata[0]) * (-1))
            #    curr.append(float(rawdata[1]) * (10**6) * (-1))
            #    cap.append(float(rawdata[2]))
            #    D.append(float(rawdata[3]))
            #    timedata = rawdata[5].replace(":", "")
            #    time.append(float(timedata))

    if not isNew_dat:
        temp = [20] * len(volt)
    base_time = datetime.strptime(time[0], "%H:%M:%S")
    pass_time = []
    for t in time:
        elapsed_time = (datetime.strptime(t, "%H:%M:%S") - base_time).total_seconds()
        pass_time.append(int(elapsed_time))

    data = {
        "voltage": volt,
        "current": curr,
        "cap": cap,
        "D": D,
        "temp": temp,
        "time": pass_time,
    }

    log.info(f"get from dat file : {data}")
    return data


def get_testRun(self, name, version, serialNumber):
    testRunFormat = self.localDBtools.QC.tests.find_one(
        {
            "code": "IV_MEASURE",
            "componentType.code": "SENSOR_TILE",
        }
    )
    testRun = {
        "serialNumber": name,
        "testType": "IV_MEASURE",
        "subtestType": "",
        "results": {
            "property": {prop["code"]: None for prop in testRunFormat["properties"]},
            "comment": "",
            "Metadata": {
                "QCHELPER_VERSION": version,
                "MODULE_SN": serialNumber,
                "Institution": "",
            },
            "Measurements": {},
        },
    }
    testRun.get("results").update(
        {param["code"]: None for param in testRunFormat["parameters"]}
    )
    return testRun


def receive_result_IV(MainWindow, InitialWindow):
    InitialWindow.hide()
    confirm_IV_result(MainWindow)


def confirm_IV_result(self):
    log.info("==========================================================")
    log.info("confirm_IV_result(): [results] sensor!!!")
    log.info(pprint.pformat(self.testRun_sen))
    log.info("==========================================================")

    try:
        test_confirm = "qc_tests/IV_MEASURE_BARE/confirm.py"

        log.info(f"test_confirm = {test_confirm}")

        test_confirm = str(Path(self.module_qc_nonelec_gui_dir) / test_confirm)
        log.info(f"test_confirm = {test_confirm}")

        self.confirm_module = machinery.SourceFileLoader(
            "confirm", test_confirm
        ).load_module()
        self.confirm_wid = self.confirm_module.ConfirmWindow(self)

        self.update_widget(self.confirm_wid)

    except Exception:
        log.exception(traceback.format_exc())
        try:
            test_confirm = Path(self.module_qc_nonelec_gui_dir).joinpath(
                "GUI", "lib", "ConfirmWindow", "default_layout;py"
            )
            self.confirm_module = machinery.SourceFileLoader(
                "default_layout", test_confirm
            ).load_module()
            self.confirm_wid = self.confirm_module.ConfirmWindow(self)
        except FileNotFoundError:
            log.exception(traceback.format_exc())
            QMessageBox.warning(
                None,
                "Warning",
                'Module: "default_layout.py" is not found',
                QMessageBox.Ok,
            )
    self.update_widget(self.confirm_wid)


def upload_to_db_IV(self):
    if self.isPractice:
        self.terminate_message()
        return None

    if self.isOK_to_upload:
        try:
            self.local_save()

            protocol = self.custom_conf.get("localDB_web").get("protocol", "http")
            host = self.custom_conf.get("localDB_web").get("address", "127.0.0.1")
            port = self.custom_conf.get("localDB_web").get("port", "5000")

            log.info(
                f"attempting to upload TestRun to LocalDB on {protocol}://{host}:{port}/localdb/ ..."
            )

            res = requests.post(
                f"{protocol}://{host}:{port}/localdb/qc_uploader_post",
                json=[[self.testRun_sen]],
                timeout=60,
            )
            log.info("... posted! response = " + str(res.text))
            out = json.loads(str(res.text))
            log.info(pprint.pformat(out))

            sen_Obj_id = self.localDB.QC.result.find_one(
                {
                    "testType": "IV_MEASURE",
                    "stage": "BAREMODULERECEPTION",
                    "serialNumber": self.testRun_sen["serialNumber"],
                },
                sort=[("_id", pymongo.DESCENDING)],
                projection={"_id": 1},
            )
            self.testRun["results"]["LINK_TO_SENSOR_IV_TEST"] = self.json_rule(
                sen_Obj_id["_id"]
            )

            return True

        except Exception:
            log.exception(traceback.format_exc())
            log.exception(str(res.text))
            QMessageBox.warning(
                None,
                "Warning",
                "ERROR: failed to upload result to DB:\n\n======================\n\n"
                + str(res.text),
                QMessageBox.Ok,
            )
            return False
    else:
        QMessageBox.warning(
            None,
            "Warning",
            "you can not have prepared to upload",
            QMessageBox.Ok,
        )
        return False
