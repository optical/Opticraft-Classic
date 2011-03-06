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

from core.servercontroller import ServerController
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

def Main():
    ServerControl = ServerController()
    try:
        ServerControl.Run()
    except:
        Console.Error("Shutdown", "Server is shutting down.")
        try:
            fHandle = open("CrashLog.txt", "a")
            fHandle.write("="*30 + "\n")
            fHandle.write("Crash date: %s\n" % time.strftime("%c", time.gmtime()))
            fHandle.write("="*30 + "\n")
            traceback.print_exc(file=fHandle)
            fHandle.close()
        except IOError:
            traceback.print_exc()
        ServerControl.Shutdown(True)
        if os.path.isfile("opticraft.pid"):
            os.remove("opticraft.pid")
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
        else:
            print "Unable to parse commandline arg: %s" % sys.argv[i]
    if ProfileRun:
        Profile.run('Main()', 'profiler-%s.pstats' % time.strftime("%d-%m-%Y_%H-%M-%S", time.gmtime()))
    else:
        Main()
        

