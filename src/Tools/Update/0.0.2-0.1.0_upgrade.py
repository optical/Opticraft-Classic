# Copyright (c) 2010-2011, Jared Klopper
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
import time
from ConfigParser import RawConfigParser
import traceback
import os
import struct
import zlib
import gzip
import array
OldToNew = {
    "s": "spectator",
    "g": "guest",
    "t": "recruit",
    "b": "builder",
    "o": "operator",
    "a": "admin",
    "z": "owner",
    }
def ConvertRanks():
    print "Converting ranks..."
    start = time.time()
    ConfigReader = RawConfigParser()
    ConfigReader.read("../../ranks.ini")
    Items = ConfigReader.items("ranks")
    for Item in Items:
        Username,Rank = Item
        ConfigReader.remove_option("ranks",Username)
        ConfigReader.set("ranks",Username,OldToNew[Rank])
    fHandle = open("../../ranks.ini","w")
    ConfigReader.write(fHandle)
    fHandle.close()
    print "Converted ranks in %f seconds" %(time.time()-start)
        
def ConvertWorlds():
    print "Converting worlds... (This may take awhile)"
    start = time.time()
    Files = os.listdir("../../Worlds")
    for File in Files:
        if len(File) < 5:
            continue
        if File[-5:] != ".save":
            continue
        ConvertWorld(File)
    print "Converted worlds in %f seconds" %(time.time()-start)
def _MakeLengthString(String):
    return struct.pack("i",len(String)) + String  

def ConvertWorld(FileName):
    #Load old data
    start = time.time()
    Blocks = array.array("c")
    fHandle = open("../../Worlds/%s" %FileName, "rb")
    CompressedSize = struct.unpack("i",fHandle.read(4))[0]
    Blocks.fromstring(zlib.decompress(fHandle.read(CompressedSize)))
    X = struct.unpack("h",fHandle.read(2))[0]
    Y = struct.unpack("h",fHandle.read(2))[0]
    Z = struct.unpack("h",fHandle.read(2))[0]
    SpawnX = struct.unpack("h",fHandle.read(2))[0]
    SpawnY = struct.unpack("h",fHandle.read(2))[0]
    SpawnZ = struct.unpack("h",fHandle.read(2))[0]
    SpawnOrientation = struct.unpack("h",fHandle.read(2))[0]
    SpawnPitch = struct.unpack("h",fHandle.read(2))[0]
    MinRank = fHandle.read(1)
    MinRank = OldToNew[MinRank]
    Hidden = fHandle.read(1)
    fHandle.close()
    fHandle = open("../../Worlds/%s" %FileName,"wb")
    #Write it out in new format.
    fHandle.write(struct.pack("h",1)) #Map version number
    fHandle.write(struct.pack("h",X))
    fHandle.write(struct.pack("h",Y))
    fHandle.write(struct.pack("h",Z))
    fHandle.write(struct.pack("h",SpawnX))
    fHandle.write(struct.pack("h",SpawnY))
    fHandle.write(struct.pack("h",SpawnZ))
    fHandle.write(struct.pack("h",SpawnOrientation))
    fHandle.write(struct.pack("h",SpawnPitch))
    fHandle.write(struct.pack("i",2))
    fHandle.write(_MakeLengthString("hidden"))
    fHandle.write(_MakeLengthString(Hidden))
    fHandle.write(_MakeLengthString("minrank"))
    fHandle.write(_MakeLengthString(MinRank))
    gzipHandle = gzip.GzipFile(fileobj = fHandle, compresslevel = 1,mode = "wb")
    gzipHandle.write(Blocks.tostring())
    gzipHandle.close()
    fHandle.close()
    print "Converted world %s in %f seconds" %(FileName, time.time()-start)
    
def ConvertZones():
    print "Converting zones..."
    start = time.time()
    Files = os.listdir("../../Zones")
    for File in Files:
        ConfigReader = RawConfigParser()
        ConfigReader.read("../../Zones/%s" %File)
        ConfigReader.set("Info","minrank",OldToNew[ConfigReader.get("Info","minrank")])
        fHandle = open("../../Zones/%s" %File,"w")
        ConfigReader.write(fHandle)
        fHandle.close()
    print "Converted zones in %.2f seconds" %(time.time()-start)
     
def Main():
    print "This tool will convert your old Zones, Worlds, and Ranks from Opticraft 0.0.2 to version 0.1.0"
    Answer = raw_input("Are you sure this is what you want to do? (Y/N): ")
    if Answer.lower() != "y":
        print "Conversion cancelled."
        return
    print "\nNow starting the conversion process..."
    start = time.time()
    ConvertRanks()
    ConvertZones()
    ConvertWorlds()
    print "\nAll conversion processes have completed in %f seconds" %(time.time()-start)
    print "You may now run Opticraft 0.1.0. Do not use this tool again."

if __name__ == "__main__":
    try:
        Main()
    except:
        traceback.print_exc()
        print "An error occured. Terminating conversion process"
    raw_input("Press enter to exit")