'''Console output'''

#Constants.
LOG_LEVEL_MINIMUM = -1
LOG_LEVEL_WARNING = 0
LOG_LEVEL_DEBUG = 2
import platform
import time
from sys import stdout
if platform.system() == 'Windows':
    ENABLE_COLOUR = True
    import ctypes
    STD_OUTPUT_HANDLE= -11
    FOREGROUND_BLUE = 0x01 # text color contains blue.
    FOREGROUND_GREEN= 0x02 # text color contains green.
    FOREGROUND_RED  = 0x04 # text color contains red.
    FOREGROUND_INTENSITY = 0x08 # text color is intensified.
    BACKGROUND_BLUE = 0x10 # background color contains blue.
    BACKGROUND_GREEN= 0x20 # background color contains green.
    BACKGROUND_RED  = 0x40 # background color contains red.
    BACKGROUND_INTENSITY = 0x80 # background color is intensified.
    TRED = FOREGROUND_RED | FOREGROUND_INTENSITY
    TGREEN = FOREGROUND_GREEN | FOREGROUND_INTENSITY
    TYELLOW = FOREGROUND_GREEN | FOREGROUND_RED | FOREGROUND_INTENSITY
    TNORMAL = FOREGROUND_GREEN | FOREGROUND_RED | 0x01
    TWHITE = TNORMAL | FOREGROUND_INTENSITY
    TBLUE = FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY

elif platform.system() == 'Linux':
    ENABLE_COLOUR = True
    TRED    = "\033[22;31m"
    TGREEN  = "\033[22;32m"
    TYELLOW = "\033[01;33m"
    TNORMAL = "\033[22;37m"
    TWHITE  = "\033[0m"
    TBLUE   = "\033[1;34m"
else:
    ENABLE_COLOUR = False

class OConsole(object):
    '''Class for Console in opticraft'''
    def __init__(self):
        self.LogLevel = LOG_LEVEL_WARNING
        self.Platform = platform.system()
        if self.Platform == 'Windows':
            self.std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    def SetLogLevel(self,Level):
        self.LogLevel = Level
    def _Colour(self,Colour):
        if ENABLE_COLOUR:
            if self.Platform == 'Windows':
                ctypes.windll.kernel32.SetConsoleTextAttribute(self.std_out_handle,Colour)
            else:
                stdout.write(Colour)

    def _Time(self,Colour):
        self._Colour(Colour)
        stdout.write("(")
        self._Colour(TWHITE)
        stdout.write(time.strftime("%H:%M:%S",time.localtime()))
        self._Colour(Colour)
        stdout.write(") ")

    def _From(self,From,Colour):
        self._Colour(Colour)
        stdout.write("(")
        self._Colour(TWHITE)
        stdout.write(From)
        self._Colour(Colour)
        stdout.write(") ")
        self._Colour(TNORMAL)

    def Out(self,From,Message):
        self._Time(TGREEN)
        self._From(From,TGREEN)
        stdout.write(Message)
        stdout.write("\n")
        stdout.flush()

    def Error(self,From,Message):
        self._Time(TRED)
        self._From(From,TRED)
        self._Colour(TRED)
        stdout.write(Message)
        self._Colour(TNORMAL)
        stdout.write("\n")
        stdout.flush()

    def Warning(self,From,Message):
        if self.LogLevel < LOG_LEVEL_MINIMUM:
            return
        self._Time(TYELLOW)
        self._From(From,TYELLOW)
        self._Colour(TYELLOW)
        stdout.write(Message)
        self._Colour(TNORMAL)
        stdout.write("\n")
        stdout.flush()
        
    def Debug(self,From,Message):
        if self.LogLevel < LOG_LEVEL_DEBUG:
            return
        self._Time(TBLUE)
        self._From(From,TBLUE)
        stdout.write(Message)
        stdout.write("\n")
        stdout.flush()

Console = OConsole()