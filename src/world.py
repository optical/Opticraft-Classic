import zlib
import gzip
import struct
import os
import time
from array import array
from opticraftpacket import OptiCraftPacket
from opcodes import *
from blocktype import *

class World(object):
    def __init__(self,Name,IsNew = False,IsDefault = False):
        self.IsDefault = IsDefault
        self.Blocks = array("c")
        self.Players = set()
        self.x, self.y, self.z = -1,-1,-1
        self.SpawnX,self.SpawnY,self.SpawnZ = -1,-1,-1
        if not IsNew:
            self.Load()
        else:
            self.GenerateGenericWorld()
        self.NetworkSize = struct.pack("!i", self.x*self.y*self.z)

        self.LastSave = time.time()
        self.SaveInterval = 180

    def Load(self):
        pass #TODO: Implement world state saving...
    def Save(self):
        print "I would be saving now!" #TODO: Implement world state saving...
        self.LastSave = time.time()

    def GenerateGenericWorld(self):
        self.x, self.y, self.z = 128,128,64
        GrassLevel = self.z / 2
        SandLevel = GrassLevel - 2
        self.SpawnY = self.y / 2
        self.SpawnX = self.x / 2
        self.SpawnZ = self.z / 2 +2
        for z in xrange(self.z):
            if z < SandLevel:
                Block = chr(BLOCK_ROCK)
            elif z >= SandLevel and z < GrassLevel:
                Block = chr(BLOCK_SAND)
            elif z == GrassLevel:
                Block = chr(BLOCK_GRASS)
            else:
                Block = chr(BLOCK_AIR)
            self.Blocks.extend((self.x*self.y)*Block)
        

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
                Packet2.WriteInt16(self.x)
                Packet2.WriteInt16(self.z)
                Packet2.WriteInt16(self.y)
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
                continue
            pPlayer.ProcessPackets()



    def RemovePlayer(self,pPlayer):
        self.Players.remove(pPlayer)
        #Send Some packets to local players...

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
            print pPlayer
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
        
    def SendPacketToAll(self,Packet,Client = None, SendToSelf = False):
        for pPlayer in self.Players:
            if pPlayer != Client or SendToSelf:
                pPlayer.SendPacket(Packet)
    