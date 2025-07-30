from __future__ import annotations

import logging
from pathlib import Path

import cv2
import defect_detection as dpa
import numpy as np

from module_qc_nonelec_gui.qc_tests.VISUAL_INSPECTION.functions.cv2_func import (
    img_cvt_rgb,
)

log = logging.getLogger(__name__)


def ML_unsup_scan(im, crop, model):
    """
    Function to apply the unsupervised automaic defect scan.

    Arguments :
        im : the input image in numpy array format
        crop : the croping edges of the applicable area
        model : the path to the ML model to be used

    Outputs :
        im_over : Defect cluster overlay corresponding to the input image
    """

    log.info("running usupervised scan")

    # For automatic device selection
    dev = "auto"
    # dev='cpu' #FIXME disable gpu for test
    log.info(f"use device {dev} for application")

    # Load data processing information
    with Path.open(model + "/data_process.json", "r") as f:
        config = eval(f.read())
    input_size = config["input_size"]
    Nseg = config["Nseg"]

    # Load ML model
    AE = dpa.deepAE_load(model)
    AE.to_dev(dev)
    AE.eval()

    # Load clustering config file
    with Path.open(model + "cluster.json", "r") as f:
        clparam = eval(f.read())
    pix_th = clparam["pix_th"]
    clparam.pop("pix_th")

    # Load selection thresholds
    with Path.open(model + "AE_threshold.txt", "r") as f:
        sel_th = eval(f.read())
    sel_th = np.mean(np.array(sel_th)) / 2  # TODO see if can be improved

    # Apply image preprocessing (crop/resize)
    log.info("prepare image")
    im_cr = im[crop[0] : crop[1], crop[2] : crop[3]]
    shape_ini = [im_cr.shape[0], im_cr.shape[1]]
    im_cr = cv2.resize(im_cr, (input_size * Nseg, input_size * Nseg))
    im_cr, _, _, _ = img_cvt_rgb(im_cr)

    # Initialize reco map
    emap = np.empty((im_cr.shape[0], im_cr.shape[1]))

    # Apply ML model
    log.info("apply ML model")
    for i in range(Nseg):
        for j in range(Nseg):
            im_seg = dpa.get_tensor(
                im_cr[
                    i * input_size : (i + 1) * input_size,
                    j * input_size : (j + 1) * input_size,
                ],
                dev,
            )
            im_rec = AE(im_seg)
            emap[
                i * input_size : (i + 1) * input_size,
                j * input_size : (j + 1) * input_size,
            ] = dpa.emap_mean(im_seg, im_rec)
            del im_seg
            del im_rec
    del AE

    # Apply filtering
    log.info("apply filtering")
    anom_cl = dpa.get_pixels(emap, sel_th, clparam, pix_th)

    # Generate anomaly clusters overlay
    log.info("generate defect overlay")
    over_cl = np.zeros((im_cr.shape[0], im_cr.shape[1], 4), dtype=im_cr.dtype)
    over_cl[:, :, 0][
        np.transpose(anom_cl)[0], np.transpose(anom_cl)[1]
    ] = 255  # red channel
    over_cl[:, :, 2][
        np.transpose(anom_cl)[0], np.transpose(anom_cl)[1]
    ] = 255  # blue channel
    over_cl[:, :, 3][
        np.transpose(anom_cl)[0], np.transpose(anom_cl)[1]
    ] = 255  # alpha channel (transparency)
    del im_cr

    # Resize cluster overlay image to original size
    over_cl = cv2.resize(over_cl, (shape_ini[1], shape_ini[0]))

    # Add padding to the overlay to match size before croping
    over_cl_full = np.zeros((im.shape[0], im.shape[1], 4), dtype=im.dtype)
    over_cl_full[crop[0] : crop[1], crop[2] : crop[3], 0] = over_cl[:, :, 0]
    over_cl_full[crop[0] : crop[1], crop[2] : crop[3], 2] = over_cl[:, :, 2]
    over_cl_full[crop[0] : crop[1], crop[2] : crop[3], 3] = over_cl[:, :, 3]
    del over_cl

    log.info("DONE")

    return over_cl_full
