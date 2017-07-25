import win32process
import win32security
import win32pipe
import win32api
import win32con
import win32file
import threading
import queue
import time
import logging


STOPPED,STARTING,RUNNING,KILLING,ERROR = 0,1,2,3,4
STATES = {STOPPED:'STOPPED', STARTING:'STARTING', RUNNING:'RUNNING', 
    KILLING:'KILLING', ERROR:'ERROR'}
STATES_TITLE = {STOPPED:'S', STARTING:'RS', RUNNING:'R', KILLING:'RS', ERROR:'E'}
REQ_START, REQ_KILL = 0, 1
EVENT_INTERVAL = 0.02

class ChildReadThread(threading.Thread):
    """
    Anonymous pipe doesn't support timeout read. 
    A thread is needed for this situation.
    """
    def __init__(self, parentRead, target):
        super(ChildReadThread, self).__init__()
        self._parentRead = parentRead
        self._target = target
        self._cease = False
    
    def stop(self):
        self._cease = True
        
    def run(self):
        while not self._cease:
            try:
                hr, result = win32file.ReadFile(self._parentRead, 1, None)
                assert hr==0
                self._target.putOutput(result)
            except Exception as ex:
                msg = "WIN32API Error(ReadFile): {}".format(str(ex))
                level = logging.INFO if self._cease else logging.WARN
                self._target.showMessage(level, msg)
                break

class ConsoleProcessThread(threading.Thread):
    def __init__(self, appName, cmdLine, curDirectory=None, newEnvironment=None, encoding=None):
        super(ConsoleProcessThread, self).__init__()
        self._appName = appName
        self._cmdLine = cmdLine
        self._encoding = encoding
        self._curDirectory = curDirectory
        self._newEnvironment = newEnvironment
        
        self._queuein = queue.Queue()
        self._queueout = queue.Queue()
        self._queuereq = queue.Queue()
        self._state = STOPPED
        
        self._childRead = None
        self._childWrite = None
        self._parentRead = None
        self._parentWrite = None
        self._childProcess = None
        self._readThread = None

        self._cease = False
        self._sleep = True

    @property
    def appName(self):
        return self._appName
    
    @property
    def state(self):
        return self._state
    
    @property
    def title(self):
        return self.appName
    
    def stop(self):
        self._cease = True
    
    def requestStart(self):
        self.putToQueue(self._queuereq, REQ_START)
    
    def requestKill(self):
        self.putToQueue(self._queuereq, REQ_KILL)

    def requestRestart(self):
        self.putToQueue(self._queuereq, REQ_KILL)
        self.putToQueue(self._queuereq, REQ_START)
    
    def flushQueue(self, q):
        while not q.empty():
            try:
                q.get_nowait()
            except queue.Empty:
                break

    def putToQueue(self, q, v):
        q.put_nowait(v)

    def getInput(self):
        result = b''
        while not self._queuein.empty():
            try:
                item = self._queuein.get_nowait()
                result += item
            except queue.Empty:
                break
        return result

    def getOutput(self):
        result = b''
        while not self._queueout.empty():
            try:
                item = self._queueout.get_nowait()
                result += item
            except queue.Empty:
                break
        if result and self._encoding:
            result = result.decode(self._encoding).encode('UTF-8')
        return result
    
    def putInput(self, msg):
        self.putToQueue(self._queuein, msg)
    
    def putOutput(self, msg):
        self.putToQueue(self._queueout, msg)

    def showMessage(self, level, msg):
        self.putOutput(b'\n* ' + msg.encode('UTF-8')+b'\n')
        logging.log(level, "<{}> {}".format(self._appName, msg))

    def reset(self):
        self.termProcess()
        if self._childRead is not None:
            win32api.CloseHandle(self._childRead)
            self._childRead = None
        if self._childWrite is not None:
            win32api.CloseHandle(self._childWrite)
            self._childWrite = None
        if self._parentRead is not None:
            win32api.CloseHandle(self._parentRead)
            self._parentRead = None
        if self._parentWrite is not None:
            win32api.CloseHandle(self._parentWrite)
        if self._childProcess is not None:
            win32api.CloseHandle(self._childProcess)
            self._childProcess = None
        if self._readThread is not None:
            logging.info("Joining readThread")
            self._readThread.join()
            self._readThread = None
        self.flushQueue(self._queuein)
        self.flushQueue(self._queueout)
        self._state = STOPPED

    def isProcessAlive(self):
        if not self._childProcess:
            return False
        try:
            dwCode = win32process.GetExitCodeProcess(self._childProcess)
            if dwCode == win32con.STILL_ACTIVE:
                return True
            return False
        except Exception as ex:
            msg = "WIN32API Error(GetExitCode): {}".format(str(ex))
            self.showMessage(logging.ERROR, msg)
        return None

    def termProcess(self):
        if not self.isProcessAlive():
            return True
        try:
            self.showMessage(logging.INFO, "Terminating process...")
            win32process.TerminateProcess(self._childProcess, 0)
            if self._readThread:
                self.showMessage(logging.INFO, "Stopping ChildReadThread")
                self.stopReadThread()
            while self.isProcessAlive():
                time.sleep(EVENT_INTERVAL)
            self._childProcess = None
            return True
        except Exception as ex:
            self.showMessage(logging.ERROR, "Failed terminating: {}".format(str(ex)))
        return False
    
    def startProcess(self):
        assert self._state==STOPPED or self._state==ERROR
        self.reset()
        try:
            self._state = STARTING
            self.showMessage(logging.INFO, "Starting process, state => STARTING")
            # Prepare pipe for child stdin/stdout/stderr
            saAttr = win32security.SECURITY_ATTRIBUTES()
            saAttr.bInheritHandle = True
            saAttr.SECURITY_DESCRIPTOR = None
            self._childRead, self._parentWrite = win32pipe.CreatePipe(saAttr, 0)
            win32api.SetHandleInformation(self._parentWrite, win32con.HANDLE_FLAG_INHERIT, 0)
            self._parentRead, self._childWrite = win32pipe.CreatePipe(saAttr, 0)
            win32api.SetHandleInformation(self._parentRead, win32con.HANDLE_FLAG_INHERIT, 0)
            
            startupInfo = win32process.STARTUPINFO()
            startupInfo.hStdInput = self._childRead
            startupInfo.hStdOutput = self._childWrite
            startupInfo.hStdError = self._childWrite
            startupInfo.dwFlags = win32con.STARTF_USESTDHANDLES|win32con.STARTF_USESHOWWINDOW
            dwCreationFlags = 0        
            self._childProcess, hThread,_dwProcessId,_dwThreadId = win32process.CreateProcess(
                None,
                self._cmdLine, 
                None, # processAttributes
                None, # threadAttributes
                True, # bInheritHandles
                dwCreationFlags,
                self._newEnvironment,
                self._curDirectory,
                startupInfo
                )
            win32api.CloseHandle(hThread)
            self._readThread = ChildReadThread(self._parentRead, self)
            self._readThread.start()
            return True
        except Exception as ex:
            msg = "WIN32API Error(CreateProcess): {}".format(str(ex))
            self.showMessage(logging.ERROR, msg)
            self._state = ERROR
            self.showMessage(logging.INFO, "Error starting, state => ERROR")
        return False
    
    def killProcess(self):
        assert self._state==RUNNING
        try:
            self._state= KILLING
            self.showMessage(logging.INFO, "Killing process, state => KILLING")
            win32process.TerminateProcess(self._childProcess, 0)
            self.stopReadThread()
            return True
        except Exception as ex:
            msg = "WIN32API Error(TerminateProcess): {}".format(str(ex))
            self.showMessage(logging.ERROR, msg)
            self._state = ERROR
            self.showMessage(logging.INFO, "Error killing, state => ERROR")
        return False
    
    def checkStateStarting(self):
        result = self.isProcessAlive()
        if result is None:
            self._state = ERROR
            self.showMessage(logging.ERROR, "Alive checking error, state => ERROR")
            return False
        if result:
            self._state = RUNNING
            self.showMessage(logging.INFO, "Process alive, state => RUNNING")
        else:
            self._state= STOPPED
            self.showMessage(logging.INFO, "Process exited, state => STOPPED")
        return True
    
    def checkStateKilling(self):
        result = self.isProcessAlive()
        if result is None:
            self._state = ERROR
            self.showMessage(logging.ERROR, "Alive checking error, state => ERROR")
            return False
        if not result:
            self._state = STOPPED
            self.showMessage(logging.ERROR, "Killing OK, state => STOPPED")
        return True
    
    def writeToChild(self, msg, echo=True):
        while msg:
            try:
                _errCode, nBytesWritten = win32file.WriteFile(self._parentWrite, msg, None)
                if echo:
                    self.putOutput(msg[0:nBytesWritten])
                msg = msg[nBytesWritten:]
            except Exception as ex:
                msg = "WIN32API Error(WriteFile): {}".format(str(ex))
                self.showMessage(logging.ERROR, msg)
                return False
        return True

    def stopReadThread(self):
        if (not self._readThread) or (not self._readThread.isAlive()):
            return True
        try:
            self._readThread.stop()
            _errCode, nBytesWritten = win32file.WriteFile(self._childWrite, b' ', None)
            self._readThread.join()
            self._readThread = None
            return True
        except Exception as ex:
            msg = "WIN32API Error(WriteFile): {}".format(str(ex))
            self.showMessage(logging.ERROR, msg)
        return False
    
    def checkStateRunning(self):
        result = self.isProcessAlive()
        if result is None:
            self._state = ERROR
            self.showMessage(logging.ERROR, "Alive checking error, state => ERROR")
            return False
        if not result:
            self._state = STOPPED
            self.showMessage(logging.INFO, "Process done, state => STOPPED")
            return True
        msg = self.getInput()
        if msg:
            if not self.writeToChild(msg):
                self._state = ERROR
                self.showMessage(logging.ERROR, "Error write child, state => ERROR")
                return False
            self._sleep = False # User is typing something
        if not self._readThread.isAlive():
            self._state = ERROR
            self.showMessage(logging.ERROR, "Error read child, state => ERROR")
            return False
        return True
    
    def run(self):
        while not self._cease:
            self._sleep = True
            if self._state==STARTING:
                self.checkStateStarting()
            elif self._state==KILLING:
                self.checkStateKilling()
            else: # state RUNNING, STOPPED, ERROR
                try:
                    action = self._queuereq.get_nowait()
                    if action == REQ_START:
                        if self._state == RUNNING:
                            self.showMessage(logging.WARN, "Process already started")
                        else:
                            self.startProcess()
                    elif action == REQ_KILL:
                        if self._state in [ERROR, STOPPED]:
                            self.showMessage(logging.WARN, "Process not started")
                        else:
                            self.killProcess()
                    else:
                        assert False
                except queue.Empty:
                    pass
                if self._state==RUNNING:
                    self.checkStateRunning()
            if self._sleep:
                time.sleep(EVENT_INTERVAL)
        self.showMessage(logging.INFO, "Stopping ConsoleProcessThread")
        self.reset()
        self.showMessage(logging.INFO, "Stopped ConsoleProcessThread")
