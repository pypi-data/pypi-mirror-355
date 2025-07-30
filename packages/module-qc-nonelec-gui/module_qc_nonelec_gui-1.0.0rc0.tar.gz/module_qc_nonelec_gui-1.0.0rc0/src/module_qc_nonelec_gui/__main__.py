from __future__ import annotations

import sys

import typer
from PyQt5.QtWidgets import QApplication

from module_qc_nonelec_gui.cli import MainWindow


def main():
    typer.echo("Launching GUI")
    app = QApplication(sys.argv[1:])
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    typer.run(main)
