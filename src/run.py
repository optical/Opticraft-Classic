'''Initial draft of OptiCraft server for Minecraft classic'''
# Copyright (c) 2010-2011,  Jared Klopper
# All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice, this
#       list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the distribution.
#     * Neither the name of Opticraft nor the names of its contributors may be
#       used to endorse or promote products derived from this software without
#       specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from core.servercontroller import ServerController, SigkillException
import traceback
import time
import os
import os.path
import sys
try:
    import cProfile as Profile
except ImportError:
    import Profile
from core.console import *

ProfileRun = False

def Main(EnablePsyco = False, PsycoLogging = False):
    ServerControl = None
    try:
        if ProfileRun != False:
            ServerControl = ServerController(Tag = ' (Profile mode)')
        else:
            ServerControl = ServerController()
            
        if EnablePsyco:
            try:
                import psyco
                psyco.full()
                if PsycoLogging:
                    psyco.log()
            except:
                Console.Warning("Psyco", "It appears you do not have psyco installed. Psyco is a specialized " \
                                + "python JIT compiler. It provides a significant performance boost when used with opticraft")
                Console.Warning("Psyco", "Psyco is easy to install and setup. See: http://psyco.sourceforge.net/download.html")
            else:
                Console.Out("Psyco", "Psyco JIT is now running.")

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
    UsePsyco = True
    PsycoLogging = False
    for i in xrange(1, len(sys.argv)):
        if sys.argv[i].lower() == "-profile":
            ProfileRun = True
        elif sys.argv[i].lower() == "-disablegc":
            import gc
            gc.disable()

            print "Garbage collection has been disabled."
        elif sys.argv[i].lower() == "-disablepsyco":
            UsePsyco = False
        elif sys.argv[i].lower() == "-psycologging":
            PsycoLogging = True
        else:
            print "Unable to parse commandline arg: %s" % sys.argv[i]
    if ProfileRun:
        Profile.run('Main()', 'profiler-%s.pstats' % time.strftime("%d-%m-%Y_%H-%M-%S", time.gmtime()))
    else:
        Main(UsePsyco, PsycoLogging)
        

