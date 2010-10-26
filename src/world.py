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
from zones import Zone
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
        self.TransferringPlayers = list()
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
        self.IdleTimeout = 0 #How long must the world be unoccupied until it unloads itself from memory
        self.IdleStart = 0 #Not idle.
        if os.path.isfile("Worlds/"+ self.Name + '.save'):
            LoadResult = self.Load()
            if LoadResult == False:
                print "Generating new world for map '%s' - Load a backup if you wish to preserve your data!" %self.Name
                self.GenerateGenericWorld()
        else:
            self.GenerateGenericWorld()
        self.NetworkSize = struct.pack("!i", self.X*self.Y*self.Z)

        self.Zones = list()
        self.ServerControl.InsertZones(self) #Servercontrol manages all the zones


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
            #Save to a temp file. Then copy it over. (If we crash during this, the old save is unchanged)
            #...Crashes may occur if we run out of memory, so do not change this!
            fHandle = open("Worlds/%s.temp" %(self.Name),'wb')
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
        shutil.copy("Worlds/%s.temp" %(self.Name),"Worlds/%s.save" %(self.Name))
        os.remove("Worlds/%s.temp" %(self.Name))
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
        FileName = self.Name + '_' + time.strftime("%d-%m-%Y_%H-%M-%S", time.gmtime()) + '.save'
        shutil.copy("Worlds/" + self.Name + '.save', "Backups/" + self.Name + "/" + FileName)
        self.SendNotice("Backed up world in %dms" %(int((time.time()-start) * 1000)))
        self.LastBackup = start

    def InsertZone(self,pZone):
        self.Zones.append(pZone)
    def GetZone(self,Name):
        Name = Name.lower()
        for pZone in self.Zones:
            if pZone.Name.lower() == Name:
                return pZone
        return None
    def GetZones(self):
        return self.Zones
    def DeleteZone(self,pZone):
        self.Zones.remove(pZone)

    def SetIdleTimeout(self,Time):
        self.IdleTimeout = Time

    def _CalculateOffset(self,x,y,z):
        return z*(self.X*self.Y) + y*(self.X) + x

    def _CalculateCoords(self, offset):
        x = offset % self.X
        y = (offset // self.X) % self.Y
        z = offset // (self.X * self.Y)
        return x, y, z

    def WithinBounds(self,x,y,z):
        if x < 0 or x >= self.X or y < 0 or y >= self.Y or z < 0 or z >= self.Z:
            return False
        return True

    def AttemptSetBlock(self,pPlayer,x,y,z,val):
        if not self.WithinBounds(x, y, z):
            return True #Cant set that block. But don't return False or it'll try "undo" the change!
        if val >= BLOCK_END:
            return False #Fake block type...
        #Rank 5 and below are normal users. 6+ is a builder and can place disabled blocks
        if RankToLevel[pPlayer.GetRank()] < 6 and val in DisabledBlocks:
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
        if pPlayer.GetTowerCmd() == True and val == 0:
            BadBlock = self.Blocks[self._CalculateOffset(x, y, z)]
            while True:
                CurBlock = self.Blocks[self._CalculateOffset(x, y, z)]
                if CurBlock == BadBlock:
                    self.Blocks[self._CalculateOffset(x, y, z)] = chr(0)
                    Packet = OptiCraftPacket(SMSG_BLOCKSET)
                    Packet.WriteInt16(x)
                    Packet.WriteInt16(z)
                    Packet.WriteInt16(y)
                    Packet.WriteByte(0)
                    self.SendPacketToAll(Packet)
                    z -= 1
                    if z == 0:
                        pPlayer.SendMessage("&aTower destroyed!")
                        pPlayer.SendMessage("&aRemember to DISABLE this command by typing /destroytower again!")
                        return
                else:
                    pPlayer.SendMessage("&aTower destroyed!")
                    pPlayer.SendMessage("&aRemember to DISABLE this command by typing /destroytower again!")
                    return True
            #Destroy the tower of shit

        #Zone creation
        if pPlayer.IsCreatingZone():
            zData = pPlayer.GetZoneData()
            if zData["Phase"] == 1:
                #Placing the first corner of the zone.
                zData["X1"] = x
                zData["Y1"] = y
                zData["Z1"] = z
                zData["Phase"] = 2
                pPlayer.SendMessage("&aNow place the final corner for the zone.")
                return True
            elif zData["Phase"] == 2:
                FileName = Zone.Create(zData["Name"], zData["X1"], x, zData["Y1"], y, zData["Z1"]-1, z-1, zData["Height"], zData["Owner"], self.Name)
                self.Zones.append(Zone(FileName))
                pPlayer.SendMessage("&aSuccessfully created zone \"%s\"" %zData["Name"])
                #hide the starting block for the zone
                self.SendBlock(pPlayer, zData["X1"], zData["Y1"], zData["Z1"])
                pPlayer.FinishCreatingZone()
                return False

        #ZONES!
        for pZone in self.Zones:
            if pZone.IsInZone(x,y,z):
                if pZone.CanBuild(pPlayer) == False:
                    pPlayer.SendMessage("&4You cannot build in zone \"%s\"" %pZone.Name)
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

    def PruneBlockLog(self,Time):
        ToRemove = []
        now = time.time()
        NumChanged = 0
        for key in self.BlockHistory:
            BlockInfo = self.BlockHistory[key]
            if BlockInfo.Time > now-time:
                ToRemove.append(key)
                NumChanged += 1
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
        if self.IdleTimeout != 0 and len(self.Players) == 0:
            if self.IdleStart != 0:
                if self.IdleStart + self.IdleTimeout < now:
                    self.ServerControl.UnloadWorld(self) #Unload.
                    return
            else:
                self.IdleStart = now
                print "Im idling... %d" %self.IdleTimeout
        elif self.IdleStart != 0:
            self.IdleStart = 0

        if self.LastSave + self.SaveInterval < now:
            self.Save()
        if self.LastBackup + self.BackupInterval < now:
            self.Backup()

        for pPlayer in self.Players:
            if pPlayer.IsLoadingWorld():
                self.SendWorld(pPlayer)
                continue
            pPlayer.ProcessPackets()
        while len(self.TransferringPlayers) > 0:
            self.Players.remove(self.TransferringPlayers.pop())

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

    def RemovePlayer(self,pPlayer,ChangingMaps = False):
        if not ChangingMaps:
            self.Players.remove(pPlayer)
        #Send Some packets to local players...
        if pPlayer.IsLoadingWorld() == False:
            Packet = OptiCraftPacket(SMSG_PLAYERLEAVE)
            Packet.WriteByte(pPlayer.GetId())
            self.SendPacketToAll(Packet, pPlayer)
            self.SendNotice("%s left the map" %pPlayer.GetName())
            if ChangingMaps:
                self._ChangeMap(pPlayer)
                self.TransferringPlayers.append(pPlayer)

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
        Packet.WriteString(pPlayer.GetColouredName())
        Packet.WriteInt16(pPlayer.GetX())
        Packet.WriteInt16(pPlayer.GetZ())
        Packet.WriteInt16(pPlayer.GetY())
        Packet.WriteByte(pPlayer.GetOrientation())
        Packet.WriteByte(pPlayer.GetPitch())
        self.SendPacketToAll(Packet, pPlayer)

    def _ChangeMap(self,pPlayer):
        for nPlayer in self.Players:
            if nPlayer != pPlayer:
                Packet = OptiCraftPacket(SMSG_PLAYERLEAVE)
                Packet.WriteByte(nPlayer.GetId())
                pPlayer.SendPacket(Packet)
    def SendAllPlayers(self,Client):
        for pPlayer in self.Players:
            if pPlayer.IsLoadingWorld() == False and pPlayer != Client:
                Packet = OptiCraftPacket(SMSG_SPAWNPOINT)
                Packet.WriteByte(pPlayer.GetId())
                Packet.WriteString(pPlayer.GetColouredName())
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
    