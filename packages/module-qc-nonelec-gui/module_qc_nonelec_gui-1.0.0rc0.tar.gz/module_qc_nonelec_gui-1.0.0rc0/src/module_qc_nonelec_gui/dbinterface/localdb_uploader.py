from __future__ import annotations

import logging
from pathlib import Path

import gridfs

log = logging.getLogger(__name__)


def jpeg_formatter(localdb, path):
    fs = gridfs.GridFS(localdb)
    with Path(path).open(mode="rb") as f:
        binary = f.read()
    return fs.put(binary)
