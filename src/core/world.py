import os.path
import cStringIO
import gzip
import struct
import random
import shutil
import sqlite3 as dbapi
import threading
import Queue
import copy
from array import array
from core.packet import PacketWriter
from core.constants import *
from core.asynchronousquery import AsynchronousQueryResult
from core.console import *
from core.jsondict import JSONDict
#Used for deciding whether to lock a map when undoing actions
#Tweak appropriately
LOCK_LEVEL = 35000 #Number of blocks needed in order to force a map lock

class BlockLog(object):
    __slots__ = ['Username', 'Time', 'Value']
    '''Stores the history of a block'''
    def __init__(self, Username, Time, Value):
        self.Username = Username
        self.Time = Time
        self.Value = Value
class BlockChange(object):
    '''Used between threads IOThread creates these and sends them to the World thread
    in order for changes to be made in a thread-safe manner'''
    __slots__ = ['Offset', 'Value']
    def __init__(self, Offset, Value):
        self.Offset = Offset
        self.Value = Value
        
class SaveTask(threading.Thread):
    '''Saves the world to disk asynchronously'''   
    def __init__(self, pWorld, Verbose):
        '''Copy all the relevant data'''
        threading.Thread.__init__(self, name = "SaveTask (%s)" % pWorld.Name)
        self.MetaData = copy.copy(pWorld.MetaData)
        self.Blocks = copy.copy(pWorld.Blocks)
        self.DataStore = pWorld.DataStore
        self.Name = pWorld.Name
        self.Verbose = Verbose
        self.CompressionLevel = pWorld.CompressionLevel
        
    def run(self):
        self.Save(self.Verbose)
        del self.Blocks
        
    def Save(self, Verbose = True):
        '''The map file is a file of the following format:
        int16 VersionNumber
        int32 MetaDataSize in bytes
        JSON MetaDataObject (dictionary of string -> value)
        int32 DataBlockSize in bytes
        JSON DataBlock (dictionary of string -> value)
        int32 gzipped block size
        gzip Blocks
        '''
        start = time.time()
        try:
            #Save to a temp file. Then copy it over. (If we crash during this, the old save is unchanged)
            #...Crashes may occur if we run out of memory, so do not change this!
            fHandle = open("Worlds/%s.temp" % (self.Name), 'wb')
        except:
            Console.Error("World", "Failed to saved world %s to disk." % self.Name)
        fHandle.write(struct.pack("h", World.VERSION))
        JSONMetaData = self.MetaData.AsJSON()
        fHandle.write(struct.pack("i", len(JSONMetaData)))
        fHandle.write(JSONMetaData)
        JSONDataStore = self.DataStore.AsJSON()
        fHandle.write(struct.pack("i", len(JSONDataStore)))
        fHandle.write(JSONDataStore)
        CompressedBlocks = cStringIO.StringIO()
        gzipHandle = gzip.GzipFile(fileobj = CompressedBlocks, mode = "wb", compresslevel = self.CompressionLevel)
        gzipHandle.write(self.Blocks.tostring())
        gzipHandle.close()        
        fHandle.write(struct.pack("i", len(CompressedBlocks.getvalue())))
        fHandle.write(CompressedBlocks.getvalue())
        fHandle.close()
        try:
            shutil.copy("Worlds/%s.temp" % (self.Name), "Worlds/%s.save" % (self.Name))
            os.remove("Worlds/%s.temp" % (self.Name))
        except:
            Console.Warning("World", "Failed to save world %s. Trying again soon" % self.Name)
            return
        if Verbose:
            Console.Out("World", "Saved world %s in %dms" % (self.Name, int((time.time() - start) * 1000)))
            #self.SendNotice("Saved world %s in %dms" % (self.Name, int((time.time() - start) * 1000)))
    
    
class AsynchronousIOThread(threading.Thread):
    '''Performs operations on the sqlite DB asynchronously to avoid long blocking
    ...waits for the disk'''
    def __init__(self, pWorld):
        threading.Thread.__init__(self, name = "BlockLog Thread (%s)" % pWorld.Name)
        self.daemon = True
        self.WorldName = pWorld.Name
        self.World = pWorld
        self.DBConnection = None
        self.Running = True
        self.Tasks = Queue.Queue()
        self.Tasks.put(["CONNECT", self.WorldName])
    
    def run(self):
        while self.Running:
            Task = self.Tasks.get()
            #Terrible, terrible way of communication between threads
            #TODO: Rewrite this junk
            #Task is a list of 2 items, [0] is the instruction, [1] is the payload
            if Task[0] == "FLUSH":
                #Flush blocks
                self._FlushBlocksTask(Task[1])
            elif Task[0] == "UNDO_ACTIONS":
                #Task 1-4 is: 
                #Number of blocks changed thus far (int)
                #Username (Who used the command
                #Username of blocks to undo,
                #Timestamp of oldest block allowed
                self._UndoActionsTask(Task[1], Task[2], Task[3])
            elif Task[0] == "ASYNC_QUERY":
                self._AsynchronousQuery(Task[1], Task[2], Task[3], Task[4])
            elif Task[0] == "EXECUTE":
                #Task[1] is a string such as "REPLACE INTO BlockLogs VALUES(?,?,?,?)"
                #Task[2] is a tupe of values to subsitute into the string safely
                #See: http://docs.python.org/library/sqlite3.html
                self._ExecuteTask(Task[1], Task[2])
            elif Task[0] == "SHUTDOWN":
                self.Running = False
                self.World = None
                self.DBConnection.commit()
                self.DBConnection.close()
            elif Task[0] == "CONNECT":
                #Connect/Reconnect to the DB.
                self._ConnectTask()

    def _ExecuteTask(self, Query, Parameters):
        '''Performs a query, but does not return any data'''
        try:
            self.DBConnection.execute(Query, Parameters)
            self.DBConnection.commit()
        except dbapi.OperationalError:
            Console.Warning("IOThread", "Failed to execute Query. Trying again soon")
            self.Tasks.put(["EXECUTE", Query, Parameters])
    
    def _AsynchronousQuery(self, Query, QueryParameters, CallbackFunc, kwArgs):
        '''Performs a query and returns the a list of Rows back'''
        IsException = False
        Results = list()
        try:
            Result = self.DBConnection.execute(Query, QueryParameters)
            Results = Result.fetchall()
        except Exception, e:
            IsException = True

        self.World.AddAsyncQueryResult(AsynchronousQueryResult(CallbackFunc, kwArgs, Results, IsException))
    
    def _ConnectTask(self):
        self.DBConnection = dbapi.connect("Worlds/BlockLogs/%s.db" % self.WorldName)
        self.DBConnection.text_factory = str

    def _FlushBlocksTask(self, Data):
        start = time.time()
        Cursor = self.DBConnection.cursor()
        def QueryGenerator(Data):
            for Key in Data:
                yield (Key, Data[Key].Username, Data[Key].Time, ord(Data[Key].Value))
        try:               
            Cursor.executemany("REPLACE INTO Blocklogs VALUES(?,?,?,?)", QueryGenerator(Data))
        except dbapi.OperationalError:
            self.Tasks.put(["FLUSH", Data])
            return
        if self.Tasks.empty():
            self.DBConnection.commit()
        Console.Debug("IOThread", "Flushing %d blocks took %.3f seconds!" % (len(Data), time.time() - start))
        
    def _UndoActionsTask(self, Username, ReverseName, Time):
        now = time.time()
        try:
            SQLResult = self.DBConnection.execute("SELECT Offset,OldValue from Blocklogs where Username = ? and Time > ?", (ReverseName, now - Time))
        except dbapi.OperationalError:
            Console.Debug("IOThread", "Failed to Execute undoactions. Trying again later")
            self.Tasks.put(["UNDO_ACTIONS", Username, ReverseName, Time])
            return
        BlockChangeList = [Username, ReverseName, 0]
        NumChanged = 0
        while True:
            Rows = SQLResult.fetchmany()
            if len(Rows) == 0:
                break
            for Row in Rows:
                BlockChangeList.append(BlockChange(Row[0], Row[1]))
                NumChanged += 1
                
        BlockChangeList[2] = NumChanged
        self.World.AddBlockChanges(BlockChangeList)
        try:
            self.DBConnection.execute("DELETE FROM Blocklogs where Username = ? and Time > ?", (ReverseName, now - Time))
            self.DBConnection.commit()
        except dbapi.OperationalError:
            Console.Debug("IOThread", "Failed to clean up undoactions. Trying again later.")
            self.Tasks.put(["EXECUTE"], "DELETE FROM Blocklogs where Username = ? and Time > ?", (ReverseName, now - Time))
        Console.Debug("IOThread", "%s reversed %s's actions. %d changed in %f seconds" % (Username, ReverseName, NumChanged, time.time() - now))
       
    def Shutdown(self, Crash):
        self.Tasks.put(["SHUTDOWN"])
        
class WorldLoadFailedException(Exception):
    pass
class WorldRequiresUpdateException(Exception):
    pass

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
    CreationDate = "CreationDate" #Integer value
    IsHidden = "Hidden"
    
class DataStoreKey(object):
    '''Enum for all required datablock keys (None, as of yet)'''
    pass
      
class World(object):
    '''Controls worlds, specifically the block store, placing blocks, and managing player actions'''
    VERSION = 2
    def __init__(self, ServerControl, Name, NewMap = False, NewX = -1, NewY = -1, NewZ = -1):
        self.Blocks = array("c")
        self.BlockCache = cStringIO.StringIO()
        self.IsDirty = True
        self.IsLocked = False
        self.Players = list()
        self.TransferringPlayers = list()
        self.JoiningPlayers = list()
        self.Name = Name
        self.X, self.Y, self.Z = -1, -1, -1
        self.MetaData = JSONDict()
        self.DataStore = JSONDict()
        self.ServerControl = ServerControl
        self.BlockHistory = dict()
        self.PlayerIDs = range(127)
        #Config values
        self.DefaultX = int(self.ServerControl.ConfigValues.GetValue("worlds", "DefaultSizeX", "256"))
        self.DefaultY = int(self.ServerControl.ConfigValues.GetValue("worlds", "DefaultSizeY", "256"))
        self.DefaultZ = int(self.ServerControl.ConfigValues.GetValue("worlds", "DefaultSizeZ", "96"))
        self.LastSave = self.ServerControl.Now + random.randrange(0, 30)
        self.SaveInterval = int(self.ServerControl.ConfigValues.GetValue("worlds", "SaveTime", "300"))
        self.LastBackup = self.ServerControl.Now + random.randrange(0, 30)
        self.BackupInterval = int(self.ServerControl.ConfigValues.GetValue("worlds", "BackupTime", "3600"))
        self.CompressionLevel = int(self.ServerControl.ConfigValues.GetValue("worlds", "CompressionLevel", 1))
        self.LogBlocks = int(self.ServerControl.ConfigValues.GetValue("worlds", "EnableBlockHistory", 1))
        self.LogFlushThreshold = int(self.ServerControl.ConfigValues.GetValue("worlds", "LogFlushThreshold", 10000))
        self.DisableBots = bool(int(self.ServerControl.ConfigValues.GetValue("server", "DisableBots", "0")))
        self.MinRankMessage = self.ServerControl.ConfigValues.GetValue("worlds", "MinimumBuildRankMessage", "&RYou do not have the required rank to build on this world")
        self.IOThread = None
        self.CurrentSaveThread = None
        self.AsyncBlockChanges = Queue.Queue()
        self.AsyncQueryCallbacks = Queue.Queue()
        self.IdleTimeout = 0 #How long must the world be unoccupied until it unloads itself from memory
        self.CanUnload = True #Is the world allowed to be unloaded
        self.IsMainWorld = False
        self.IdleStart = 0 #Not idle.
        self.DBConnection = None
        self.DBCursor = None
        self.Unloaded = False
        if self.LogBlocks != 0:
            if os.path.exists("Worlds/BlockLogs") == False:
                os.mkdir("Worlds/BlockLogs")
            #Setup the DB connections
            self.DBConnection = dbapi.connect("Worlds/BlockLogs/%s.db" % self.Name, timeout = 0.1)
            self.DBConnection.text_factory = str
            self.DBCursor = self.DBConnection.cursor()
            try:
                Result = self.DBCursor.execute("SELECT * FROM sqlite_master where name='Blocklogs' and type='table'")
            except dbapi.OperationalError:
                raise WorldLoadFailedException
            if Result.fetchone() is None:
                #Create the table
                self.DBCursor.execute("CREATE TABLE Blocklogs (Offset INTEGER UNIQUE,Username TEXT,Time INTEGER,OldValue INTEGER)")
                self.DBCursor.execute("CREATE INDEX Lookup ON Blocklogs (Offset)")
                self.DBCursor.execute("CREATE INDEX Deletion ON Blocklogs (Username,Time)")
                self.DBConnection.commit()
            self.IOThread = AsynchronousIOThread(self)
            self.IOThread.start()

        if os.path.isfile("Worlds/" + self.Name + '.save'):
            LoadResult = self.Load()
            if LoadResult == False:
                Console.Warning("World", "Generating new world for map '%s' - Load a backup if you wish to preserve your data!" % self.Name)
                self.GenerateGenericWorld(self.DefaultX, self.DefaultY, self.DefaultZ)
        else:
            if not NewMap:
                self.GenerateGenericWorld(self.DefaultX, self.DefaultY, self.DefaultZ)
            else:
                self.GenerateGenericWorld(NewX, NewY, NewZ)
        self.NetworkSize = struct.pack("!i", self.X * self.Y * self.Z)

        self.ServerControl.PluginMgr.OnWorldLoad(self)
    
    def Load(self):
        '''The map file is a file of the following format:
        int16 VersionNumber
        int32 MetaDataSize in bytes
        JSON MetaDataObject (dictionary of string -> value)
        int32 DataBlockSize in bytes
        JSON DataBlock (dictionary of string -> value)
        int32 gzipped blocks size
        gzip Block
        '''
        start = time.time()
        rHandle = cStringIO.StringIO()
        fHandle = None
        try:
            fHandle = open("Worlds/" + self.Name + '.save', 'rb')
        except:
            Console.Warning("World", "Failed to open up save file for world %s!" % self.Name)
            return False
        try:
            rHandle.write(fHandle.read())
            fHandle.close()
            rHandle.seek(0)
            Version = struct.unpack("h", rHandle.read(2))[0] #Unused for now
            if Version == 1:
                Console.Error("World", "You have not ran the update script for upgrading from version 0.1 to 0.2. See the Readme for more information!")
                raise WorldRequiresUpdateException
            elif Version != World.VERSION:
                Console.Error("World", "Unknown map version (%d) found on world %s. Unable to load." % (Version, self.Name))
                return False
            MetaDataLength = struct.unpack("i", rHandle.read(4))[0]
            #MetaData is managed by ServerControl, seek ahead and get copy from it.
            rHandle.read(MetaDataLength)
            self.MetaData = self.ServerControl.GetWorldMetaData(self.Name)
            DataStoreLength = struct.unpack("i", rHandle.read(4))[0]
            self.DataStore = JSONDict.FromJSON(rHandle.read(DataStoreLength))
            BlockSize = struct.unpack("i", rHandle.read(4))
            gzipHandle = gzip.GzipFile(fileobj = rHandle, mode = "rb")
            self.Blocks.fromstring(gzipHandle.read(BlockSize))
            gzipHandle.close() 
            rHandle.close()
            
            #MetaData setup
            self.SetCoordinatesFromMetaData()
            self.ValidateMetaData()
            Console.Out("World", "Loaded world %s in %dms" % (self.Name, int((time.time() - start) * 1000)))
            
            #Ensure the data is not corrupt in some way
            assert(len(self.Blocks) == self.X * self.Y * self.Z)
            assert(self.MetaData is not None)
        except WorldRequiresUpdateException, e:
            raise e
        except Exception:
            Console.Warning("World", "Failed to load map '%s'.save The save file is out of date or corrupt." % self.Name)
            return False
    
    def Save(self, Verbose = True):
        '''The map file is a file of the following format:
        int16 VersionNumber
        int32 MetaDataSize in bytes
        JSON MetaDataObject (dictionary of string -> value)
        int32 DataBlockSize in bytes
        JSON DataBlock (dictionary of string -> value)
        '''
        #Saving is done in another thread to prevent blocking writes in the main thread
        self.CurrentSaveThread = SaveTask(self, Verbose)
        self.CurrentSaveThread.start()
        self.LastSave = self.ServerControl.Now

    def Backup(self, Verbose = True):
        '''Performs a backup of the current save file'''
        start = time.time()
        if os.path.isfile("Worlds/" + self.Name + ".save") == False:
            return
        if os.path.exists("Backups/" + self.Name) == False:
            os.mkdir("Backups/" + self.Name)
        FileName = self.Name + '_' + time.strftime("%d-%m-%Y_%H-%M-%S", time.gmtime()) + '.save'
        shutil.copy("Worlds/" + self.Name + '.save', "Backups/" + self.Name + "/" + FileName)
        if Verbose:
            self.SendNotice("Backed up world in %dms" % (int((time.time() - start) * 1000)))
        self.LastBackup = start

    def SetCoordinatesFromMetaData(self):
        '''Sets up basic convenience member data from the metadata
        ...This is only done for X, Y, and Z as they cannot ever change'''
        self.X = self.GetMetaDataEntry(MetaDataKey.X)
        self.Y = self.GetMetaDataEntry(MetaDataKey.Y)
        self.Z = self.GetMetaDataEntry(MetaDataKey.Z)
    
    def ValidateMetaData(self):
        '''Ensures all required keys are present'''
        assert(self.HasMetaDataEntry(MetaDataKey.X))
        assert(self.HasMetaDataEntry(MetaDataKey.Y))
        assert(self.HasMetaDataEntry(MetaDataKey.Z))
        assert(self.HasMetaDataEntry(MetaDataKey.SpawnX))
        assert(self.HasMetaDataEntry(MetaDataKey.SpawnY))
        assert(self.HasMetaDataEntry(MetaDataKey.SpawnZ))
        assert(self.HasMetaDataEntry(MetaDataKey.SpawnOrientation))
        assert(self.HasMetaDataEntry(MetaDataKey.SpawnPitch))
        assert(self.HasMetaDataEntry(MetaDataKey.CreationDate))
        assert(self.HasMetaDataEntry(MetaDataKey.MinimumBuildRank))
        assert(self.HasMetaDataEntry(MetaDataKey.MinimumJoinRank))
        assert(self.HasMetaDataEntry(MetaDataKey.IsHidden))
    
    #####################################################
    #            Meta-Data acessors and mutators        #
    #####################################################
    def GetMetaDataEntry(self, Key):
        return self.MetaData[Key]
    def SetMetaDataEntry(self, Key, Value):
        self.MetaData[Key] = Value
    def HasMetaDataEntry(self, Key):
        return Key in self.MetaData
    
    def GetSpawnX(self):
        return self.GetMetaDataEntry(MetaDataKey.SpawnX)
    def SetSpawnX(self, Value):
        self.SetMetaDataEntry(MetaDataKey.SpawnX, Value)
    def GetSpawnY(self):
        return self.GetMetaDataEntry(MetaDataKey.SpawnY)
    def SetSpawnY(self, Value):
        self.SetMetaDataEntry(MetaDataKey.SpawnY, Value)
    def GetSpawnZ(self):
        return self.GetMetaDataEntry(MetaDataKey.SpawnZ)    
    def SetSpawnZ(self, Value):
        self.SetMetaDataEntry(MetaDataKey.SpawnZ, Value)
    def GetSpawnOrientation(self):
        return self.GetMetaDataEntry(MetaDataKey.SpawnOrientation)
    def SetSpawnOrientation(self, Value):
        self.SetMetaDataEntry(MetaDataKey.SpawnOrientation, Value)
    def GetSpawnPitch(self):
        return self.GetMetaDataEntry(MetaDataKey.SpawnPitch)
    def SetSpawnPitch(self, Value):
        self.SetMetaDataEntry(MetaDataKey.SpawnPitch, Value)
    
    def IsHidden(self):
        return self.GetMetaDataEntry(MetaDataKey.IsHidden)
    def SetHidden(self, Value):
        self.SetMetaDataEntry(MetaDataKey.IsHidden, Value)
        
    def GetMinimumBuildRank(self):
        return self.GetMetaDataEntry(MetaDataKey.MinimumBuildRank)
    def SetMinimumBuildRank(self, Value):
        self.SetMetaDataEntry(MetaDataKey.MinimumBuildRank, Value)
    def GetMinimumJoinRank(self):
        return self.GetMetaDataEntry(MetaDataKey.MinimumJoinRank)
    def SetMinimumJoinRank(self, Value):
        self.SetMetaDataEntry(MetaDataKey.MinimumJoinRank, Value)
    
    def GetCreationDate(self):
        return self.GetMetaDataEntry(MetaDataKey.CreationDate)
    def SetCreationDate(self, Value):
        self.SetMetaDataEntry(MetaDataKey.CreationDate, Value)
    
    ########################################
    #End of MetaData Accessors and mutators#
    ########################################
    
    #####################################################
    #            DataStore acessors and mutators        #
    #####################################################
    
    def GetDataStoreEntry(self, Key):
        return self.DataStore[Key]
    def SetDataStoreEntry(self, Key, Value):
        self.DataStore[Key] = Value
    def HasDataStoreEntry(self, Key):
        return Key in self.DataStore
    
    def GetGzippedBlockStore(self):
        '''This returns the gzipped block store.
        ...This will most likely contain the value of the store as at
        ...The time of the world being loaded, but this is not guaranteed.
        ...If you are looking for the actual block values. See World.Blocks (self.Blocks)'''
        return self.GetDataStoreEntry(DataStoreKey.Blocks)
    def SetGzippedBlockStore(self, Value):
        '''Sets the value of the gzipped block store,
        ...This has no real use other than to initialise it on a new world'''
        self.SetDataStoreEntry(DataStoreKey.Blocks, Value)
    
    ########################################
    #End of DataStore Accessors and mutators#
    ########################################    

    def SetIdleTimeout(self, Time):
        self.IdleTimeout = Time

    def _CalculateOffset(self, x, y, z):
        return z * (self.X * self.Y) + y * (self.X) + x

    def _CalculateCoords(self, offset):
        x = offset % self.X
        y = (offset // self.X) % self.Y
        z = offset // (self.X * self.Y)
        return x, y, z

    def WithinBounds(self, x, y, z):
        return x >= 0 and x < self.X and y >= 0 and y < self.Y and z >= 0 and z < self.Z

    def AttemptSetBlock(self, pPlayer, x, y, z, val, ResendToClient = False, AutomatedChange = False):
        #TODO: Rewrite this terrible, terrible function
        if not self.WithinBounds(x, y, z):
            return True #Cant set that block. But don't return False or it'll try "undo" the change!
        if val >= BLOCK_END:
            return False #Fake block type...
        ArrayValue = self._CalculateOffset(x, y, z)
        if ord(self.Blocks[ArrayValue]) == val:
            return  
        if pPlayer.HasPermission(self.GetMinimumBuildRank()) == False:
            pPlayer.SendMessage(self.MinRankMessage)
            return False              
        #Too far away!
        if not AutomatedChange and pPlayer.CalcDistance(x, y, z) > 10 and pPlayer.GetRank() == 'guest':
            return False
        if pPlayer.GetAboutCmd() == True:
            self.HandleAboutCmd(pPlayer, x, y, z)
            return False  
        
        if not AutomatedChange:
            if (val in WaterBlocks and not pPlayer.HasPermission(self.ServerControl.WaterRank)) or (val in LavaBlocks and not pPlayer.HasPermission(self.ServerControl.LavaRank)) or (val == BLOCK_HARDROCK and not pPlayer.HasPermission(self.ServerControl.PlaceAdmincreteRank)):
                   pPlayer.SendMessage("&RYou do not have the required rank to place that block!")
                   return False

        #Plugins
        PluginResult = self.ServerControl.PluginMgr.OnAttemptPlaceBlock(self, pPlayer, val, x, y, z)
        if PluginResult != True:
            if PluginResult == False:
                return False
            else:
                return True #Fail silently (Will rewrite this if we end up needing multiple return types for other plugin hooks
        #Temporary code to make "steps" function normally.
        if val == BLOCK_STEP and z > 0:
            BlockBelow = self._CalculateOffset(x, y, z - 1)
            if ord(self.Blocks[BlockBelow]) == BLOCK_STEP:
                if  self.AttemptSetBlock(pPlayer, x, y, z - 1, BLOCK_DOUBLESTEP, True, AutomatedChange):
                    return False
        if ord(self.Blocks[ArrayValue]) == BLOCK_HARDROCK:
            if pPlayer.HasPermission(self.ServerControl.AdmincreteRank) == False:
                pPlayer.SendMessage("&RYou are not allowed to delete bedrock")
                return False
        if self.LogBlocks == True:
            self.BlockHistory[ArrayValue] = BlockLog(pPlayer.GetName().lower(), int(self.ServerControl.Now), self.Blocks[ArrayValue])
        if len(self.BlockHistory) >= self.LogFlushThreshold:
            self.FlushBlockLog()    
        self.SetBlock(pPlayer, x, y, z, val, ResendToClient)
        return True

    def SetBlock(self, pPlayer, x, y, z, val, ResendToClient = False):
        #Changes a block to a certain value.
        ArrayValue = self._CalculateOffset(x, y, z)
        cval = chr(val)
        if self.Blocks[ArrayValue] == cval:
            return
        OldValue = ord(self.Blocks[ArrayValue])
        self.Blocks[ArrayValue] = cval
        self.IsDirty = True
        self.ServerControl.PluginMgr.OnPostPlaceBlock(self, pPlayer, OldValue, val, x, y, z)
        if self.IsLocked == True:
            return
        Packet = PacketWriter.MakeBlockSetPacket(x, z, y, val)
        if not ResendToClient:
            self.SendPacketToAllButOne(Packet, pPlayer)
        else:
            self.SendPacketToAll(Packet)
        
    def GetBlock(self, x, y, z):
        '''Returns the numeric value of a block on the map
        ...Throws exception if coordinates are out of bounds'''
        return ord(self.Blocks[self._CalculateOffset(x, y, z)])
       
    def HandleAboutCmd(self, pPlayer, x, y, z):
        #Display block information
        BlockInfo = self.GetBlockLogEntry(x, y, z)
        if BlockInfo is not None:
            self.SendAboutInfo(pPlayer, BlockInfo)
        else:
            #Query database
            pPlayer.SendMessage("&SQuerying database. This may take a few moments")
            Query = "SELECT Username,Time,Oldvalue FROM Blocklogs where Offset = ?"
            QueryParameters = (self._CalculateOffset(x, y, z),)
            kwArgs = {"pPlayer": pPlayer.GetName(), "ServerControl": self.ServerControl, "World":self}
            self.AsynchronousQuery(Query, QueryParameters, World.AboutCmdCallback, kwArgs)
            
        pPlayer.SetAboutCmd(False)
        
    @staticmethod
    def AboutCmdCallback(Results, kwArgs, isException):
        '''Called when the query for the blocklog returns'''
        ServerControl = kwArgs["ServerControl"]
        self = kwArgs["World"]
        pPlayer = ServerControl.GetPlayerFromName(kwArgs["pPlayer"])
        if pPlayer is None:
            return
        if len(Results) == 0:
            pPlayer.SendMessage("&SNo information available for this block (No changes made)")
            return
        Row = Results[0]
        self.SendAboutInfo(pPlayer, BlockLog(Row[0], Row[1], chr(Row[2])))
        
    def SendAboutInfo(self, pPlayer, BlockInfo):
        if BlockInfo is None:
            pPlayer.SendMessage("&SNo information available for this block (No changes made)")
        else:
            now = int(self.ServerControl.Now)
            pPlayer.SendMessage("&SThis block was last changed by &V%s" % BlockInfo.Username)
            pPlayer.SendMessage("&SThe old block was: &V%s" % GetBlockNameFromID(ord(BlockInfo.Value)))
            pPlayer.SendMessage("&SChanged &V%s &Sago" % ElapsedTime(now - BlockInfo.Time))        
    
    def UndoActions(self, Username, ReversePlayer, Time):
        self.FlushBlockLog()
        #Reverse stuff in SQL DB
        self.IOThread.Tasks.put(["UNDO_ACTIONS", Username.lower(), ReversePlayer.lower(), Time])

    def AddBlockChanges(self, BlockChangeList):
        self.AsyncBlockChanges.put(BlockChangeList)
        
    def AddAsyncQueryResult(self, QueryResult):
        self.AsyncQueryCallbacks.put(QueryResult)

    def AsynchronousQuery(self, Query, QueryParameters, CallbackFunc, kwArgs):
        '''Performs and query on the player DB asynchronously, calling 
           CallbackFunc with the results when done'''
        self.IOThread.Tasks.put(["ASYNC_QUERY", Query, QueryParameters, CallbackFunc, kwArgs])

    def GetBlockLogEntry(self, X, Y, Z):
        '''Attempts to return a Blocklog entry from memory'''
        Offset = self._CalculateOffset(X, Y, Z)
        #First check our hashmap.
        Result = self.BlockHistory.get(Offset, None)
        return Result


    def FlushBlockLog(self):
        '''Tells the IO Thread to Flush out the blockhistory to the disk'''
        self.IOThread.Tasks.put(["FLUSH", self.BlockHistory])
        self.BlockHistory = dict()


    def SetSpawn(self, x, y, z, o, p):
        '''Sets the worlds default spawn position. Stored in the format the client uses (pixels)'''
        self.SetSpawnX(x)
        self.SetSpawnY(y)
        self.SetSpawnZ(z)
        self.SetSpawnOrientation(o)
        self.SetSpawnPitch(p)

    def InitialiseBuiltInMetaData(self):
        '''Inserts all the mandatory, built in meta data
        ...This is called after GenerateGenericWorld. 
        ...So some values are inserted there.'''
        self.SetMetaDataEntry(MetaDataKey.X, self.X)
        self.SetMetaDataEntry(MetaDataKey.Y, self.Y)
        self.SetMetaDataEntry(MetaDataKey.Z, self.Z)
        #Spawn values should be set at this stage.
        self.SetCreationDate(int(self.ServerControl.Now))
        self.SetMinimumBuildRank('guest')
        self.SetMinimumJoinRank('spectator')
        self.SetHidden(False)
    
    def InitialiseBuiltInDataStore(self):
        '''Insert all the mandatory, built in data store entries
        ...This is called after GenerateGenericWorld. 
        ...So some values are inserted there.'''
        pass
        
    def GenerateGenericWorld(self, x = 512, y = 512, z = 96):
        '''Generates a flatgrass world'''
        self.X, self.Y, self.Z = x, y, z
        GrassLevel = self.Z / 2
        SandLevel = GrassLevel - 2
        self.SetSpawnX(self.X / 2 * 32)
        self.SetSpawnY(self.Y / 2 * 32)
        self.SetSpawnZ((self.Z / 2 + 2) * 32 + 51)
        self.SetSpawnOrientation(0)
        self.SetSpawnPitch(0)
        
        self.Blocks = array('c')
        self.Blocks.fromstring((self.X * self.Y) * chr(BLOCK_ROCK) * (SandLevel - 1))
        self.Blocks.fromstring((self.X * self.Y) * chr(BLOCK_DIRT) * 2)
        self.Blocks.fromstring((self.X * self.Y) * chr(BLOCK_GRASS))
        self.Blocks.fromstring((self.X * self.Y) * chr(BLOCK_AIR) * GrassLevel)
        
        self.IsDirty = True
        self.InitialiseBuiltInMetaData()
        self.InitialiseBuiltInDataStore()
        self.ServerControl.SetWorldMetaData(self.Name, self.MetaData)
        self.Save(False)

    def Unload(self, ShouldSave = True):
        #Remove players..
        for pPlayer in self.Players:
            pPlayer.Disconnect("The world you were on was deleted. Please reconnect")
            pPlayer.SetWorld(None)
        self.ServerControl.UnloadWorld(self)
        if ShouldSave:
            self.Save(True)
        self.CurrentSaveThread = None
        self.Unloaded = True
        if self.LogBlocks:
            self.FlushBlockLog()
            self.IOThread.Shutdown(False)
            self.DBConnection.commit()
            self.DBConnection.close()
            self.DBConnection = None
            self.DBCursor = None
        self.ServerControl.PluginMgr.OnWorldUnload(self)

    def Run(self):
        if self.Unloaded == True:
            return
        if self.IdleTimeout != 0 and len(self.Players) == 0:
            if self.IdleStart != 0:
                if self.IdleStart + self.IdleTimeout < self.ServerControl.Now and self.CanUnload:
                    self.Unload()
                    return
            else:
                self.IdleStart = self.ServerControl.Now
        elif self.IdleStart != 0:
            self.IdleStart = 0

        if self.LastSave + self.SaveInterval < self.ServerControl.Now:
            self.Save()
        if self.LastBackup + self.BackupInterval < self.ServerControl.Now:
            self.Backup()
        #Check for pending block changes from the IO Thread
        #This is only used when Blockhistory is enabled.
        if self.LogBlocks == True:
            while True:
                try:
                    Data = self.AsyncBlockChanges.get_nowait()
                except Queue.Empty:   
                    break
                #Data is a list where the 0th element is a string of
                #the username who initiated the block changes
                #The 1th element is the player whos actions have been reversed
                #The 2th element is the number of blocks changed (from the hashmap, and from disk)
                #The rest of the elements are BlockChange objects
                Username = Data[0]
                ReversedPlayer = Data[1]
                NumChanged = Data[2]
                if NumChanged > LOCK_LEVEL:
                    self.Lock()
                for i in xrange(3, len(Data)):
                    x, y, z = self._CalculateCoords(Data[i].Offset)
                    self.SetBlock(None, x, y, z, Data[i].Value)
                Initiator = self.ServerControl.GetPlayerFromName(Username)
                if Initiator:
                    Initiator.SendMessage("&SFinished reversing %s's actions" % ReversedPlayer)
                if NumChanged > 0:
                    self.ServerControl.SendNotice("Antigrief: %s's actions have been reversed." % ReversedPlayer)
                elif Initiator and NumChanged == 0:
                    Initiator.SendMessage("&R%s had no block history!" % ReversedPlayer)
                if NumChanged > LOCK_LEVEL:
                    self.UnLock()
                    
        while True:
            try:
                QueryResult = self.AsyncQueryCallbacks.get_nowait()
                QueryResult.Callback()
            except Queue.Empty:
                break
            
        while len(self.JoiningPlayers) > 0:
            pPlayer = self.JoiningPlayers.pop()
            self.Players.append(pPlayer)
            pPlayer.SetWorld(self)
            pPlayer.SetId(pPlayer.GetNewId())
            self.SendWorld(pPlayer)
        for pPlayer in self.Players:
            pPlayer.ProcessPackets()
        #Transferring players will now have all players leaving.
        while len(self.TransferringPlayers) > 0:
            self.Players.remove(self.TransferringPlayers.pop())

    def Shutdown(self, Crash):
        self.Save(False)
        self.Backup(False)
        if self.LogBlocks:
            self.FlushBlockLog()
            self.IOThread.Shutdown(Crash)

    def IsFull(self):
        return len(self.PlayerIDs) == 0

    def Lock(self):
        '''Locks the worlds blocks. Any changes made after the world is locked
        ...Will not be sent to the clients. Unlock() Should be called
        ...after all changes have been made'''
        self.IsLocked = True
        for pPlayer in self.Players:
            self._RemoveAllPlayersFromView(pPlayer)
        
    def UnLock(self):
        '''Unlocks the worlds blocklogs. All clients on the map will have the
        ...updated level sent to them again as gzipped chunks
        ...This is useful as the client lags when it receives large volumes of chunk updates'''
        self.IsLocked = False
        for pPlayer in self.Players:
            pPlayer.SetSpawnPosition(pPlayer.GetX(), pPlayer.GetY(), pPlayer.GetZ(), pPlayer.GetOrientation(), pPlayer.GetPitch())
            self.SendWorld(pPlayer)
            
    def SendWorld(self, pPlayer):
        '''Sends the gzipped level to the client'''
        Packet = chr(SMSG_PRECHUNK)
        pPlayer.SendPacket(Packet)
        if self.IsDirty:
            StringHandle = cStringIO.StringIO()
            fHandle = gzip.GzipFile(fileobj = StringHandle, mode = "wb", compresslevel = self.CompressionLevel)
            fHandle.write(self.NetworkSize)
            fHandle.write(self.Blocks)
            fHandle.close()
            self.IsDirty = False
            self.BlockCache = StringHandle
        else:
            StringHandle = self.BlockCache
        TotalBytes = StringHandle.tell()
        StringHandle.seek(0)
        Chunk = StringHandle.read(1024)
        CurBytes = 0
        while len(Chunk) > 0:
            ChunkSize = len(Chunk)
            CurBytes += ChunkSize
            Packet = PacketWriter.MakeChunkPacket(ChunkSize, Chunk, int(100.0 * (float(CurBytes) / TotalBytes)))
            pPlayer.SendPacket(Packet)
            Chunk = StringHandle.read(1024)

        if self.DisableBots:
            #Sending this causes InsideBots draw commands to break
            BadPacket = PacketWriter.MakeIdentifcationPacket("Finished loading world: %s" % self.Name,
                         self.ServerControl.Motd,
                         0x64 if pPlayer.HasOpFlags() else 0x00)
            pPlayer.SendPacket(BadPacket)
            
        Packet2 = PacketWriter.MakeLevelSizePacket(self.X, self.Z, self.Y)
        pPlayer.SendPacket(Packet2)

        pPlayer.SetLocation(self.GetSpawnX(), self.GetSpawnY(), self.GetSpawnZ(), self.GetSpawnOrientation(), self.GetSpawnPitch())

        Packet3 = None
        if pPlayer.GetSpawnPosition()[0] == -1:
            Packet3 = PacketWriter.MakeSpawnPointPacket(255, pPlayer.GetColouredName(), self.GetSpawnX(), self.GetSpawnZ(), self.GetSpawnY(),
                                                    self.GetSpawnOrientation(), self.GetSpawnPitch())
        else:
            Location = pPlayer.GetSpawnPosition()
            pPlayer.SetSpawnPosition(-1, -1, -1, -1, -1)
            Packet3 = PacketWriter.MakeSpawnPointPacket(255, pPlayer.GetColouredName(), Location[0], Location[2], Location[1],
                                                    Location[3], Location[4])            
            
        pPlayer.SendPacket(Packet3)
        self.SendPlayerJoined(pPlayer)
        self.SendAllPlayers(pPlayer)



    def RemovePlayer(self, pPlayer, ChangingMaps = False):
        if not ChangingMaps:
            self.Players.remove(pPlayer)
        #Send Some packets to local players...
        Packet = PacketWriter.MakeDespawnPacket(pPlayer.GetId())
        self.SendPacketToAllButOne(Packet, pPlayer)
        self.PlayerIDs.append(pPlayer.GetId()) #release the ID
        if ChangingMaps:
            self._RemoveAllPlayersFromView(pPlayer)
            self.TransferringPlayers.append(pPlayer)

    def SendBlock(self, pPlayer, x, y, z):
        #We can trust that these coordinates will be within bounds.
        Packet = PacketWriter.MakeBlockSetPacket(x, z, y, ord(self.Blocks[self._CalculateOffset(x, y, z)]))
        pPlayer.SendPacket(Packet)
        
    def AddPlayer(self, pPlayer):
        self.JoiningPlayers.append(pPlayer)
        pPlayer.SetNewId(self.PlayerIDs.pop())

    def SendPlayerJoined(self, pPlayer):
        Packet = PacketWriter.MakeSpawnPointPacket(pPlayer.GetId(), pPlayer.GetColouredName(),
                    pPlayer.GetX(), pPlayer.GetZ(), pPlayer.GetY(),
                    pPlayer.GetOrientation(), pPlayer.GetPitch())
        for nPlayer in self.Players:
            if nPlayer != pPlayer and pPlayer.CanBeSeenBy(nPlayer):
                nPlayer.SendPacket(Packet)

    def _RemoveAllPlayersFromView(self, pPlayer):
        for nPlayer in self.Players:
            if nPlayer != pPlayer:
                Packet = PacketWriter.MakeDespawnPacket(nPlayer.GetId())
                pPlayer.SendPacket(Packet)

    def SendAllPlayers(self, Client):
        for pPlayer in self.Players:
            if pPlayer != Client and pPlayer.CanBeSeenBy(Client):
                Packet = PacketWriter.MakeSpawnPointPacket(pPlayer.GetId(), pPlayer.GetColouredName(),
                    pPlayer.GetX(), pPlayer.GetZ(), pPlayer.GetY(),
                    pPlayer.GetOrientation(), pPlayer.GetPitch())
                Client.SendPacket(Packet)

    def SendNotice(self, Message):
        Packet = PacketWriter.MakeMessagePacket(0, self.ServerControl.ConvertColours(("&N" + Message)))
        self.SendPacketToAll(Packet)
        
    def SendJoinMessage(self, Message):
        Packet = PacketWriter.MakeMessagePacket(0, self.ServerControl.ConvertColours(("&N" + Message)))
        for pPlayer in self.Players:
            if pPlayer.GetJoinNotifications():
                pPlayer.SendPacket(Packet)
    def SendPacketToAll(self, Packet):
        '''Distributes a packet to all clients on a map
            *ANY CHANGES TO THIS FUNCTION NEED TO BE MADE TO Player::SendPacket!'''
        for pPlayer in self.Players:
            pPlayer.OutBuffer.append(Packet)
    def SendPacketToAllButOne(self, Packet, Client):
        '''Distributes a packet to all clients on a map
            *ANY CHANGES TO THIS FUNCTION NEED TO BE MADE TO Player::SendPacket!'''
        for pPlayer in self.Players:
            if pPlayer != Client:
                pPlayer.OutBuffer.append(Packet)
                
    @staticmethod
    def GetMetaData(Name):
        '''Loads metadata from the world file, return type is the MetaDataDictionary
        ...It does not ensure the metadata contains all necessary keys'''
        with open("Worlds/%s.save" % Name) as fHandle:
            Version = struct.unpack("h", fHandle.read(2))[0]
            if Version == 1:
                Console.Error("World", "You have not run the 0.1 to 0.2 update. Refer to the readme for more information")
                raise WorldRequiresUpdateException("World file %s out of date" % Name)
            elif Version != World.VERSION:
                raise Exception("World file %s has unknown version" % Name)
            MetaDataLen = struct.unpack("i", fHandle.read(4))[0]
            EncodedJson = fHandle.read(MetaDataLen)
            MetaData = JSONDict.FromJSON(EncodedJson)
            return MetaData
    
