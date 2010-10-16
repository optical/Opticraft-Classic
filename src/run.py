'''Initial draft of OptiCraft server for Minecraft classic'''
from servercontroller import ServerController
import traceback
import time
if __name__ == "__main__":
    try:
        ServerControl = ServerController()
        ServerControl.run()
    except:
        fHandle = open("CrashLog.txt","a")
        fHandle.write("="*15 + "\n")
        fHandle.write("Crash date: %s" %time.strftime("%c", time.gmtime()))
        fHandle.write("="*15 + "\n")
        traceback.print_exc(file=fHandle)
        fHandle.close()