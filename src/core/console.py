'''Console output'''

#Constants.
LOG_LEVEL_MINIMUM = -1
LOG_LEVEL_WARNING = 0
LOG_LEVEL_DEBUG = 1
import platform
import time
from threading import Lock
from sys import stdout
if platform.system() == 'Windows':
    #Windows colour stuff...
    ENABLE_COLOUR = True
    import ctypes
    STD_OUTPUT_HANDLE = -11
    FOREGROUND_BLUE = 0x01 # text color contains blue.
    FOREGROUND_GREEN = 0x02 # text color contains green.
    FOREGROUND_RED = 0x04 # text color contains red.
    FOREGROUND_INTENSITY = 0x08 # text color is intensified.
    BACKGROUND_BLUE = 0x10 # background color contains blue.
    BACKGROUND_GREEN = 0x20 # background color contains green.
    BACKGROUND_RED = 0x40 # background color contains red.
    BACKGROUND_INTENSITY = 0x80 # background color is intensified.
    TRED = FOREGROUND_RED | FOREGROUND_INTENSITY
    TGREEN = FOREGROUND_GREEN | FOREGROUND_INTENSITY
    TYELLOW = FOREGROUND_GREEN | FOREGROUND_RED | FOREGROUND_INTENSITY
    TNORMAL = FOREGROUND_GREEN | FOREGROUND_RED | 0x01
    TWHITE = TNORMAL | FOREGROUND_INTENSITY
    TBLUE = FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY

elif platform.system() == 'Linux' or platform.system() == 'Darwin':
    #Unix ANSI Colour codes
    ENABLE_COLOUR = True
    TRED = "\033[22;31m"
    TGREEN = "\033[01;32m"
    TYELLOW = "\033[01;33m"
    TNORMAL = "\033[22;37m"
    TWHITE = "\033[1;37m"
    TBLUE = "\033[1;36m"
else:
    #Unsure if this platform supports ANSI colour codes, so lets assume not.
    ENABLE_COLOUR = False
    TRED = 0
    TGREEN = 0
    TYELLOW = 0
    TNORMAL = 0
    TWHITE = 0
    TBLUE = 0

class OConsole(object):
    '''Class for Console in opticraft'''
    def __init__(self):
        self.LogLevel = LOG_LEVEL_WARNING
        self.Platform = platform.system()
        self.FileLogging = False
        self.Lock = Lock()
        self.LogHandle = None
        if self.Platform == 'Windows':
            self.std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    def SetLogLevel(self, Level):
        self.LogLevel = Level
    def SetColour(self, Value):
        global ENABLE_COLOUR
        ENABLE_COLOUR = bool(Value)
    def SetFileLogging(self, Value):
        if self.FileLogging == True and Value == False:
            self.LogHandle.close()
        elif self.FileLogging == False and Value == True:
            self.LogHandle = open("Logs/console.log", "a")
        self.FileLogging = Value
    def Write(self, Value, IsColour = False):
        stdout.write(Value)
        if self.FileLogging and IsColour == False:
            self.LogHandle.write(Value)

    def _Colour(self, Colour):
        if ENABLE_COLOUR:
            if self.Platform == 'Windows':
                ctypes.windll.kernel32.SetConsoleTextAttribute(self.std_out_handle, Colour)
            else:
                self.Write(Colour, True)

    def _Time(self, Colour):
        self._Colour(Colour)
        self.Write("(")
        self._Colour(TWHITE)
        self.Write(time.strftime("%H:%M:%S", time.localtime()))
        self._Colour(Colour)
        self.Write(") ")

    def _From(self, From, Colour):
        self._Colour(Colour)
        self.Write("(")
        self._Colour(TWHITE)
        self.Write(From)
        self._Colour(Colour)
        self.Write(") ")
        self._Colour(TNORMAL)

    def Out(self, From, Message):
        self.Lock.acquire()
        self._Time(TGREEN)
        self._From(From, TGREEN)
        self.Write(Message)
        self.Write("\n")
        stdout.flush()
        self.Lock.release()

    def Error(self, From, Message):
        self.Lock.acquire()
        self._Time(TRED)
        self._From(From, TRED)
        self._Colour(TRED)
        self.Write(Message)
        self._Colour(TNORMAL)
        self.Write("\n")
        stdout.flush()
        self.Lock.release()

    def Warning(self, From, Message):
        if self.LogLevel < LOG_LEVEL_WARNING:
            return
        self.Lock.acquire()
        self._Time(TYELLOW)
        self._From(From, TYELLOW)
        self._Colour(TYELLOW)
        self.Write(Message)
        self._Colour(TNORMAL)
        self.Write("\n")
        stdout.flush()
        self.Lock.release()
        
    def Debug(self, From, Message):
        if self.LogLevel < LOG_LEVEL_DEBUG:
            return
        self.Lock.acquire()
        self._Time(TBLUE)
        self._From(From, TBLUE)
        self.Write(Message)
        self.Write("\n")
        stdout.flush()
        self.Lock.release()

    def FlushLog(self):
        if self.FileLogging:
            self.LogHandle.flush()
    
Console = OConsole()
