###########################################
#        Packet Writers / Creators        #
###########################################

import struct
from core.constants import *

class PacketWriter(object):
    IdentifcationStruct = struct.Struct("BB64s64sB")
    ChunkStruct = struct.Struct("!Bh1024sB")
    LevelSizeStruct = struct.Struct("!Bhhh")
    BlockSetStruct = struct.Struct("!BhhhB")
    SpawnPointStruct = struct.Struct("!BB64shhhBB")
    FullMoveStruct = struct.Struct("!BBhhhBB")
    MovementUpdateStruct = struct.Struct("BBbbb")
    RotateUpdateStruct = struct.Struct("BBBB")
    DespawnStruct = struct.Struct("BB")
    MessageStruct = struct.Struct("BB64s")
    DisconnectStruct = struct.Struct("B64s")
    UpdateUserStruct = struct.Struct("BB")
    
    @staticmethod
    def MakeIdentifcationPacket(ServerName, Motd, OpFlags):
        return PacketWriter.IdentifcationStruct.pack(SMSG_INITIAL, 7, ServerName, Motd, OpFlags)
    
    @staticmethod
    def MakeChunkPacket(Length, Chunk, Percent):
        return PacketWriter.ChunkStruct.pack(SMSG_CHUNK, Length, Chunk, Percent)
    
    @staticmethod 
    def MakeLevelSizePacket(x, z, y):
        return PacketWriter.LevelSizeStruct.pack(SMSG_LEVELSIZE, x, z, y)
    
    @staticmethod
    def MakeBlockSetPacket(x, z, y, BlockValue):
        return PacketWriter.BlockSetStruct.pack(SMSG_BLOCKSET, x, z, y, BlockValue)

    @staticmethod
    def MakeSpawnPointPacket(PlayerId, PlayerName, x, z, y, Orientation, Heading):
        return PacketWriter.SpawnPointStruct.pack(SMSG_SPAWNPOINT, PlayerId, PlayerName, x, z, y, Orientation, Heading)
    
    @staticmethod 
    def MakeFullMovePacket(PlayerID, x, z, y, o, p):
        return PacketWriter.FullMoveStruct.pack(SMSG_PLAYERPOS, PlayerID, x, z, y, o, p)
    
    @staticmethod 
    def MakeMoveUpdatePacket(PlayerID, dx, dz, dy):
        return PacketWriter.MovementUpdateStruct.pack(SMSG_POSITION_UDPDATE, PlayerID, dx, dz, dy)
    
    @staticmethod 
    def MakeRotateUpdatePacket(PlayerId, o, p):
        return PacketWriter.RotateUpdateStruct.pack(SMSG_ORIENTATION_UPDATE, PlayerId, o, p)
    
    @staticmethod 
    def MakeDespawnPacket(PlayerID):
        return PacketWriter.DespawnStruct.pack(SMSG_PLAYERLEAVE, PlayerID)

    @staticmethod 
    def MakeMessagePacket(NoticeFlags, Message):
        return PacketWriter.MessageStruct.pack(SMSG_MESSAGE, NoticeFlags, Message)

    @staticmethod     
    def MakeDisconnectPacket(Message):
        return PacketWriter.DisconnectStruct.pack(SMSG_DISCONNECT, Message)

    @staticmethod 
    def MakeUpdateUserPacket(Flags):
        return PacketWriter.UpdateUserStruct.pack(SMSG_USERTYPE, Flags)
    

class PacketReader(object):    
    IdentifyStruct = struct.Struct("B64s64sB")
    BlockSetStruct = struct.Struct("!hhhBB")
    MovementStruct = struct.Struct("!BhhhBB")
    MessageStruct = struct.Struct("B64s")
    
    @staticmethod 
    def ParseIdentificationPacket(Packet):
        return PacketReader.IdentifyStruct.unpack(Packet)
    
    @staticmethod 
    def ParseBlockSetPacket(Packet):
        return PacketReader.BlockSetStruct.unpack(Packet)
    
    @staticmethod 
    def ParseMovementPacket(Packet):
        return PacketReader.MovementStruct.unpack(Packet)
    
    @staticmethod 
    def ParseMessagePacket(Packet):
        return PacketReader.MessageStruct.unpack(Packet)

