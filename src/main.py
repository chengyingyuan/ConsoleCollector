# -*- coding: utf-8 -*-
#

import sys, os
sys.path.append(os.path.realpath(os.path.dirname(__file__)))
import ctypes
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication
from PyQt5.QtGui import QIcon
from MainWindow import MainWindow
from SmartConfig import SmartConfig
import logging


def main():
    loglevel = logging.DEBUG
    logdatefmt = "%Y-%m-%d %H:%M:%S"
    logfmt = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s"
    logging.basicConfig(format=logfmt, level=loglevel, datefmt=logdatefmt)

    if len(sys.argv) != 2:
        print("USAGE: ConsoleCollector.py <config-file>", file=sys.stderr)
        sys.exit(-1)
    configfile = sys.argv[1]
    config = SmartConfig(configfile, encoding='UTF-8')
    if not config.valid:
        print("Config file {} not valid: {}".format(configfile, config.errstring))
        sys.exit(-1)
    app = QApplication(sys.argv)
    if config.AppWindowIcon:
        app.setWindowIcon(QIcon(config.AppWindowIcon))
    if config.AppUserModelID:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(config.AppUserModelID)
    mainWnd = MainWindow(config)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
