import os.path
import zlib
import gzip
import struct
import time
from array import array
from opticraftpacket import OptiCraftPacket
from opcodes import *
from blocktype import *

class World(object):
    def __init__(self,Name,IsDefault = False):
        self.IsDefault = IsDefault
        self.Blocks = array("c")
        self.Players = set()
        self.Name = Name
        self.X, self.Y, self.Z = -1,-1,-1
        self.SpawnX,self.SpawnY,self.SpawnZ = -1,-1,-1
        if os.path.isfile(self.Name + '.save'):
            self.Load()
        else:
            self.GenerateGenericWorld()
        self.NetworkSize = struct.pack("!i", self.X*self.Y*self.Z)

        self.LastSave = time.time()
        self.SaveInterval = 180

    def Load(self):
        '''First draft of map format:
        0-2 = X
        2-4 = Y
        4-6 = Z
        6-8 = SpawnX
        8-10 = SpawnY
        12-12 = SpawnZ
        12+ = zlibbed array data'''
        start = time.time()
        try:
            fHandle = open(self.Name + '.save','rb')
        except:
            print "Failed to open up save file for world %s!" %self.Name
            return False
        
        raw_data = fHandle.read()
        self.X = struct.unpack("h",raw_data[0:2])[0]
        self.Y = struct.unpack("h",raw_data[2:4])[0]
        self.Z = struct.unpack("h",raw_data[4:6])[0]
        self.SpawnX = struct.unpack("h",raw_data[6:8])[0]
        self.SpawnY = struct.unpack("h",raw_data[8:10])[0]
        self.SpawnZ = struct.unpack("h",raw_data[10:12])[0]
        self.Blocks.extend(zlib.decompress(raw_data[12:]))
        fHandle.close()
        print "Loaded world %s in %dms" %(self.Name,int((time.time()-start)*1000))       
    
    def Save(self, Verbose = True):
        '''First draft of map format:
        0-2 = X
        2-4 = Y
        4-6 = Z
        6-8 = SpawnX
        8-10 = SpawnY
        12-12 = SpawnZ
        12+ = zlibbed array data'''
        start = time.time()
        try:
            fHandle = open(self.Name + '.save','wb')
        except:
            print "Critical error, could not save world data for world %s" %self.Name
            return
        fHandle.write(struct.pack("h",self.X))
        fHandle.write(struct.pack("h",self.Y))
        fHandle.write(struct.pack("h",self.Z))
        fHandle.write(struct.pack("h",self.SpawnX))
        fHandle.write(struct.pack("h",self.SpawnY))
        fHandle.write(struct.pack("h",self.SpawnZ))
        fHandle.write(zlib.compress(self.Blocks,1))
        #We use the lowest level of compression as saving time is much more important here
        fHandle.close()
        if Verbose:
            print "Saved world %s in %dms" %(self.Name,int((time.time()-start)*1000))
            self.SendNotice("Saved world %s in %dms" %(self.Name,int((time.time()-start)*1000)))
        self.LastSave = time.time()

    def _CalculateOffset(self,x,y,z):
        return z*(self.X*self.Y) + y*(self.X) + x
    
    def AttemptSetBlock(self,x,y,z,val):
        #TODO: Check the block type & coordinates are correct
        if x < 0 or x >= self.X or y < 0 or y >= self.Y or z < 0 or z >= self.Z:
            return True #Cant set that block. But don't return False or it'll try "undo" the change!
        self.SetBlock(x,y,z,val)
        return True
    def SetBlock(self,x,y,z,val):
        #Changes a block to a certain value.
        ArrayValue = self._CalculateOffset(x,y,z)
        self.Blocks[ArrayValue] = chr(val)
        Packet = OptiCraftPacket(SMSG_BLOCKSET)
        Packet.WriteInt16(x)
        Packet.WriteInt16(z)
        Packet.WriteInt16(y)
        Packet.WriteByte(val)
        self.SendPacketToAll(Packet)


    def GenerateGenericWorld(self):
        self.X, self.Y, self.Z = 128,128,64
        GrassLevel = self.Z / 2
        SandLevel = GrassLevel - 2
        self.SpawnY = self.Y / 2
        self.SpawnX = self.X / 2
        self.SpawnZ = self.Z / 2 +2
        for z in xrange(self.Z):
            if z < SandLevel:
                Block = chr(BLOCK_ROCK)
            elif z >= SandLevel and z < GrassLevel:
                Block = chr(BLOCK_SAND)
            elif z == GrassLevel:
                Block = chr(BLOCK_GRASS)
            else:
                Block = chr(BLOCK_AIR)
            self.Blocks.extend((self.X*self.Y)*Block)
        self.Save(False)
        

    def run(self):
        if self.LastSave + self.SaveInterval < time.time():
            self.Save()

        for pPlayer in self.Players:
            if pPlayer.IsLoadingWorld():
                #TODO: Pack this in memory!
                fHandle = gzip.GzipFile("temp","wb")
                fHandle.write(self.NetworkSize)
                fHandle.write(self.Blocks)
                fHandle.close()
                del fHandle
                rHandle = open("temp","rb")
                data = rHandle.read()
                rHandle.close()
                os.remove("temp")
                CurPos = 0
                EndPos = len(data)
                while CurPos < EndPos:
                    ChunkEnd = CurPos+1024
                    if ChunkEnd > EndPos:
                        ChunkEnd = EndPos
                    ChunkSize = ChunkEnd - CurPos
                    Packet = OptiCraftPacket(SMSG_CHUNK)
                    Packet.WriteInt16(ChunkSize)
                    Packet.WriteKBChunk(data[CurPos:ChunkEnd])
                    Packet.WriteByte(100.0 * (float(ChunkEnd)/float(EndPos)))
                    pPlayer.SendPacket(Packet)
                    CurPos = ChunkEnd

                Packet2 = OptiCraftPacket(SMSG_LEVELSIZE)
                Packet2.WriteInt16(self.X)
                Packet2.WriteInt16(self.Z)
                Packet2.WriteInt16(self.Y)
                pPlayer.SendPacket(Packet2)

                x = self.SpawnX * 32
                y = self.SpawnY * 32
                z = self.SpawnZ * 32 + 51 #51 = height of player!
                pPlayer.SetLocation(x, y, z, 0, 0)

                Packet3 = OptiCraftPacket(SMSG_SPAWNPOINT)
                Packet3.WriteByte(255)
                Packet3.WriteString("")
                Packet3.WriteInt16(x)
                Packet3.WriteInt16(z)
                Packet3.WriteInt16(y)
                Packet3.WriteByte(0)
                Packet3.WriteByte(0)
                pPlayer.SendPacket(Packet3)
                pPlayer.SetLoadingWorld(False)
                self.SendPlayerJoined(pPlayer)
                self.SendAllPlayers(pPlayer)
                self.SendNotice('%s joined the map!' %pPlayer.GetName())
                continue
            pPlayer.ProcessPackets()



    def RemovePlayer(self,pPlayer):
        self.Players.remove(pPlayer)
        #Send Some packets to local players...

    def SendBlock(self,pPlayer,x,y,z):
        #We can trust that these coordinates will be within bounds.
        Packet = OptiCraftPacket(SMSG_BLOCKSET)
        Packet.WriteInt16(x)
        Packet.WriteInt16(z)
        Packet.WriteInt16(y)
        Packet.WriteByte(self.Blocks[self._CalculateOffset(x, y, z)])
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
    