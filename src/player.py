import hashlib
from opticraftpacket import OptiCraftPacket
from constants import *
import cStringIO
class Player(object):
    #Constructor is located at the bottom
    def ProcessPackets(self):
        ProcessingPackets = True
        while ProcessingPackets:
            RawBuffer = self.SockBuffer.getvalue()
            if len(RawBuffer) == 0:
                return
            OpCode = ord(RawBuffer[0])
            if PacketSizes.has_key(OpCode) == False:
                self.Disconnect("Unhandled packet!") #Unimplemented packet type.
                return
            PacketSize = PacketSizes[OpCode]
            BufLen = len(RawBuffer) - 1 #Remove one for opcode
            #print "OpCode:", OpCode
            #print "Buffer:", self.SockBuffer
            #print "Buflen:", BufLen
            #print "Size:", PacketSize
            if BufLen >= PacketSize:
                Packet = OptiCraftPacket(OpCode,RawBuffer[1:PacketSize+1]) #up to and including end of packet
                self.SockBuffer.truncate(0)
                self.SockBuffer.write(RawBuffer[PacketSize+1:]) #From end of packet on
                if self.OpcodeHandler.has_key(OpCode):
                    self.OpcodeHandler[OpCode](Packet)
            else:
                ProcessingPackets = False

    def PushRecvData(self,Data):
        '''Called by the Socketmanager. Gives us raw data to be processed'''
        self.SockBuffer.write(Data)
    def GetOutBuffer(self):
        return self.OutBuffer

    def SendPacket(self,Packet):
        '''Lets the socketmanager know that we have data to send'''
        self.OutBuffer.write(Packet.GetOutData())
        if self.IsWriteFlagged == False:
            self.ServerControl.SockManager.AddWriteablePlayer(self)
            self.IsWriteFlagged = True

    def Disconnect(self,Message):
        #TODO: Implement message
        self.ServerControl.SockManager.CloseSocket(self.PlayerSocket)
        self.ServerControl.RemovePlayer(self)

    def SendMessage(self,Message):
        if len(Message) > 64:
            self._SlowSendMessage(Message)
        else:
            Packet = OptiCraftPacket(SMSG_MESSAGE)
            Packet.WriteByte(0)
            Packet.WriteString(Message[:64])
            self.SendPacket(Packet)

    def _SlowSendMessage(self,Message):
        '''Sends a multiline message'''
        Tokens = Message.split()
        if Tokens[0][0] == "&":
            ColourTag = Tokens[0][0] + Tokens[0][1]
        else:
            ColourTag = ''
        OutStr = str()
        for Token in Tokens:
            if len(Token) + len(OutStr) + 1 > 64:
                self.SendMessage(OutStr)
                OutStr = ColourTag + Token
            else:
                OutStr = OutStr + ' ' + Token
        if len(OutStr) > 0:
            self.SendMessage(OutStr)

    def GetId(self):
        return self.Id
    def SetId(self,Id):
        self.Id = Id
    def GetName(self):
        return self.Name
    def GetColouredName(self):
        return '%s%s' %(RankToColour[self.Rank],self.Name)
    def GetSocket(self):
        return self.PlayerSocket
    def GetIP(self):
        return self.PlayerIP

    def GetWorld(self):
        return self.World
    def SetWorld(self,pWorld):
        self.World = pWorld
    def IsLoadingWorld(self):
        return self.IsLoading
    def SetLoadingWorld(self,Val):
        self.IsLoading = Val
    def SetLocation(self,x,y,z,o,p):
        '''Stores client position. X Y Z are floats with the fractal bit at position 5'''
        self.X = x
        self.Y = y
        self.Z = z
        self.O = o
        self.P = p

    def GetX(self):
        return self.X
    def GetY(self):
        return self.Y
    def GetZ(self):
        return self.Z
    def GetOrientation(self):
        return self.O
    def GetPitch(self):
        return self.P
    def GetRank(self):
        return self.Rank
    def SetRank(self,Rank):
        self.Rank = Rank
    def HasPermission(self,Permission):
        return RankToLevel[self.Rank] >= RankToLevel[Permission]
    def SetBlockOverride(self,Block):
        self.BlockOverride = Block
    def GetBlockOverride(self):
        return self.BlockOverride
    
    def GetAboutCmd(self):
        return self.AboutCmd
    def SetAboutCmd(self,Value):
        self.AboutCmd = Value
    def GetTowerCmd(self):
        return self.TowerCmd
    def SetTowerCmd(self,Value):
        self.TowerCmd = Value


    def GetWriteFlagged(self):
        return self.IsWriteFlagged
    def SetWriteFlagged(self,Value):
        self.IsWriteFlagged = Value

    def Teleport(self,x,y,z,o,p):
        '''Teleports the player to X Y Z. These coordinates have the fractal bit at position 5'''
        self.SetLocation(x, y, z, o, p)
        Packet = OptiCraftPacket(SMSG_SPAWNPOINT)
        Packet.WriteByte(255)
        Packet.WriteString("")
        Packet.WriteInt16(x)
        Packet.WriteInt16(z)
        Packet.WriteInt16(y)
        Packet.WriteByte(o)
        Packet.WriteByte(p)
        self.SendPacket(Packet)

    def IsCreatingZone(self):
        return self.CreatingZone
    def GetZoneData(self):
        return self.ZoneData

    def StartZone(self,Name,Owner,Height):
        self.ZoneData["Name"] = Name
        self.ZoneData["Owner"] = Owner
        self.ZoneData["Height"] = Height
        self.ZoneData["Phase"] = 1
        self.CreatingZone = True
    def FinishCreatingZone(self):
        self.zData = dict()
        self.CreatingZone = False
    
    #Opcode handlers go below this line
    def HandleIdentify(self,Packet):
        '''Handles the initial packet sent by the client'''
        if self.IsIdentified == True:
            self.Disconnect()
            return

        Version = Packet.GetByte()
        self.Name = Packet.GetString()
        HashedPass = Packet.GetString().strip("0")
        Unk = Packet.GetByte()
        CorrectPass = hashlib.md5("SOMESALT" + self.Name).hexdigest().strip("0")
        if Version != 7:
            self.Disconnect("Your client is incompatible with this server")
            return

        if self.Name.lower() in self.ServerControl.PlayerNames:
            self.Disconnect("Duplicates are not allowed!")
            return
        if self.ServerControl.IsBanned(self) == True:
            self.Disconnect("You are banned!")
            return
        
        if CorrectPass == HashedPass:
            print self.Name, "connected to the server!"
            self.ServerControl.PlayerNames[self.Name.lower()] = self
            self.IsIdentified = True
            #send the next packet...
            OutPacket = OptiCraftPacket(SMSG_INITIAL)
            OutPacket.WriteByte(7)
            OutPacket.WriteString(self.ServerControl.GetName())
            OutPacket.WriteString(self.ServerControl.GetMotd())
            OutPacket.WriteByte(0)
            self.SendPacket(OutPacket)
            self.Rank = self.ServerControl.GetRank(self.Name)
            self.ServerControl.SendNotice('%s connected to the server' %self.Name)
            return
        else:
            print "Spoofed password!"
            self.Disconnect("Could not authenticate your username.")
            return
    def HandleMovement(self,Packet):
        #This is sent even when the player isn't moving!
        if self.World is not None:
            junk = Packet.GetByte()
            x = Packet.GetInt16()
            z = Packet.GetInt16()
            y = Packet.GetInt16()
            o = Packet.GetByte()
            p = Packet.GetByte()
            if x == self.X and y == self.Y and z == self.Z and o == self.O and p == self.P:
                return #Saves bandwidth. No need to redistribute something we just sent..
            self.SetLocation(x, y, z, o, p)
            NewPacket = OptiCraftPacket(SMSG_PLAYERPOS)
            NewPacket.WriteByte(self.GetId())
            NewPacket.WriteInt16(self.X)
            NewPacket.WriteInt16(self.Z)
            NewPacket.WriteInt16(self.Y)
            NewPacket.WriteByte(self.O)
            NewPacket.WriteByte(self.P)
            self.World.SendPacketToAll(NewPacket, self)




    def HandleBlockChange(self,Packet):
        if self.World is not None:
            x = Packet.GetInt16()
            z = Packet.GetInt16()
            y = Packet.GetInt16()
            Mode = Packet.GetByte()
            Block = Packet.GetByte()
            Result = None
            if Mode == 0:
                Result = self.World.AttemptSetBlock(self,x,y,z,0)
            else:
                if self.BlockOverride != -1:
                    Block = self.BlockOverride
                Result = self.World.AttemptSetBlock(self,x,y,z,Block)
            if Result != True or self.GetBlockOverride() != -1:
                if self.World.WithinBounds(x, y, z):
                    self.World.SendBlock(self,x,y,z)
            
    def HandleChatMessage(self,Packet):
        junk = Packet.GetByte()
        Message = Packet.GetString()
        if Message[0] == "/":
            self.ServerControl.CommandHandle.HandleCommand(self,Message[1:])
            return

        Packet2 = OptiCraftPacket(SMSG_MESSAGE)
        Packet2.WriteByte(self.GetId())
        Message = '%s:&f %s' %(self.GetColouredName(),Message)
        Message = Message[:64]
        Packet2.WriteString(Message)
        self.ServerControl.SendPacketToAll(Packet2)
        
    def __init__(self,PlayerSocket,SockAddress,ServerControl):
        self.PlayerSocket = PlayerSocket
        self.PlayerIP = SockAddress
        self.Name = ''
        self.IsIdentified = False
        self.Id = -1
        self.ServerControl = ServerControl
        self.World = None #Pointer to our current world.
        self.IsLoading = False
        self.AboutCmd = False
        self.TowerCmd = False
        self.IsWriteFlagged = False
        self.Rank = ''
        self.CreatingZone = False
        self.ZoneData = dict()
        #This is used for commands such as /lava, /water, and /grass
        self.BlockOverride = -1

        self.X,self.Y,self.Z,self.O,self.P = -1,-1,-1,-1,-1 #X,Y,Z,Orientation and pitch with the fractional position at 5 bits

        self.OutBuffer = cStringIO.StringIO()
        print "Creating player!"
        self.SockBuffer = cStringIO.StringIO()
        self.OpcodeHandler = {
            CMSG_IDENTIFY: self.HandleIdentify,
            CMSG_BLOCKCHANGE: self.HandleBlockChange,
            CMSG_POSITIONUPDATE: self.HandleMovement,
            CMSG_MESSAGE: self.HandleChatMessage
        }


