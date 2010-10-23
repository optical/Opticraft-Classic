import os.path
import os
import cStringIO
import zlib
import gzip
import struct
import time
import random
import shutil
from array import array
from opticraftpacket import OptiCraftPacket
from constants import *

class BlockLog(object):
    '''Stores the history of a block'''
    def __init__(self,Username,Time,Value):
        self.Username = Username
        self.Time = Time
        self.Value = Value

class World(object):
    def __init__(self,ServerControl,Name):
        self.Blocks = array("c")
        self.Players = set()
        self.Name = Name
        self.X, self.Y, self.Z = -1,-1,-1
        self.SpawnX,self.SpawnY,self.SpawnZ = -1,-1,-1
        self.SpawnOrientation, self.SpawnPitch = 0, 0
        self.ServerControl = ServerControl
        self.BlockHistory = dict()
        #Config values
        self.DefaultX = self.ServerControl.ConfigValues.GetValue("worlds","DefaultSizeX","256")
        self.DefaultY = self.ServerControl.ConfigValues.GetValue("worlds","DefaultSizeY","256")
        self.DefaultZ = self.ServerControl.ConfigValues.GetValue("worlds","DefaultSizeZ","96")
        self.LastSave = time.time() + random.randrange(0,30)
        self.SaveInterval = int(self.ServerControl.ConfigValues.GetValue("worlds","SaveTime","300"))
        self.LastBackup = time.time() + random.randrange(0,30)
        self.BackupInterval = int(self.ServerControl.ConfigValues.GetValue("worlds","BackupTime","3600"))
        self.CompressionLevel = int(self.ServerControl.ConfigValues.GetValue("worlds","CompressionLevel",1))
        self.LogBlocks = int(self.ServerControl.ConfigValues.GetValue("worlds","EnableBlockHistory",1))
        if os.path.isfile("Worlds/"+ self.Name + '.save'):
            LoadResult = self.Load()
            if LoadResult == False:
                print "Generating new world for map '%s' - Load a backup if you wish to preserve your data!" %self.Name
                self.GenerateGenericWorld()
        else:
            self.GenerateGenericWorld()
        self.NetworkSize = struct.pack("!i", self.X*self.Y*self.Z)


    def Load(self):
        '''First draft of map format:
        0-2 = X
        2-4 = Y
        4-6 = Z
        6-8 = SpawnX
        8-10 = SpawnY
        10-12 = SpawnZ
        12-14 = SpawnOrientation
        14-16 = SpawnPitch
        16+ = zlibbed array data'''
        start = time.time()
        try:
            fHandle = open("Worlds/" +self.Name + '.save','rb')
        except:
            print "Failed to open up save file for world %s!" %self.Name
            return False
        try:
            raw_data = fHandle.read()
            self.X = struct.unpack("h",raw_data[0:2])[0]
            self.Y = struct.unpack("h",raw_data[2:4])[0]
            self.Z = struct.unpack("h",raw_data[4:6])[0]
            self.SpawnX = struct.unpack("h",raw_data[6:8])[0]
            self.SpawnY = struct.unpack("h",raw_data[8:10])[0]
            self.SpawnZ = struct.unpack("h",raw_data[10:12])[0]
            self.SpawnOrientation = struct.unpack("h",raw_data[12:14])[0]
            self.SpawnPitch = struct.unpack("h",raw_data[14:16])[0]
            self.Blocks.fromstring(zlib.decompress(raw_data[16:]))
            fHandle.close()
            print "Loaded world %s in %dms" %(self.Name,int((time.time()-start)*1000))
            if len(self.Blocks) != self.X*self.Y*self.Z:
                raise Exception()
        except:
            print "CRITICAL ERROR - Failed to load map '%s'." %self.Name + 'save'
            return False
    
    def Save(self, Verbose = True):
        '''First draft of map format:
        0-2 = X
        2-4 = Y
        4-6 = Z
        6-8 = SpawnX
        8-10 = SpawnY
        12-12 = SpawnZ
        12-14 = SpawnOrientation
        14-16 = SpawnPitch
        16+ = zlibbed array data'''
        start = time.time()
        try:
            fHandle = open("Worlds/" +self.Name + '.save','wb')
        except:
            print "Critical error, could not save world data for world %s" %self.Name
            return
        fHandle.write(struct.pack("h",self.X))
        fHandle.write(struct.pack("h",self.Y))
        fHandle.write(struct.pack("h",self.Z))
        fHandle.write(struct.pack("h",self.SpawnX))
        fHandle.write(struct.pack("h",self.SpawnY))
        fHandle.write(struct.pack("h",self.SpawnZ))
        fHandle.write(struct.pack("h",self.SpawnOrientation))
        fHandle.write(struct.pack("h",self.SpawnPitch))
        fHandle.write(zlib.compress(self.Blocks,self.CompressionLevel))
        fHandle.close()
        if Verbose:
            print "Saved world %s in %dms" %(self.Name,int((time.time()-start)*1000))
            self.SendNotice("Saved world %s in %dms" %(self.Name,int((time.time()-start)*1000)))
        self.LastSave = start

    def Backup(self):
        '''Performs a backup of the current save file'''
        start = time.time()
        if os.path.isfile("Worlds/" + self.Name + ".save") == False:
            return
        if os.path.exists("Backups/" + self.Name) == False:
            os.mkdir("Backups/" + self.Name)
        FileName = self.Name + '_' + time.strftime("%d-%m-%Y_%M-%S", time.gmtime()) + '.save'
        shutil.copy("Worlds/" + self.Name + '.save', "Backups/" + self.Name + "/" + FileName)
        self.SendNotice("Backed up world in %dms" %(int((time.time()-start) * 1000)))
        self.LastBackup = start

    def _CalculateOffset(self,x,y,z):
        return z*(self.X*self.Y) + y*(self.X) + x

    def _CalculateCoords(self, offset):
        x = offset % self.X
        y = (offset // self.X) % self.Y
        z = offset // (self.X * self.Y)
        return x, y, z

    def AttemptSetBlock(self,pPlayer,x,y,z,val):
        if x < 0 or x >= self.X or y < 0 or y >= self.Y or z < 0 or z >= self.Z:
            return True #Cant set that block. But don't return False or it'll try "undo" the change!
        if val >= BLOCK_END:
            return False #Fake block type...
        if val in DisabledBlocks:
            pPlayer.SendMessage("&4That block is disabled!")
            return False
        
        if pPlayer.GetAboutCmd() == True:
            #Display block information
            BlockInfo = self.BlockHistory.get(self._CalculateOffset(x, y, z),None)
            if BlockInfo == None:
                pPlayer.SendMessage("No information available for this block (No changes made)")
            else:
                now = int(time.time())
                pPlayer.SendMessage("This block was last changed by %s" %BlockInfo.Username)
                pPlayer.SendMessage("The old value for the block was %d" %ord(BlockInfo.Value))
                pPlayer.SendMessage("Changed %s ago" %time.strftime("%H hour(s) %M minutes(s) and %S second(s)", time.gmtime(now-BlockInfo.Time)))
            pPlayer.SetAboutCmd(False)
            return False

        ArrayValue = self._CalculateOffset(x,y,z)
        if self.LogBlocks == True:
            self.BlockHistory[ArrayValue] = BlockLog(pPlayer.GetName().lower(),int(time.time()),self.Blocks[ArrayValue])
        self.SetBlock(pPlayer,x,y,z,val)
        return True

    def SetBlock(self,pPlayer,x,y,z,val):
        #Changes a block to a certain value.
        ArrayValue = self._CalculateOffset(x,y,z)
        self.Blocks[ArrayValue] = chr(val)
        Packet = OptiCraftPacket(SMSG_BLOCKSET)
        Packet.WriteInt16(x)
        Packet.WriteInt16(z)
        Packet.WriteInt16(y)
        Packet.WriteByte(val)
        self.SendPacketToAll(Packet,pPlayer)
        
    def UndoActions(self,Username,Time):
        Username = Username.lower()
        ToRemove = []
        NumChanged = 0
        now = time.time()
        
        for key in self.BlockHistory:
            BlockInfo = self.BlockHistory[key]
            if BlockInfo.Username == Username and BlockInfo.Time > now-Time:
                x,y,z = self._CalculateCoords(key)
                self.SetBlock(None, x,y,z, ord(BlockInfo.Value))
                NumChanged += 1
                ToRemove.append(key)
        
        while len(ToRemove) > 0:
            del self.BlockHistory[ToRemove.pop()]
        return NumChanged

    def SetSpawn(self,x,y,z,o,p):
        '''Sets the worlds default spawn position. Stored in the format the client uses'''
        self.SpawnX = x
        self.SpawnY = y
        self.SpawnZ = z
        self.SpawnOrientation = o
        self.SpawnPitch = p



    def GenerateGenericWorld(self,x=512,y=512,z=96):
        self.X, self.Y, self.Z = x,y,z
        GrassLevel = self.Z / 2
        SandLevel = GrassLevel - 2
        self.SpawnY = self.Y / 2 * 32
        self.SpawnX = self.X / 2 * 32
        self.SpawnZ = (self.Z / 2 + 2) * 32 + 51
        self.SpawnOrientation = 0
        self.SpawnPitch = 0
        for z in xrange(self.Z):
            if z < SandLevel:
                Block = chr(BLOCK_ROCK)
            elif z >= SandLevel and z < GrassLevel:
                Block = chr(BLOCK_SAND)
            elif z == GrassLevel:
                Block = chr(BLOCK_GRASS)
            else:
                Block = chr(BLOCK_AIR)
            self.Blocks.fromstring((self.X*self.Y)*Block)
        self.Save(False)
        

    def run(self):
        now = time.time()
        if self.LastSave + self.SaveInterval < now:
            self.Save()
        if self.LastBackup + self.BackupInterval < now:
            self.Backup()

        for pPlayer in self.Players:
            if pPlayer.IsLoadingWorld():
                self.SendWorld(pPlayer)
                continue
            pPlayer.ProcessPackets()

    def SendWorld(self,pPlayer):
        StringHandle = cStringIO.StringIO()
        fHandle = gzip.GzipFile(filename="temp",fileobj=StringHandle,mode="wb",compresslevel=self.CompressionLevel)
        fHandle.write(self.NetworkSize)
        fHandle.write(self.Blocks)
        fHandle.close()
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
            Packet.WriteByte(100.0 * (float(CurBytes)/float(TotalBytes)))
            pPlayer.SendPacket(Packet)
            Chunk = StringHandle.read(1024)

        Packet2 = OptiCraftPacket(SMSG_LEVELSIZE)
        Packet2.WriteInt16(self.X)
        Packet2.WriteInt16(self.Z)
        Packet2.WriteInt16(self.Y)
        pPlayer.SendPacket(Packet2)

        pPlayer.SetLocation(self.SpawnX, self.SpawnY, self.SpawnZ, self.SpawnOrientation, self.SpawnPitch)
        Packet3 = OptiCraftPacket(SMSG_SPAWNPOINT)
        Packet3.WriteByte(255)
        Packet3.WriteString("")
        Packet3.WriteInt16(self.SpawnX)
        Packet3.WriteInt16(self.SpawnZ)
        Packet3.WriteInt16(self.SpawnY)
        Packet3.WriteByte(self.SpawnOrientation)
        Packet3.WriteByte(self.SpawnPitch)
        pPlayer.SendPacket(Packet3)
        pPlayer.SetLoadingWorld(False)
        self.SendPlayerJoined(pPlayer)
        self.SendAllPlayers(pPlayer)
        self.SendNotice('%s joined the map' %pPlayer.GetName())

    def RemovePlayer(self,pPlayer):
        self.Players.remove(pPlayer)
        #Send Some packets to local players...
        if pPlayer.IsLoadingWorld() == False:
            Packet = OptiCraftPacket(SMSG_PLAYERLEAVE)
            Packet.WriteByte(pPlayer.GetId())
            self.SendPacketToAll(Packet, pPlayer)
            self.SendNotice("%s left the map" %pPlayer.GetName())
    def SendBlock(self,pPlayer,x,y,z):
        #We can trust that these coordinates will be within bounds.
        Packet = OptiCraftPacket(SMSG_BLOCKSET)
        Packet.WriteInt16(x)
        Packet.WriteInt16(z)
        Packet.WriteInt16(y)
        Packet.WriteByte(ord(self.Blocks[self._CalculateOffset(x, y, z)]))
        pPlayer.SendPacket(Packet)
    def AddPlayer(self,pPlayer):
        self.Players.add(pPlayer)
        Packet = OptiCraftPacket(SMSG_PRECHUNK)
        pPlayer.SendPacket(Packet)
        pPlayer.SetLoadingWorld(True)
        pPlayer.SetWorld(self)

    def SendPlayerJoined(self,pPlayer):
        Packet = OptiCraftPacket(SMSG_SPAWNPOINT)
        Packet.WriteByte(pPlayer.GetId())
        Packet.WriteString(pPlayer.GetName())
        Packet.WriteInt16(pPlayer.GetX())
        Packet.WriteInt16(pPlayer.GetZ())
        Packet.WriteInt16(pPlayer.GetY())
        Packet.WriteByte(pPlayer.GetOrientation())
        Packet.WriteByte(pPlayer.GetPitch())
        self.SendPacketToAll(Packet, pPlayer)

    def SendAllPlayers(self,Client):
        for pPlayer in self.Players:
            if pPlayer.IsLoadingWorld() == False and pPlayer != Client:
                Packet = OptiCraftPacket(SMSG_SPAWNPOINT)
                Packet.WriteByte(pPlayer.GetId())
                Packet.WriteString(pPlayer.GetName())
                Packet.WriteInt16(pPlayer.GetX())
                Packet.WriteInt16(pPlayer.GetZ())
                Packet.WriteInt16(pPlayer.GetY())
                Packet.WriteByte(pPlayer.GetOrientation())
                Packet.WriteByte(pPlayer.GetPitch())
                Client.SendPacket(Packet)
    def SendNotice(self,Message):
        Packet = OptiCraftPacket(SMSG_MESSAGE)
        Packet.WriteByte(0xFF)
        Packet.WriteString(Message)
        self.SendPacketToAll(Packet)
        
    def SendPacketToAll(self,Packet,Client = None, SendToSelf = False):
        for pPlayer in self.Players:
            if pPlayer != Client or SendToSelf:
                pPlayer.SendPacket(Packet)
    