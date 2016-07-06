import json
import gzip
import struct
import array
import time
import os
import ConfigParser

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


def ConvertWorld(Path, WorldName):
    start = time.time()
    print "Converting world %s..." % WorldName,
    with open(Path + WorldName, "rb") as rHandle:
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
    with open(Path + WorldName, "wb") as fHandle:
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
            ConvertWorld('../../Worlds/', Filename)
            
    print "Converted all worlds in %.3f seconds" % (time.time() - start)

def ConvertTemplates():
    start = time.time()
    for Filename in os.listdir('../../Templates/'):
        if Filename.endswith('.save'):
            ConvertWorld('../../Templates/', Filename)
            
    print "Converted all templates in %.3f seconds" % (time.time() - start)


def ConvertZones():
    start = time.time()
    print "Loading zones...."
    zonestart = time.time()
    Zones = dict() #Key is worldname
    for Filename in os.listdir('../../Zones/'):
        if Filename.endswith('.ini'):
            Zone = dict()
            Conf = ConfigParser.RawConfigParser()
            Conf.read('../../Zones/' + Filename)
            Zone['Name'] = Conf.get('Info', 'Name')
            Zone['X1'] = int(Conf.get('Info', 'x1'))
            Zone['X2'] = int(Conf.get('Info', 'x2'))
            Zone['Y1'] = int(Conf.get('Info', 'y1'))
            Zone['Y2'] = int(Conf.get('Info', 'y2'))
            Zone['Z1'] = int(Conf.get('Info', 'z1'))
            Zone['Z2'] = int(Conf.get('Info', 'z2'))
            Zone['Owner'] = Conf.get('Info', 'owner')
            Zone['MinimumRank'] = Conf.get('Info', 'minrank')
            Zone['Builders'] = list()
            CurWorld = Conf.get('Info', 'map')
            for Item, Junk in Conf.items('Builders'):
                Zone['Builders'].append(Item)
            ZoneList = Zones.get(Conf.get('Info', 'map'), None)
            if ZoneList is None:
                ZoneList = list()
                Zones[Conf.get('Info', 'map')] = ZoneList
            ZoneList.append(Zone)
            print "Loaded zone %s." % Zone['Name']
            
    print "Loaded zones in %.3f seconds" % (time.time() - zonestart)
    #Rewrite worlds with zone data...
    print "Converting world zones..."
    worldstart = time.time()
    for WorldName in Zones:
        #Read the world
        with open("../../Worlds/%s.save" % WorldName, "rb") as fHandle:
            
            Version = struct.unpack("h", fHandle.read(2))[0]
            if Version != World.Version:
                Console.Error("World", "Unknown map version (%d) found on world %s. Unable to convert its zones." % (Version, self.Name))
                return False
            MetaDataLength = struct.unpack("i", fHandle.read(4))[0]
            MetaData = json.loads(fHandle.read(MetaDataLength))
            DataStoreLength = struct.unpack("i", fHandle.read(4))[0]
            DataStore = json.loads(fHandle.read(DataStoreLength))
            DataStore["Zones"] = Zones[WorldName]
            BlockSize = struct.unpack("i", fHandle.read(4))[0]
            Blocks = fHandle.read(BlockSize)
            
        #Write it out again
        with open("../../Worlds/%s.save" % WorldName, "wb") as fHandle:
            fHandle.write(struct.pack("h", World.Version))
            JSONMetaData = json.dumps(MetaData)
            fHandle.write(struct.pack("i", len(JSONMetaData)))
            fHandle.write(JSONMetaData)
            JSONDataStore = json.dumps(DataStore)
            fHandle.write(struct.pack("i", len(JSONDataStore)))
            fHandle.write(JSONDataStore)
            fHandle.write(struct.pack("i", len(Blocks)))
            fHandle.write(Blocks)
            
        print "Converted zones on world %s" % WorldName
    print "Converted all world zones in %.3f seconds" % (time.time() - worldstart)
    print "Converted all zones in %.3f seconds" % (time.time() - start)
    
def Main():
    start = time.time()
    print "Starting update process for version 0.1 to 0.2.."
    ConvertWorlds()
    ConvertTemplates()
    ConvertZones()
    print "Conversion process complete. Took %.3f seconds" % (time.time() - start)
    raw_input("Press enter to terminate")

if __name__ == "__main__":
    Main()
                


