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
from core.opticraftpacket import OptiCraftPacket
from core.constants import *
from core.zones import Zone
from core.console import *

#Used for deciding whether to lock a map when undoing actions
#Tweak appropriately
LOCK_LEVEL = 10000 #Number of blocks needed in order to force a map lock

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
        threading.Thread.__init__(self)
        self.pWorld = pWorld
        self.X, self.Y, self.Z = pWorld.X, pWorld.Y, pWorld.Z
        self.SpawnX, self.SpawnY, self.SpawnZ = pWorld.SpawnX, pWorld.SpawnY, pWorld.SpawnZ
        self.SpawnOrientation, self.SpawnPitch = pWorld.SpawnOrientation, pWorld.SpawnPitch
        self.MetaData = copy.copy(pWorld.MetaData)
        self.Blocks = copy.copy(pWorld.Blocks)
        self.Name = pWorld.Name
        self.Verbose = Verbose
        self.CompressionLevel = pWorld.CompressionLevel
        
    def run(self):
        self.Save(self.Verbose)
    def Save(self, Verbose = True):
        '''The map file is a file of the following format:
        int16 VersionNumber
        int16 X
        int16 Y
        int16 Z
        int16 SpawnX
        int16 SpawnY
        int16 SpawnZ
        int16 SpawnOrientation
        int16 SpawnPitch
        int32 MetaDataLength (number of elements)
              MetaDataLength *2 Length delimited strings of Key/Value
        array* gzipped Blockstore till EOF
        '''
        start = time.time()
        try:
            #Save to a temp file. Then copy it over. (If we crash during this, the old save is unchanged)
            #...Crashes may occur if we run out of memory, so do not change this!
            fHandle = open("Worlds/%s.temp" % (self.Name), 'wb')
        except:
            Console.Error("World", "Failed to saved world %s to disk." % self.Name)
        fHandle.write(struct.pack("h", 1)) #Map version number
        fHandle.write(struct.pack("h", self.X))
        fHandle.write(struct.pack("h", self.Y))
        fHandle.write(struct.pack("h", self.Z))
        fHandle.write(struct.pack("h", self.SpawnX))
        fHandle.write(struct.pack("h", self.SpawnY))
        fHandle.write(struct.pack("h", self.SpawnZ))
        fHandle.write(struct.pack("h", self.SpawnOrientation))
        fHandle.write(struct.pack("h", self.SpawnPitch))
        #Meta data saving.
        fHandle.write(struct.pack("i", len(self.MetaData))) #Number of elements to be saved
        for Key in self.MetaData:
            fHandle.write(World._MakeLengthString(Key))
            fHandle.write(World._MakeLengthString(self.MetaData[Key]))
        #Block Array
        gzipHandle = gzip.GzipFile(fileobj = fHandle, mode = "wb", compresslevel = self.CompressionLevel)
        gzipHandle.write(self.Blocks.tostring())
        gzipHandle.close()
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
        threading.Thread.__init__(self)
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
        try:
            self.DBConnection.execute(Query, Parameters)
            self.DBConnection.commit()
        except dbapi.OperationalError:
            Console.Warning("IOThread", "Failed to execute Query. Trying again soon")
            self.Tasks.put(["EXECUTE", Query, Parameters])
    def _ConnectTask(self):
        self.DBConnection = dbapi.connect("Worlds/BlockLogs/%s.db" % self.WorldName)
        self.DBConnection.text_factory = str

    def _FlushBlocksTask(self, Data):
        start = time.time()
        for key in Data:
            SuccessfulQuery = False
            while SuccessfulQuery != True:
                try:
                    BlockInfo = Data[key]
                    self.DBConnection.execute("REPLACE INTO Blocklogs VALUES(?,?,?,?)", (key, BlockInfo.Username, BlockInfo.Time, ord(BlockInfo.Value)))
                except dbapi.OperationalError:
                    time.sleep(0.05) #Tiny sleep to prevent slamming the DB while its locked.
                    continue
                else:
                    SuccessfulQuery = True
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
        Row = SQLResult.fetchone()
        BlockChangeList = [Username, ReverseName, 0]
        NumChanged = 0
        while Row != None:
            BlockChangeList.append(BlockChange(Row[0], Row[1]))
            NumChanged += 1
            Row = SQLResult.fetchone()
        BlockChangeList[2] = NumChanged
        self.World.AddBlockChanges(BlockChangeList)
        try:
            Console.Debug("IOThread", "Failed to clean up undoactions. Trying again later.")
            self.DBConnection.execute("DELETE FROM Blocklogs where Username = ? and Time > ?", (ReverseName, now - Time))
            self.DBConnection.commit()
        except dbapi.OperationalError:
            self.Tasks.put(["EXECUTE"], "DELETE FROM Blocklogs where Username = ? and Time > ?", (ReverseName, now - Time))
        Console.Debug("IOThread", "%s reversed %s's actions. %d changed in %f seconds" % (Username, ReverseName, NumChanged, time.time() - now))

    def Shutdown(self, Crash):
        self.Tasks.put(["SHUTDOWN"])
        
class WorldLoadFailedException(Exception):
    pass
class World(object):
    def __init__(self, ServerControl, Name, NewMap = False, NewX = -1, NewY = -1, NewZ = -1):
        self.Blocks = array("c")
        self.BlockCache = cStringIO.StringIO()
        self.IsDirty = True
        self.IsLocked = False
        self.Players = set()
        self.TransferringPlayers = list()
        self.JoiningPlayers = list()
        self.Name = Name
        self.X, self.Y, self.Z = -1, -1, -1
        self.SpawnX, self.SpawnY, self.SpawnZ = -1, -1, -1
        self.SpawnOrientation, self.SpawnPitch = 0, 0
        self.MetaData = dict()
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
        self.LogFlushThreshold = int(self.ServerControl.ConfigValues.GetValue("worlds", "LogFlushThreshold", 100000))
        self.DisableBots = bool(int(self.ServerControl.ConfigValues.GetValue("server", "DisableBots", "0")))
        self.IOThread = None
        self.CurrentSaveThread = None
        self.AsyncBlockChanges = Queue.Queue()
        self.IdleTimeout = 0 #How long must the world be unoccupied until it unloads itself from memory
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

        self.Zones = list()
        self.ServerControl.InsertZones(self) #Servercontrol manages all the zones
        self.ServerControl.PluginMgr.OnWorldLoad(self)

    @staticmethod
    def _ReadLengthString(FileHandle):
        Val = struct.unpack("i", FileHandle.read(4))[0]
        return FileHandle.read(Val)
    @staticmethod
    def _MakeLengthString(String):
        return struct.pack("i", len(String)) + String
    
    def Load(self):
        '''The map file is a file of the following format:
        int16 VersionNumber
        int16 X
        int16 Y
        int16 Z
        int16 SpawnX
        int16 SpawnY
        int16 SpawnZ
        int16 SpawnOrientation
        int16 SpawnPitch
        int32 MetaDataLength (number of elements)
              MetaDataLength *2 Length delimited strings of Key/Value
        array* gzipped Blockstore till EOF
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
            if Version != 1:
                Console.Error("World", "Unknown map version %d found on world %s. Unable to load." % (Version, self.Name))
                return False
            self.X = struct.unpack("h", rHandle.read(2))[0]
            self.Y = struct.unpack("h", rHandle.read(2))[0]
            self.Z = struct.unpack("h", rHandle.read(2))[0]
            self.SpawnX = struct.unpack("h", rHandle.read(2))[0]
            self.SpawnY = struct.unpack("h", rHandle.read(2))[0]
            self.SpawnZ = struct.unpack("h", rHandle.read(2))[0]
            self.SpawnOrientation = struct.unpack("h", rHandle.read(2))[0]
            self.SpawnPitch = struct.unpack("h", rHandle.read(2))[0]
            MetaLength = struct.unpack("i", rHandle.read(4))[0]
            for i in xrange(MetaLength):
                Key = World._ReadLengthString(rHandle)
                Value = World._ReadLengthString(rHandle)
                self.MetaData[Key] = Value
            gzipHandle = gzip.GzipFile(fileobj = rHandle, mode = "rb")
            self.Blocks.fromstring(gzipHandle.read())
            gzipHandle.close()                
            rHandle.close()
            Console.Out("World", "Loaded world %s in %dms" % (self.Name, int((time.time() - start) * 1000)))
            #Ensure the data is not corrupt in some way
            assert(len(self.Blocks) == self.X * self.Y * self.Z)
            try:
                int(self.MetaData["hidden"])
            except:
                self.MetaData["hidden"] = "0"
            try:
                if self.ServerControl.IsValidRank(self.MetaData["minrank"]) == False:
                    raise Exception()
            except:
                self.MetaData["minrank"] = "guest"
        except:
            Console.Warning("World", "Failed to load map '%s'.save The save file is out of date or corrupt." % self.Name)
            return False
    
    def Save(self, Verbose = True):
        '''The map file is a file of the following format:
        int16 VersionNumber
        int16 X
        int16 Y
        int16 Z
        int16 SpawnX
        int16 SpawnY
        int16 SpawnZ
        int16 SpawnOrientation
        int16 SpawnPitch
        int32 MetaDataLength (number of elements)
              MetaDataLength *2 Length delimited strings of Key/Value
        array* gzipped Blockstore till EOF
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

    def InsertZone(self, pZone):
        self.Zones.append(pZone)
    def GetZone(self, Name):
        Name = Name.lower()
        for pZone in self.Zones:
            if pZone.Name.lower() == Name:
                return pZone
        return None
    def GetZones(self):
        return self.Zones
    def DeleteZone(self, pZone):
        self.Zones.remove(pZone)

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
        if pPlayer.HasPermission(self.GetMinRank()) == False:
            pPlayer.SendMessage("&RYou do not have the required rank to build on this world")
            return False
        ArrayValue = self._CalculateOffset(x, y, z)
        if ord(self.Blocks[ArrayValue]) == val:
            return        
        #Too far away!
        if not AutomatedChange and pPlayer.CalcDistance(x, y, z) > 10 and pPlayer.GetRank() == 'guest':
            return False
        #Plugins
        if self.ServerControl.PluginMgr.OnAttemptPlaceBlock(self, pPlayer, val, x, y, z) == False:
            return False
        if pPlayer.GetAboutCmd() == True:
            #Display block information
            try:
                BlockInfo = self.GetBlockLogEntry(x, y, z)
            except dbapi.OperationalError:
                pPlayer.SendMessage("&RDatabase is busy, try again in a few moments.")
                return False
            
            if BlockInfo is None:
                pPlayer.SendMessage("&SNo information available for this block (No changes made)")
            else:
                now = int(self.ServerControl.Now)
                pPlayer.SendMessage("&SThis block was last changed by &V%s" % BlockInfo.Username)
                pPlayer.SendMessage("&SThe old block was: &V%s" % GetBlockNameFromID(ord(BlockInfo.Value)))
                pPlayer.SendMessage("&SChanged &V%s &Sago" % ElapsedTime(now - BlockInfo.Time))
            pPlayer.SetAboutCmd(False)
            return False
        #ZONES!
        if self.CheckZones(pPlayer, x, y, z) == False:
            return False
        if not AutomatedChange and val in DisabledBlocks and pPlayer.GetBlockOverride() != val:
            pPlayer.SendMessage("&RThat block is disabled!")
            return False
        
        #Zone creation
        if pPlayer.IsCreatingZone():
            zData = pPlayer.GetZoneData()
            if zData["Phase"] == 1:
                #Placing the first corner of the zone.
                zData["X1"] = x
                zData["Y1"] = y
                zData["Z1"] = z
                zData["Phase"] = 2
                pPlayer.SendMessage("&SNow place the final corner for the zone.")
                return True
            elif zData["Phase"] == 2:
                FileName = Zone.Create(zData["Name"], zData["X1"], x, zData["Y1"], y, zData["Z1"] - 1, z - 1, zData["Height"], zData["Owner"], self.Name)
                pZone = Zone(FileName, self.ServerControl)
                self.Zones.append(pZone)
                self.ServerControl.AddZone(pZone)
                pPlayer.SendMessage("&SSuccessfully created zone \"%s\"" % zData["Name"])
                #hide the starting block for the zone
                self.SendBlock(pPlayer, zData["X1"], zData["Y1"], zData["Z1"])
                pPlayer.FinishCreatingZone()
                return False

        #Temporary code to make "steps" function normally.
        if val == BLOCK_STEP and z > 0:
            BlockBelow = self._CalculateOffset(x, y, z - 1)
            if ord(self.Blocks[BlockBelow]) == BLOCK_STEP:
                if self.CheckZones(pPlayer, x, y, z - 1) != False:
                    self.SetBlock(None, x, y, z - 1, BLOCK_DOUBLESTEP)
                    return False
        if ord(self.Blocks[ArrayValue]) == BLOCK_HARDROCK:
            if pPlayer.HasPermission(self.ServerControl.AdmincreteRank) == False:
                #not allowed to delete admincrete
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
        self.Blocks[ArrayValue] = cval
        self.IsDirty = True
        self.ServerControl.PluginMgr.OnPostPlaceBlock(self, pPlayer, val, x, y, z)
        if self.IsLocked == True:
            return
        Packet = OptiCraftPacket(SMSG_BLOCKSET)
        Packet.WriteInt16(x)
        Packet.WriteInt16(z)
        Packet.WriteInt16(y)
        Packet.WriteByte(val)
        if not ResendToClient:
            self.SendPacketToAllButOne(Packet, pPlayer)
        else:
            self.SendPacketToAll(Packet)
        
    def CheckZones(self, pPlayer, x, y, z):
        for pZone in self.Zones:
            if pZone.IsInZone(x, y, z):
                if pZone.CanBuild(pPlayer) == False:
                    pPlayer.SendMessage("&RYou cannot build in zone \"%s\"" % pZone.Name)
                    return False
        return True
    
    def GetBlock(self, x, y, z):
        '''Returns the numeric value of a block on the map
        ...Throws exception if coordinates are out of bounds'''
        return ord(self.Blocks[self._CalculateOffset(x, y, z)])
                
    def UndoActions(self, Username, ReversePlayer, Time):
        self.FlushBlockLog()
        #Reverse stuff in SQL DB
        self.IOThread.Tasks.put(["UNDO_ACTIONS", Username.lower(), ReversePlayer.lower(), Time])

    def AddBlockChanges(self, BlockChangeList):
        self.AsyncBlockChanges.put(BlockChangeList)

    def GetBlockLogEntry(self, X, Y, Z):
        '''Attempts to return a Blocklog entry'''
        Offset = self._CalculateOffset(X, Y, Z)
        #First check our hashmap.
        Result = self.BlockHistory.get(Offset, None)
        if Result != None:
            #Easy peezy...
            return Result
        #Turn to SQL - This can throw an exception that needs to be handled!
        self.DBCursor.execute("SELECT Username,Time,Oldvalue FROM Blocklogs where Offset = ?", (Offset,))
        SQLResult = self.DBCursor.fetchone()
        if SQLResult is None:
            return None
        else:
            return BlockLog(SQLResult[0], SQLResult[1], chr(SQLResult[2]))

    def FlushBlockLog(self):
        '''Tells the IO Thread to Flush out the blockhistory to the disk'''
        self.IOThread.Tasks.put(["FLUSH", self.BlockHistory])
        self.BlockHistory = dict()


    def SetSpawn(self, x, y, z, o, p):
        '''Sets the worlds default spawn position. Stored in the format the client uses (pixels)'''
        self.SpawnX = x
        self.SpawnY = y
        self.SpawnZ = z
        self.SpawnOrientation = o
        self.SpawnPitch = p



    def GenerateGenericWorld(self, x = 512, y = 512, z = 96):
        self.X, self.Y, self.Z = x, y, z
        GrassLevel = self.Z / 2
        SandLevel = GrassLevel - 2
        self.SpawnY = self.Y / 2 * 32
        self.SpawnX = self.X / 2 * 32
        self.SpawnZ = (self.Z / 2 + 2) * 32 + 51
        self.SpawnOrientation = 0
        self.SpawnPitch = 0
        self.Blocks = array('c')
        for z in xrange(self.Z):
            if z < SandLevel:
                Block = chr(BLOCK_ROCK)
            elif z >= SandLevel and z < GrassLevel:
                Block = chr(BLOCK_SAND)
            elif z == GrassLevel:
                Block = chr(BLOCK_GRASS)
            else:
                Block = chr(BLOCK_AIR)
            self.Blocks.fromstring((self.X * self.Y) * Block)
        self.MetaData["hidden"] = '0'
        self.MetaData["minrank"] = "guest"
        self.IsDirty = True
        self.Save(False)

    def SetMetaData(self, Key, Value):
        self.MetaData[Key] = Value
    def IsHidden(self):
        return int(self.MetaData["hidden"])
    def SetHidden(self, Value):
        self.SetMetaData("hidden", str(Value))
    def GetMinRank(self):
        return self.MetaData["minrank"]
    def SetMinRank(self, Value):
        self.SetMetaData("minrank", Value)
    def Unload(self):
        #Remove players..
        for pPlayer in self.Players:
            #Super lazy mode =|
            pPlayer.Disconnect("The world you were on was deleted. Please reconnect")
            pPlayer.SetWorld(None)
        self.ServerControl.UnloadWorld(self)
        self.Save(True)
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
                if self.IdleStart + self.IdleTimeout < self.ServerControl.Now:
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

        while len(self.JoiningPlayers) > 0:
            pPlayer = self.JoiningPlayers.pop()
            self.Players.add(pPlayer)
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
        ...This is useful as the client lags when it recieves large volumes of chunk updates'''
        self.IsLocked = False
        for pPlayer in self.Players:
            Packet = OptiCraftPacket(SMSG_INITIAL)
            Packet.WriteByte(7)
            Packet.WriteString("Reloading map...")
            Packet.WriteString("The map is being refreshed");
            if pPlayer.HasPermission(self.ServerControl.AdmincreteRank):
                Packet.WriteByte(0x64)
            else:
                Packet.WriteByte(0x00)
            pPlayer.SetSpawnPosition(pPlayer.GetX(), pPlayer.GetY(), pPlayer.GetZ(), pPlayer.GetOrientation(), pPlayer.GetPitch())
            self.SendWorld(pPlayer)
            pPlayer.SendPacket(Packet)
            
    def SendWorld(self, pPlayer):
        '''Sends the gzipped level to the client'''
        Packet = OptiCraftPacket(SMSG_PRECHUNK)
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
            Packet = OptiCraftPacket(SMSG_CHUNK)
            Packet.WriteInt16(ChunkSize)
            Packet.WriteKBChunk(Chunk)
            Packet.WriteByte(100.0 * (float(CurBytes) / float(TotalBytes)))
            pPlayer.SendPacket(Packet)
            Chunk = StringHandle.read(1024)
            
        if self.DisableBots:
            #Sending this causes InsideBots draw commands to break
            BadPacket = OptiCraftPacket(SMSG_INITIAL)
            BadPacket.WriteByte(7)
            BadPacket.WriteString("Finished loading world: %s" % self.Name)
            BadPacket.WriteString(self.ServerControl.Motd)
            if pPlayer.HasPermission(self.ServerControl.AdmincreteRank):
                BadPacket.WriteByte(0x64)
            else:
                BadPacket.WriteByte(0x00)
            pPlayer.SendPacket(BadPacket)
        Packet2 = OptiCraftPacket(SMSG_LEVELSIZE)
        Packet2.WriteInt16(self.X)
        Packet2.WriteInt16(self.Z)
        Packet2.WriteInt16(self.Y)
        pPlayer.SendPacket(Packet2)

        pPlayer.SetLocation(self.SpawnX, self.SpawnY, self.SpawnZ, self.SpawnOrientation, self.SpawnPitch)
        Packet3 = OptiCraftPacket(SMSG_SPAWNPOINT)
        Packet3.WriteByte(255)
        Packet3.WriteString("")
        if pPlayer.GetSpawnPosition()[0] == -1:
            Packet3.WriteInt16(self.SpawnX)
            Packet3.WriteInt16(self.SpawnZ)
            Packet3.WriteInt16(self.SpawnY)
            Packet3.WriteByte(self.SpawnOrientation)
            Packet3.WriteByte(self.SpawnPitch)
        else:
            Location = pPlayer.GetSpawnPosition()
            pPlayer.SetSpawnPosition(-1, -1, -1, -1, -1)
            Packet3.WriteInt16(Location[0])
            Packet3.WriteInt16(Location[2])
            Packet3.WriteInt16(Location[1])
            Packet3.WriteByte(Location[3])
            Packet3.WriteByte(Location[4])
        pPlayer.SendPacket(Packet3)
        self.SendPlayerJoined(pPlayer)
        self.SendAllPlayers(pPlayer)



    def RemovePlayer(self, pPlayer, ChangingMaps = False):
        if not ChangingMaps:
            self.Players.remove(pPlayer)
        #Send Some packets to local players...
        Packet = OptiCraftPacket(SMSG_PLAYERLEAVE)
        Packet.WriteByte(pPlayer.GetId())
        self.SendPacketToAllButOne(Packet, pPlayer)
        self.PlayerIDs.append(pPlayer.GetId()) #release the ID
        if ChangingMaps:
            self._RemoveAllPlayersFromView(pPlayer)
            self.TransferringPlayers.append(pPlayer)

    def SendBlock(self, pPlayer, x, y, z):
        #We can trust that these coordinates will be within bounds.
        Packet = OptiCraftPacket(SMSG_BLOCKSET)
        Packet.WriteInt16(x)
        Packet.WriteInt16(z)
        Packet.WriteInt16(y)
        Packet.WriteByte(ord(self.Blocks[self._CalculateOffset(x, y, z)]))
        pPlayer.SendPacket(Packet)
    def AddPlayer(self, pPlayer, Transferring = False):
        self.JoiningPlayers.append(pPlayer)
        pPlayer.SetNewId(self.PlayerIDs.pop())

    def SendPlayerJoined(self, pPlayer):
        Packet = OptiCraftPacket(SMSG_SPAWNPOINT)
        Packet.WriteByte(pPlayer.GetId())
        Packet.WriteString(pPlayer.GetColouredName())
        Packet.WriteInt16(pPlayer.GetX())
        Packet.WriteInt16(pPlayer.GetZ())
        Packet.WriteInt16(pPlayer.GetY())
        Packet.WriteByte(pPlayer.GetOrientation())
        Packet.WriteByte(pPlayer.GetPitch())
        for nPlayer in self.Players:
            if nPlayer != pPlayer and pPlayer.CanBeSeenBy(nPlayer):
                nPlayer.SendPacket(Packet)

    def _RemoveAllPlayersFromView(self, pPlayer):
        for nPlayer in self.Players:
            if nPlayer != pPlayer:
                Packet = OptiCraftPacket(SMSG_PLAYERLEAVE)
                Packet.WriteByte(nPlayer.GetId())
                pPlayer.SendPacket(Packet)

    def SendAllPlayers(self, Client):
        for pPlayer in self.Players:
            if pPlayer != Client and pPlayer.CanBeSeenBy(Client):
                Packet = OptiCraftPacket(SMSG_SPAWNPOINT)
                Packet.WriteByte(pPlayer.GetId())
                Packet.WriteString(pPlayer.GetColouredName())
                Packet.WriteInt16(pPlayer.GetX())
                Packet.WriteInt16(pPlayer.GetZ())
                Packet.WriteInt16(pPlayer.GetY())
                Packet.WriteByte(pPlayer.GetOrientation())
                Packet.WriteByte(pPlayer.GetPitch())
                Client.SendPacket(Packet)

    def SendNotice(self, Message):
        Packet = OptiCraftPacket(SMSG_MESSAGE)
        Packet.WriteByte(0)
        Message = self.ServerControl.ConvertColours(("&N" + Message))
        Packet.WriteString(Message)
        self.SendPacketToAll(Packet)
        
    def SendJoinMessage(self, Message):
        Packet = OptiCraftPacket(SMSG_MESSAGE)
        Packet.WriteByte(0)
        Message = self.ServerControl.ConvertColours(Message)
        Packet.WriteString(Message[:64])
        for pPlayer in self.Players:
            if pPlayer.GetJoinNotifications():
                pPlayer.SendPacket(Packet)
    def SendPacketToAll(self, Packet):
        '''Distributes a packet to all clients on a map
            *ANY CHANGES TO THIS FUNCTION NEED TO BE MADE TO Player::SendPacket!'''
        Data = Packet.GetOutData()
        for pPlayer in self.Players:
            pPlayer.OutBuffer.write(Data)
    def SendPacketToAllButOne(self, Packet, Client):
        '''Distributes a packet to all clients on a map
            *ANY CHANGES TO THIS FUNCTION NEED TO BE MADE TO Player::SendPacket!'''
        Data = Packet.GetOutData()
        for pPlayer in self.Players:
            if pPlayer != Client:
                pPlayer.OutBuffer.write(Data)
    @staticmethod
    def GetCacheValues(Name, ServerControl):
        try:
            fHandle = open("Worlds/%s.save" % Name)
            fHandle.seek(18)
            NumElements = struct.unpack("i", fHandle.read(4))[0]
            MinRank = 'guest'
            Hidden = 0
            for i in xrange(NumElements):
                Key = World._ReadLengthString(fHandle)
                Value = World._ReadLengthString(fHandle)
                if Key == "hidden":
                    Hidden = int(Value)
                elif Key == "minrank":
                    MinRank = Value
            fHandle.close()
            assert(MinRank.capitalize() in ServerControl.RankNames)
        except AssertionError:
            MinRank = 'guest'
        finally:
            return MinRank, Hidden

