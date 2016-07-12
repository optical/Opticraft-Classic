'''Initial draft of OptiCraft server for Minecraft classic'''
from core.servercontroller import ServerController, SigkillException
import traceback
import time
import os
import os.path
import shutil
import sys
try:
    import cProfile as Profile
except ImportError:
    import Profile
from core.console import *

ProfileRun = False

def EnsureConfigurationSetup(configName):
    if not os.path.exists(configName):
        if os.path.exists(configName + ".sample"):
            shutil.copy2(configName + ".sample", configName);
            Console.Warning("Configuration", "No %s found. Copying template from %s. Default values will be used" %(configName, configName + ".sample"))
        else:
            Console.Error("Configuration", "No %s found. Server terminating" %(configName))
            sys.exit(-1)

def Main():
    ServerControl = None
    try:
        EnsureConfigurationSetup("opticraft.ini")
        EnsureConfigurationSetup("ranks.ini")

        ServerControl = ServerController()
        ServerControl.Run()
    except BaseException, e:
        ExceptionType = type(e)
        Crash = ExceptionType not in [KeyboardInterrupt, SigkillException]
        if Crash:
            Console.Error("Shutdown", "The server has encountered a critical error and is shutting down.")
            Console.Error("Shutdown", "Details about the error can be found in CrashLog.txt")
            try:
                fHandle = open("CrashLog.txt", "a")
                fHandle.write("="*30 + "\n")
                fHandle.write("Crash date: %s\n" % time.strftime("%c", time.gmtime()))
                fHandle.write("="*30 + "\n")
                traceback.print_exc(file = fHandle)
                fHandle.close()
            except IOError:
                traceback.print_exc()            
        else:
            Console.Error("Shutdown", "Server shutdown has been initiated")
        if os.path.isfile("opticraft.pid"):
            os.remove("opticraft.pid")            
        if ServerControl is not None:
            ServerControl.Shutdown(Crash)
            if ServerControl.InstantClose == 0:
                raw_input("\nPress enter to terminate ")
        return
    
if __name__ == "__main__":
    ProfileRun = False            

    for i in xrange(1, len(sys.argv)):
        if sys.argv[i].lower() == "-profile":
            ProfileRun = True
        elif sys.argv[i].lower() == "-disablegc":
            import gc
            gc.disable()

            print "Garbage collection has been disabled."
        else:
            print "Unable to parse commandline arg: %s" % sys.argv[i]
    if ProfileRun:
        Profile.run('Main()', 'profiler-%s.pstats' % time.strftime("%d-%m-%Y_%H-%M-%S", time.gmtime()))
    else:
        Main()
        

