'''Initial draft of OptiCraft server for Minecraft classic'''
from servercontroller import ServerController
import traceback
import time


def Main():
    ServerControl = ServerController()
    try:
        ServerControl.Run()
    except:
        fHandle = open("CrashLog.txt","a")
        fHandle.write("="*30 + "\n")
        fHandle.write("Crash date: %s\n" %time.strftime("%c", time.gmtime()))
        fHandle.write("="*30 + "\n")
        traceback.print_exc(file=fHandle)
        fHandle.close()
        ServerControl.Shutdown(True)
        return
if __name__ == "__main__":
    Main()
