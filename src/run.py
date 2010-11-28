'''Initial draft of OptiCraft server for Minecraft classic'''
from servercontroller import ServerController
import traceback
import time
import os
import os.path
from console import *

def Main():
    ServerControl = ServerController()
    try:
        ServerControl.Run()
    except:
        derp=1/0
        Console.Error("Shutdown","Server is shutting down.")
        fHandle = open("CrashLog.txt","a")
        fHandle.write("="*30 + "\n")
        fHandle.write("Crash date: %s\n" %time.strftime("%c", time.gmtime()))
        fHandle.write("="*30 + "\n")
        traceback.print_exc(file=fHandle)
        fHandle.close()
        ServerControl.Shutdown(True)
        if os.path.isfile("opticraft.pid"):
            os.remove("opticraft.pid")
        return
if __name__ == "__main__":
    Main()
