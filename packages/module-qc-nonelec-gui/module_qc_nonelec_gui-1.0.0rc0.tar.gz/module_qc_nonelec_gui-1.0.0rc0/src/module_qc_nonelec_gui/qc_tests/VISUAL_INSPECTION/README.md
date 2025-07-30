Supported OS

- Cent OS 7
- macOS 10.15.3

Required packages

- PyQt5
- OpenCV
- dbinterface [link](https://gitlab.cern.ch/sshirabe/dbinterface)
- local DB [link](https://localdb-docs.readthedocs.io/en/master/)

install PyQt5

    pip3 install PyQt5

install OpenCV

    pip3 install opencv-python

    pip3 install opencv-python==4.1.2.30 (for macOS)

install dbinterface

    git clone https://gitlab.cern.ch/sshirabe/dbinterface.git

**Quick Tutorial**

Setup

    mkdir Workdir

    cd Workdir

    git clone https://gitlab.cern.ch/sshirabe/dbinterface.git

    mkdir VisualInspection

    cd VisualInspection

    git clone https://gitlab.cern.ch/sshirabe/visualinspectionsoftware.git

Run VI GUI

    cd visualinspectionsoftware

    python3 bin/main.py

Need to prepare the golden module images under /Workdir/VisualInspeection.
Please unzip golden_module.zip and put unzipped directoru under
/Workdir/VisualInspeection.
