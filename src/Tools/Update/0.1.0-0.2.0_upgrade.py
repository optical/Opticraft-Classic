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
import json
import gzip
import struct
import array
import time
import os

class World(object):
    Version = 2
    @staticmethod
    def _ReadLengthString(FileHandle):
        Val = struct.unpack("i", FileHandle.read(4))[0]
        return FileHandle.read(Val)
    @staticmethod
    def _MakeLengthString(String):
        return struct.pack("i", len(String)) + String
    
class MetaDataKey(object):
    '''Enum for all required (core) metadata keys'''
    X = "X"
    Y = "Y"
    Z = "Z"
    SpawnX = "SpawnX"
    SpawnY = "SpawnY"
    SpawnZ = "SpawnZ"
    SpawnOrientation = "SpawnOrientation"
    SpawnPitch = "SpawnPitch"
    MinimumBuildRank = "MinimumBuildRank"
    MinimumJoinRank = "MinimumJoinRank"
    CreationDate = "CreationDate"
    IsHidden = "Hidden"


def ConvertWorld(WorldName):
    start = time.time()
    print "Converting world %s..." % WorldName,
    with open("../../Worlds/%s" % WorldName, "rb") as rHandle:
        Version = struct.unpack("h", rHandle.read(2))[0] #Unused for now
        if Version != 1:
            print "Unknown map version %d found on world %s. Unable to convert." % (Version, WorldName)
            return False
        X = struct.unpack("h", rHandle.read(2))[0]
        Y = struct.unpack("h", rHandle.read(2))[0]
        Z = struct.unpack("h", rHandle.read(2))[0]
        SpawnX = struct.unpack("h", rHandle.read(2))[0]
        SpawnY = struct.unpack("h", rHandle.read(2))[0]
        SpawnZ = struct.unpack("h", rHandle.read(2))[0]
        SpawnOrientation = struct.unpack("h", rHandle.read(2))[0]
        SpawnPitch = struct.unpack("h", rHandle.read(2))[0]
        MetaLength = struct.unpack("i", rHandle.read(4))[0]
        MetaData = dict()
        for i in xrange(MetaLength):
            Key = World._ReadLengthString(rHandle)
            Value = World._ReadLengthString(rHandle)
            MetaData[Key] = Value
        CompressedBlocks = rHandle.read()
        
    #Now write it out
    with open("../../Worlds/%s" % WorldName, "wb") as fHandle:
        fHandle.write(struct.pack("h", World.Version))
        #Setup the metadata.
        NewMetaData = {}
        NewMetaData[MetaDataKey.X] = X
        NewMetaData[MetaDataKey.Y] = Y
        NewMetaData[MetaDataKey.Z] = Z
        NewMetaData[MetaDataKey.SpawnX] = SpawnX
        NewMetaData[MetaDataKey.SpawnY] = SpawnY
        NewMetaData[MetaDataKey.SpawnZ] = SpawnZ
        NewMetaData[MetaDataKey.SpawnOrientation] = SpawnOrientation
        NewMetaData[MetaDataKey.SpawnPitch] = SpawnPitch
        NewMetaData[MetaDataKey.CreationDate] = int(time.time())
        NewMetaData[MetaDataKey.MinimumJoinRank] = 'spectator'
        NewMetaData[MetaDataKey.MinimumBuildRank] = MetaData["minrank"]
        NewMetaData[MetaDataKey.IsHidden] = not bool(MetaData["hidden"])
        
        JSONMetaData = json.dumps(NewMetaData)
        fHandle.write(struct.pack("i", len(JSONMetaData)))
        fHandle.write(JSONMetaData)
        fHandle.write(struct.pack("i", 2))
        fHandle.write("{}")
        fHandle.write(struct.pack("i", len(CompressedBlocks)))
        fHandle.write(CompressedBlocks)
    
    print "Done in %.3f seconds" % (time.time() - start)
        
def ConvertWorlds():
    start = time.time()
    for Filename in os.listdir('../../Worlds/'):
        if Filename.endswith('.save'):
            ConvertWorld(Filename)
            
    print "Converted all worlds in %.3f seconds" % (time.time() - start)

def Main():
    start = time.time()
    print "Starting update process for version 0.1 to 0.2.."
    ConvertWorlds()
    print "Conversion process complete. Took %.3f seconds" % (time.time() - start)
    raw_input("Press enter to terminate")

if __name__ == "__main__":
    Main()
                


