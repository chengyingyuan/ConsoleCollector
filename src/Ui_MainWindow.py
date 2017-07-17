# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\MainWindow.ui'
#
# Created by: PyQt5 UI code generator 5.7.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(771, 506)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.tabConsoles = QtWidgets.QTabWidget(self.centralwidget)
        self.tabConsoles.setObjectName("tabConsoles")
        self.tabConsole1 = QtWidgets.QWidget()
        self.tabConsole1.setObjectName("tabConsole1")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tabConsole1)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.console1Output = QtWidgets.QTextBrowser(self.tabConsole1)
        self.console1Output.setObjectName("console1Output")
        self.gridLayout_2.addWidget(self.console1Output, 0, 0, 1, 1)
        self.tabConsoles.addTab(self.tabConsole1, "")
        self.tabConsole2 = QtWidgets.QWidget()
        self.tabConsole2.setObjectName("tabConsole2")
        self.tabConsoles.addTab(self.tabConsole2, "")
        self.gridLayout.addWidget(self.tabConsoles, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 771, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuControl = QtWidgets.QMenu(self.menubar)
        self.menuControl.setObjectName("menuControl")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.menuView = QtWidgets.QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionStartAll = QtWidgets.QAction(MainWindow)
        self.actionStartAll.setObjectName("actionStartAll")
        self.actionKillAll = QtWidgets.QAction(MainWindow)
        self.actionKillAll.setObjectName("actionKillAll")
        self.actionRestartAll = QtWidgets.QAction(MainWindow)
        self.actionRestartAll.setObjectName("actionRestartAll")
        self.actionAbout = QtWidgets.QAction(MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.actionShowHideStatus = QtWidgets.QAction(MainWindow)
        self.actionShowHideStatus.setObjectName("actionShowHideStatus")
        self.actionFullScreen = QtWidgets.QAction(MainWindow)
        self.actionFullScreen.setObjectName("actionFullScreen")
        self.menuFile.addAction(self.actionExit)
        self.menuControl.addAction(self.actionStartAll)
        self.menuControl.addAction(self.actionKillAll)
        self.menuControl.addAction(self.actionRestartAll)
        self.menuHelp.addAction(self.actionAbout)
        self.menuView.addAction(self.actionShowHideStatus)
        self.menuView.addAction(self.actionFullScreen)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuControl.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        self.tabConsoles.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.tabConsoles.setTabText(self.tabConsoles.indexOf(self.tabConsole1), _translate("MainWindow", "Tab 1"))
        self.tabConsoles.setTabText(self.tabConsoles.indexOf(self.tabConsole2), _translate("MainWindow", "Tab 2"))
        self.menuFile.setTitle(_translate("MainWindow", "文件(&F)"))
        self.menuControl.setTitle(_translate("MainWindow", "控制(&C)"))
        self.menuHelp.setTitle(_translate("MainWindow", "帮助(&H)"))
        self.menuView.setTitle(_translate("MainWindow", "视图(&V)"))
        self.actionExit.setText(_translate("MainWindow", "退出(&X)"))
        self.actionExit.setIconText(_translate("MainWindow", "退出"))
        self.actionExit.setToolTip(_translate("MainWindow", "退出程序"))
        self.actionExit.setStatusTip(_translate("MainWindow", "退出程序"))
        self.actionExit.setShortcut(_translate("MainWindow", "Ctrl+X"))
        self.actionStartAll.setText(_translate("MainWindow", "全部启动(&S)"))
        self.actionStartAll.setShortcut(_translate("MainWindow", "Ctrl+S"))
        self.actionKillAll.setText(_translate("MainWindow", "全部终止(&K)"))
        self.actionKillAll.setShortcut(_translate("MainWindow", "Ctrl+K"))
        self.actionRestartAll.setText(_translate("MainWindow", "全部重启(&R)"))
        self.actionRestartAll.setShortcut(_translate("MainWindow", "Ctrl+R"))
        self.actionAbout.setText(_translate("MainWindow", "关于(&A)"))
        self.actionAbout.setShortcut(_translate("MainWindow", "F1"))
        self.actionShowHideStatus.setText(_translate("MainWindow", "显示/隐藏状态栏(&S)"))
        self.actionFullScreen.setText(_translate("MainWindow", "全屏(&F)"))
        self.actionFullScreen.setShortcut(_translate("MainWindow", "Ctrl+F"))

