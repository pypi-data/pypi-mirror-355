from __future__ import annotations

import hashlib
import logging

from pymongo import MongoClient

log = logging.getLogger(__name__)


def connectDB(address="127.0.0.1", port="27017", username="", password=""):
    url = f"mongodb://{address}:{port}/"
    client = MongoClient(url)
    localdb = client["localdb"]
    localdbtools = client["localdbtools"]

    user_doc = localdbtools.viewer.user.find_one({"username": username})
    if user_doc.get("password") == "":
        return localdb, localdbtools

    if hashlib.md5(password.encode("utf-8")).hexdigest() == user_doc.get("password"):
        log.info("[connectDB]: Successful LocalDB Viewer Authentication!")
        return localdb, localdbtools

    msg = "[connectDB]: Authentication Failed"
    raise Exception(msg)
