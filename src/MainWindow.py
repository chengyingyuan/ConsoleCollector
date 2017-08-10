import sys, os
from PyQt5.QtCore import Qt, QEvent, QTimer, QCoreApplication
from PyQt5.QtWidgets import QMainWindow, QApplication, QMenu, QToolButton, QTabBar, QWidget
from PyQt5.QtWidgets import QGridLayout, QTextEdit, QAction
from PyQt5.QtGui import QIcon, QTextCursor
from Ui_MainWindow import Ui_MainWindow
from ConsoleProcess import ConsoleProcessThread
from ConsoleProcess import STOPPED, STARTING, RUNNING, KILLING, ERROR

TIMER_INTERVAL = 20 # Milliseconds

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self._config = config
        self._showStatusBar = True
        self._fullScreen = False
        self.initConsoles()
        
        # Prepare state icons
        prefix = os.path.realpath(os.path.dirname(__file__) + '\\..\\data\\images')
        stateIconsPath = { STOPPED:(prefix+'\\ProcessStopped.png'), 
                          STARTING:(prefix+'\\ProcessStarting.png'),
                          RUNNING:(prefix+'\\ProcessRunning.png'),
                          KILLING:(prefix+'\\ProcessKilling.png'),
                          ERROR:(prefix+'\\ProcessError.png')}
        self._stateIcons = {}
        for state, path in stateIconsPath.items():
            self._stateIcons[state] = QIcon(path)

        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)
        self.initUI()
        
        self._timer = QTimer()
        self._timer.timeout.connect(self.onTimeout)
        self._timer.start(TIMER_INTERVAL)
    
    def initConsoles(self):
        self._consoles = []
        for secName in self._config.sectionNames:
            section = self._config.getSection(secName)
            cmdline = section['CMDLINE']
            appname = self._config.get('APPNAME', secName)
            workdir = self._config.get('WORKDIR', secName)
            environ = self._config.getDict('ENVIRON', secName)
            encoding = self._config.get('ENCODING', secName)
            console = ConsoleProcessThread(secName, appname, cmdline, workdir, environ, encoding)
            self._consoles.append(console)
            console.start()
    
    def initUI(self):
        self.statusBar().showMessage('Ready')
        if self._config.AppMainWindowTitle:
            self.setWindowTitle(self._config.AppMainWindowTitle)
        if self._config.AppMainWindowIcon:
            self.setWindowIcon(QIcon(self._config.AppMainWindowIcon))
        
        self._ui.tabConsoles.clear()
        self._tabPages = []
        self._outputWidgets = []
        self._outputWidgetsCursor = []
        self._consolesState = []
        for i,console in enumerate(self._consoles):
            state = console.state
            tabPage = QWidget()
            tabPage.setObjectName("tabPage%s" % (i,))
            layout = QGridLayout(tabPage)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setObjectName("gridLayout")
            textBrowser = QTextEdit(tabPage)
            textBrowser.setObjectName("consoleOutput")
            #textBrowser.setReadOnly(True)
            layout.addWidget(textBrowser, 0, 0, 1, 1)
            self._ui.tabConsoles.addTab(tabPage, self._stateIcons[state], console.title)
            self._tabPages.append(tabPage)
            self._outputWidgets.append(textBrowser)
            self._outputWidgetsCursor.append(textBrowser.textCursor())
            self._consolesState.append(state)
            textBrowser.installEventFilter(self)
        
        self._tabBar = self._ui.tabConsoles.tabBar()
        self._tabBar.installEventFilter(self)
        
        self._tabBarMenu = QMenu(self)
        action = QAction("启动(&S)", self)
        action.triggered.connect(self.onStart)
        self._actionStart = action
        self._tabBarMenu.addAction(action)
        action = QAction("停止(&K)", self)
        action.triggered.connect(self.onKill)
        self._tabBarMenu.addAction(action)
        self._actionKill = action
        action = QAction("重启(&R)", self)
        action.triggered.connect(self.onRestart)
        self._tabBarMenu.addAction(action)
        self._actionRestart = action
        self._tabBarMenuIndex = -1 # Not triggered

        self._ui.actionExit.triggered.connect(self.onExit)
        self._ui.actionStartAll.triggered.connect(self.onStartAll)
        self._ui.actionKillAll.triggered.connect(self.onKillAll)
        self._ui.actionRestartAll.triggered.connect(self.onRestartAll)
        self._ui.actionShowHideStatus.triggered.connect(self.onShowHideStatus)
        self._ui.actionFullScreen.triggered.connect(self.onFullScreen)
        self._ui.actionAbout.triggered.connect(self.onAbout)

        self.show()
    
    def eventFilter(self, target, event):
        tabBar = self._ui.tabConsoles.tabBar()
        if target == tabBar:
            if event.type() == QEvent.MouseButtonRelease: # QMouseEvent
                if event.button() == Qt.RightButton: 
                    self._tabBarMenuIndex = tabBar.tabAt(event.pos())
                    self._actionStart.setEnabled(False)
                    self._actionKill.setEnabled(False)
                    self._actionRestart.setEnabled(False)
                    console = self._consoles[self._tabBarMenuIndex]
                    if console.state in [STOPPED, ERROR]:
                        self._actionStart.setEnabled(True)
                    elif console.state in [RUNNING,]:
                        self._actionKill.setEnabled(True)
                        self._actionRestart.setEnabled(True)
                    self._tabBarMenu.exec(event.globalPos())
        elif target == self._outputWidgets[self._ui.tabConsoles.currentIndex()]:
            tabIndex = self._ui.tabConsoles.currentIndex()
            if event.type() == QEvent.KeyRelease: # QKeyEvent
                text = event.text() # event.key() without Shift/Control/Alt/Meta considered
                console = self._consoles[tabIndex]
                try:
                    tstr = text.encode('UTF-8')
                    console.putInput(tstr)
                except:
                    pass
                event.ignore()
                return True # Filter the event out
            elif event.type() == QEvent.KeyPress:
                event.ignore()
                return True # Filter the event out
        return QMainWindow.eventFilter(self, target, event)
    
    def closeEvent(self, event):
        print("Closing...")
        for console in self._consoles:
            console.stop()
        for console in self._consoles:
            print("Joining console {}".format(console.appId))
            console.join()
        super().closeEvent(event)
        #QCoreApplication.instance().quit()
    
    def onTimeout(self):
        maxCharCount = int(self._config.AppConsoleMaxSize)
        minCharCount = int(maxCharCount/4.0)
        for i, console in enumerate(self._consoles):
            state = console.state
            if state != self._consolesState[i]:
                self._ui.tabConsoles.setTabIcon(i, self._stateIcons[state])
                self._consolesState[i] = state
            text = console.getOutput()
            if text:
                textBrowser = self._outputWidgets[i]
                textCursor = self._outputWidgetsCursor[i]
                #cursor = textBrowser.textCursor()
                #textBrowser.append(text.decode('UTF-8'))
                textBrowser.setTextCursor(textCursor)
                try:
                    tstr = text.decode('UTF-8')
                    textBrowser.insertPlainText(tstr)
                except:
                    pass
                charCount = textBrowser.document().characterCount()
                if charCount > maxCharCount:
                    text = textBrowser.toPlainText()
                    textBrowser.clear()
                    textBrowser.insertPlainText(text[(charCount-minCharCount):])
                self._outputWidgetsCursor[i] = textBrowser.textCursor()
 
    def onExit(self):
        self.close()
    
    def onStartAll(self):
        for i in range(len(self._consoles)):
            self._tabBarMenuIndex = i
            self.onStart()
    
    def onKillAll(self):
        for i in range(len(self._consoles)):
            self._tabBarMenuIndex = i
            self.onKill()
    
    def onRestartAll(self):
        for i in range(len(self._consoles)):
            self._tabBarMenuIndex = i
            self.onRestart()
    
    def onStart(self):
        console = self._consoles[self._tabBarMenuIndex]
        console.requestStart()
    
    def onKill(self):
        console = self._consoles[self._tabBarMenuIndex]
        console.requestKill()
    
    def onRestart(self):
        console = self._consoles[self._tabBarMenuIndex]
        console.requestRestart()
    
    def onShowHideStatus(self):
        self._showStatusBar = not self._showStatusBar
        if self._showStatusBar:
            self.statusBar().show()
        else:
            self.statusBar().hide()
    
    def onFullScreen(self):
        if self._fullScreen:
            self.showNormal()
        else:
            self.showFullScreen()
        self._fullScreen = not self._fullScreen
    
    def onAbout(self):
        pass
