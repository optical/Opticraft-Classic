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
        if OldToNew.has_key(Rank):
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
    if OldToNew.has_key(MinRank):
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
        if len(File) < 4:
            continue
        if File[-3:] != "ini":
            continue        
        ConfigReader = RawConfigParser()
        ConfigReader.read("../../Zones/%s" %File)
        if OldToNew.has_key(ConfigReader.get("Info","minrank")):
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