import hashlib
from opticraftpacket import OptiCraftPacket
from opcodes import *
class Player(object):
    #Constructor is located at the bottom
    def ProcessPackets(self):
        ProcessingPackets = True
        while ProcessingPackets:
            if len(self.SockBuffer) == 0:
                return
            OpCode = ord(self.SockBuffer[0])
            if PacketSizes.has_key(OpCode) == False:
                self.Disconnect("Unhandled packet!") #Unimplemented packet type.
                return
            PacketSize = PacketSizes[OpCode]
            BufLen = len(self.SockBuffer) - 1 #Remove one for opcode
            #print "OpCode:", OpCode
            #print "Buffer:", self.SockBuffer
            #print "Buflen:", BufLen
            #print "Size:", PacketSize
            if BufLen >= PacketSize:
                Packet = OptiCraftPacket(OpCode,self.SockBuffer[1:PacketSize+1]) #up to and including end of packet
                self.SockBuffer = self.SockBuffer[PacketSize+1:] #From end of packet on
                if self.OpcodeHandler.has_key(OpCode):
                    self.OpcodeHandler[OpCode](Packet)
            else:
                ProcessingPackets = False

    def Push_Recv_Data(self,Data):
        '''Called by the Socketmanager. Gives us raw data to be processed'''
        self.SockBuffer += Data
    def GetOutBuffer(self):
        return self.OutBuffer
    def SetOutBuffer(self,NewBuffer):
        self.OutBuffer = NewBuffer
    def SendPacket(self,Packet):
        '''Lets the socketmanager know that we have data to send'''
        self.OutBuffer += Packet.GetOutData()
        self.ServerControl.SockManager.AddWriteablePlayer(self)
    def Disconnect(self,Message):
        #TODO: Implement message properly =\
        self.ServerControl.SockManager.CloseSocket(self.PlayerSocket)
        self.ServerControl.RemovePlayer(self)

    def SendMessage(self,Message):
        Packet = OptiCraftPacket(SMSG_MESSAGE)
        Packet.WriteByte(0)
        Packet.WriteString(Message[:64])
        self.SendPacket(Packet)

    def GetId(self):
        return self.Id
    def SetId(self,Id):
        self.Id = Id
    def GetName(self):
        return self.Name
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
    def GetPermissions(self):
        return self.Permissions
    
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

        if self.Name in self.ServerControl.PlayerNames:
            self.Disconnect("Duplicates are not allowed!")
            return
        if self.ServerControl.IsBanned(self) == True:
            self.Disconnect("You are banned!")
            return
        
        if CorrectPass == HashedPass:
            print self.Name, "connected to the server!"
            self.ServerControl.PlayerNames.add(self.Name)
            self.IsIdentified = True
            #send the next packet...
            OutPacket = OptiCraftPacket(SMSG_INITIAL)
            OutPacket.WriteByte(7)
            OutPacket.WriteString(self.ServerControl.GetName())
            OutPacket.WriteString(self.ServerControl.GetMotd())
            OutPacket.WriteByte(0)
            self.SendPacket(OutPacket)
            if self.Name == "opticalza":
                self.Permissions.add("a")
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
                Result = self.World.AttemptSetBlock(self,x,y,z,Block)
            if Result != True:
                self.World.SendBlock(self,x,y,z)
            
    def HandleChatMessage(self,Packet):
        junk = Packet.GetByte()
        Message = Packet.GetString()
        if Message[0] == "/":
            self.ServerControl.CommandHandle.HandleCommand(self,Message[1:])
            return

        Packet2 = OptiCraftPacket(SMSG_MESSAGE)
        Packet2.WriteByte(self.GetId())
        Message = self.Name + ": " +Message
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

        self.Permissions = set()

        self.X,self.Y,self.Z,self.O,self.P = -1,-1,-1,-1,-1 #X,Y,Z,Orientation and pitch with the fractional position at 5 bits

        self.OutBuffer = '' #TODO: Replace this with a mutable buffer
        print "Creating player!"
        self.SockBuffer = '' #TODO: Replace this with a mutable buffer
        self.OpcodeHandler = {
            CMSG_IDENTIFY: self.HandleIdentify,
            CMSG_BLOCKCHANGE: self.HandleBlockChange,
            CMSG_POSITIONUPDATE: self.HandleMovement,
            CMSG_MESSAGE: self.HandleChatMessage
        }


