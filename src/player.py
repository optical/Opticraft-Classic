# Copyright (c) 2010, Jared Klopper
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

import hashlib
import cStringIO
import time
import math
from opticraftpacket import OptiCraftPacket
from constants import *
from console import *
class Player(object):
    #Constructor is located at the bottom
    def ProcessPackets(self):
        ProcessingPackets = True
        while ProcessingPackets:
            RawBuffer = self.SockBuffer.getvalue()
            if len(RawBuffer) == 0:
                break
            OpCode = ord(RawBuffer[0])
            if PacketSizes.has_key(OpCode) == False:
                self.Disconnect("Unhandled packet!") #Unimplemented packet type.
                return
            PacketSize = PacketSizes[OpCode]
            BufLen = len(RawBuffer) - 1 #Remove one for opcode
            if BufLen >= PacketSize:
                Packet = OptiCraftPacket(OpCode,RawBuffer[1:PacketSize+1]) #up to and including end of packet
                self.SockBuffer.truncate(0)
                self.SockBuffer.write(RawBuffer[PacketSize+1:]) #From end of packet on
                if self.OpcodeHandler.has_key(OpCode):
                    self.OpcodeHandler[OpCode](Packet)
            else:
                ProcessingPackets = False
        #Check to see if we have got too much data in our out buffer.
        #Send Queue exceeded (Default = 4MB of buffered data)
        if self.OutBuffer.tell() > self.ServerControl.SendBufferLimit and self.Disconnecting == False:
            Console.Debug("Player", "Disconnecting player as their send queue buffer contains %d bytes" %self.OutBuffer.tell())
            self.Disconnect()
    def PushRecvData(self,Data):
        '''Called by the Socketmanager. Gives us raw data to be processed'''
        self.SockBuffer.write(Data)

    def GetOutBuffer(self):
        return self.OutBuffer
    def SendPacket(self,Packet):
        '''Appends data to the end of our buffer
            *ANY CHANGES TO THIS FUNCTION NEED TO BE MADE TO SendPacketToAll functions!'''
        self.OutBuffer.write(Packet.data.getvalue())

    def IsDisconnecting(self):
        return self.Disconnecting
    def Disconnect(self,Message =''):
        if self.Disconnecting == True:
            return
        self.Disconnecting = True
        Console.Debug("Player","Disconnecting player %s for \"%s\"" %(self.Name,Message))
        if Message != '':
            Packet = OptiCraftPacket(SMSG_DISCONNECT)
            Packet.WriteString(Message[:64])
            self.SendPacket(Packet)
        self.ServerControl.SockManager.CloseSocket(self.PlayerSocket)
        self.ServerControl.RemovePlayer(self)

    def SendMessage(self,Message,ColourNewLines=True):
        if len(Message) > 63:
            self._SlowSendMessage(Message,ColourNewLines)
        else:
            Packet = OptiCraftPacket(SMSG_MESSAGE)
            Packet.WriteByte(0)
            Packet.WriteString(Message[:64])
            self.SendPacket(Packet)

    def _SlowSendMessage(self,Message,ColourNewLines=True):
        '''Sends a multiline message'''
        Tokens = Message.split()
        if Tokens[0][0] == "&" and ColourNewLines:
            ColourTag = Tokens[0][0] + Tokens[0][1]
        else:
            ColourTag = ''
        OutStr = str()
        for Token in Tokens:
            if len(Token) >= 63:
                continue #too long
            elif len(Token) + len(OutStr) + 1 > 63:
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
        return self.ColouredName
    def GetSocket(self):
        return self.PlayerSocket
    def GetIP(self):
        return self.PlayerIP[0]

    def GetWorld(self):
        return self.World
    def SetWorld(self,pWorld):
        self.World = pWorld
    def ChangeWorld(self,Name):
        #is this an active world? If so - leave and join
        #else - Boot up new world and then leave/join
        #Leave our world first.
        Name = Name.lower()
        ActiveWorlds, IdleWorlds = self.ServerControl.GetWorlds()
        NewWorld = None
        for pWorld in ActiveWorlds:
            if pWorld.Name.lower() == Name:
                NewWorld = pWorld
        if NewWorld == None:
            #Its idle...
            for WorldName in IdleWorlds:
                if Name == WorldName.lower():
                    Name = WorldName
                    break
            NewWorld = self.ServerControl.LoadWorld(Name)
        if NewWorld != None and NewWorld != False:
            self.UpdateLastWorldChange()
            self.World.RemovePlayer(self,True)
            #Send packet telling client were changing the world.
            OutPacket = OptiCraftPacket(SMSG_INITIAL)
            OutPacket.WriteByte(7)
            OutPacket.WriteString(self.ServerControl.GetName())
            OutPacket.WriteString("Loading world: %s%s" %(RankToColour[NewWorld.MinRank],NewWorld.Name))
            OutPacket.WriteByte(0)
            self.SendPacket(OutPacket)
            NewWorld.AddPlayer(self,True)
            if self.Invisible == False:
                self.ServerControl.SendJoinMessage("&e%s changed map to %s%s"%(self.Name,RankToColour[NewWorld.MinRank],NewWorld.Name))
        else:
            #World couldn't be loaded (Probably because the block-log is still in use)
            #This is a very very rare condition which can occur on slow computers with high load (100+ users etc)
            self.SendMessage("&4Could not change your world. Try again in a minute")


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
    def SetSpawnPosition(self,x,y,z,o,p):
        '''Stores client position. X Y Z are floats with the fractal bit at position 5'''
        self.SpawnX = x
        self.SpawnY = y
        self.SpawnZ = z
        self.SpawnO = o
        self.SpawnP = p
    def GetSpawnPosition(self):
        return self.SpawnX, self.SpawnY, self.SpawnZ, self.SpawnO,self.SpawnP
    def GetX(self):
        return self.X
    def GetY(self):
        return self.Y
    def GetLoginTime(self):
        return self.LoginTime
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
        self.ColouredName = '%s%s' %(RankToColour[self.Rank],self.Name)
    def HasPermission(self,Permission):
        return RankToLevel[self.Rank] >= RankToLevel[Permission]
    def SetBlockOverride(self,Block):
        self.BlockOverride = Block
    def GetBlockOverride(self):
        return self.BlockOverride
    def GetPaintCmd(self):
        return self.PaintCmd
    def SetPaintCmd(self,Value):
        self.PaintCmd = Value
    def GetAboutCmd(self):
        return self.AboutCmd
    def SetAboutCmd(self,Value):
        self.AboutCmd = Value
    def GetTowerCmd(self):
        return self.TowerCmd
    def SetTowerCmd(self,Value):
        self.TowerCmd = Value
    def GetLastAction(self):
        return self.LastAction
    def IsAuthenticated(self):
        return self.IsIdentified
    def GetJoinNotifications(self):
        return self.JoinNotifications
    def SetJoinNotifications(self, Value):
        self.JoinNotifications = int(Value)
    def GetTimePlayed(self):
        return self.TimePlayed
    def GetKickCount(self):
        return self.KickCount
    def IncreaseKickCount(self):
        self.KickCount += 1
    def GetIpLog(self):
        return self.LastIps
    def GetBlocksErased(self):
        return self.BlocksErased
    def IncreaseBlocksErased(self):
        self.BlocksErased += 1
    def GetBlocksMade(self):
        return self.BlocksMade
    def IncreaseBlocksMade(self):
        self.BlocksMade += 1
    def GetJoinedTime(self):
        return self.JoinTime
    def GetChatMessageCount(self):
        return self.ChatMessageCount
    def IncreaseChatMessageCount(self):
        self.ChatMessageCount += 1
    def GetLoginCount(self):
        return self.LoginCount
    def IncreaseLoginCount(self):
        self.LoginCount += 1
    def GetLastWorldChange(self):
        return self.LastWorldChange
    def UpdateLastWorldChange(self):
        self.LastWorldChange = int(self.ServerControl.Now)
    def IsDataLoaded(self):
        return self.DataIsLoaded
    def UpdatePlayedTime(self):
        self.TimePlayed += int(self.ServerControl.Now) - self.LastPlayedTimeUpdate
        self.LastPlayedTimeUpdate = int(self.ServerControl.Now)

    def IsInvisible(self):
        return self.Invisible
    def SetInvisible(self, Value):
        if Value == True:
            self.Invisible = True
            Packet = OptiCraftPacket(SMSG_PLAYERLEAVE)
            Packet.WriteByte(self.GetId())
            for pPlayer in self.World.Players:
                #Make us invisible to all players who shouldnt be able to see us
                if pPlayer != self and self.CanBeSeenBy(pPlayer) == False:
                    pPlayer.SendPacket(Packet)
        else:
            #Make us visible to all those who previously couldnt see us.
            Packet = OptiCraftPacket(SMSG_SPAWNPOINT)
            Packet.WriteByte(self.GetId())
            Packet.WriteString(self.GetColouredName())
            Packet.WriteInt16(self.GetX())
            Packet.WriteInt16(self.GetZ())
            Packet.WriteInt16(self.GetY())
            Packet.WriteByte(self.GetOrientation())
            Packet.WriteByte(self.GetPitch())
            for pPlayer in self.World.Players:
                if self.CanBeSeenBy(pPlayer) == False:
                    pPlayer.SendPacket(Packet)
            self.Invisible = False

    def CanBeSeenBy(self,pPlayer):
        '''Can i be seen by pPlayer'''
        if self.Invisible and RankToLevel[self.Rank] > RankToLevel[pPlayer.GetRank()]:
            return False
        else:
            return True
    def LoadData(self,Row):
        self.DataIsLoaded = True
        if Row == None:
            #No data found, must be the first login.
            self.LastIps = self.GetIP()
            self.JoinTime = int(self.ServerControl.Now)
            self.LoginCount = 1
        else:
            self.JoinTime = Row["Joined"]
            self.BlocksMade = Row["BlocksMade"]
            self.BlocksErased = Row["BlocksDeleted"]
            self.LastIps = Row["IpLog"]
            self.JoinNotifications = Row["JoinNotifications"]
            self.ChatMessageCount = Row["ChatLines"]
            self.KickCount = Row["KickCount"]
            self.TimePlayed = Row["PlayedTime"]
            self.LoginCount = Row["LoginCount"] + 1

            #Update the IpLog
            Tokens = self.LastIps.split(",")
            if self.GetIP() not in Tokens:
                self.LastIps = "%s,%s" %(self.LastIps,self.GetIP())


    def Teleport(self,x,y,z,o,p):
        '''Teleports the player to X Y Z. These coordinates have the fractal bit at position 5'''
        self.SetLocation(x, y, z, o, p)
        Packet = OptiCraftPacket(SMSG_PLAYERPOS)
        Packet.WriteByte(255)
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

    def SetLastPM(self,Username):
        self.LastPmUsername = Username
    def GetLastPM(self):
        return self.LastPmUsername
    def CalcDistance(self,x,y,z):
        '''Returns the distance to another point in absolute coordinates'''
        dx = self.X/32 - x
        dy = self.Y/32 - y
        dz = self.Z/32 - z
        return math.sqrt(dx*dx+dy*dy+dz*dz)
    #Opcode handlers go below this line
    def HandleIdentify(self,Packet):
        '''Handles the initial packet sent by the client'''
        if self.IsIdentified == True:
            return

        Version = Packet.GetByte()
        self.Name = Packet.GetString()
        HashedPass = Packet.GetString().strip("0")
        CorrectPass = hashlib.md5(self.ServerControl.Salt + self.Name).hexdigest().strip("0")
        if Version != 7:
            self.Disconnect("Your client is incompatible with this server")
            return

        if self.ServerControl.GetPlayerFromName(self.Name) != None:
            Console.Debug("Player","%s tried to connect but is already online." %self.Name)
            self.Disconnect("Disconnecting your duplicate login. Please reconnect.")
            self.ServerControl.GetPlayerFromName(self.Name).Disconnect("Disonnecting for second login")
            return
        if self.ServerControl.IsBanned(self) == True:
            Console.Debug("Player","Banned player %s tried to connect." %self.Name)
            self.Disconnect("You are banned!")
            return
        
        if CorrectPass == HashedPass or self.ServerControl.LanMode == True:
            Console.Out("Player", "%s connected to the server" %self.Name)
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
            self.ColouredName = '%s%s' %(RankToColour[self.Rank],self.Name)
            if self.ServerControl.EnableIRC:
                self.ServerControl.IRCInterface.HandleLogin(self.GetName())
            self.ServerControl.PlayerDBThread.Tasks.put(["GET_PLAYER",self.Name.lower()])

            return
        else:
            Console.Warning("Player","%s Failed to authenticate. Disconnecting" %self.Name)
            self.Disconnect("Could not authenticate your username.")
            return
    def HandleMovement(self,Packet):
        #This is sent even when the player isn't moving!
        if self.World is not None:
            Packet.GetByte()
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
            NewPacket.WriteInt16(x)
            NewPacket.WriteInt16(z)
            NewPacket.WriteInt16(y)
            NewPacket.WriteByte(o)
            NewPacket.WriteByte(p)
            self.World.SendPacketToAll(NewPacket)

    def HandleBlockChange(self,Packet):
        if self.World is not None:
            self.LastAction = self.ServerControl.Now
            x = Packet.GetInt16()
            z = Packet.GetInt16()
            y = Packet.GetInt16()
            Mode = Packet.GetByte()
            Block = Packet.GetByte()
            Result = None
            #Flood detection
            if self.ServerControl.BlockChangePeriod and self.Rank == 'g':
                if self.ServerControl.Now - self.BlockChangeTime > self.ServerControl.BlockChangePeriod:
                    self.BlockChangeTime = self.ServerControl.Now
                    self.BlockChangeCount = 0
                self.BlockChangeCount += 1
                if self.BlockChangeCount > self.ServerControl.BlockChangeCount:
                    self.Disconnect("Antigrief: You are changing too many blocks")
                    return

            if Mode == 0:
                self.IncreaseBlocksErased()
                if self.GetPaintCmd() == True:
                     if self.BlockOverride != -1:
                         Block = self.BlockOverride
                     self.World.AttemptSetBlock(self,x,y,z,Block)
                     Result = False
                else:
                    Result = self.World.AttemptSetBlock(self,x,y,z,0)
            else:
                self.IncreaseBlocksMade()
                if self.BlockOverride != -1:
                    Block = self.BlockOverride
                Result = self.World.AttemptSetBlock(self,x,y,z,Block)
            if Result != True or self.GetBlockOverride() != -1:
                if self.World.WithinBounds(x, y, z):
                    self.World.SendBlock(self,x,y,z)
            
    def HandleChatMessage(self,Packet):
        if self.World == None:
            return
        self.IncreaseChatMessageCount()
        self.LastAction = self.ServerControl.Now
        Packet.GetByte() #junk
        Contents = Packet.GetString().translate(None,DisabledChars)
        if len(Contents) == 0:
            return
        if Contents[0] == "/":
            self.ServerControl.CommandHandle.HandleCommand(self,Contents[1:])
        elif Contents[0] == "@":
            self.HandlePrivateMessage(Contents[1:])
        else:
            if self.ServerControl.AllowCaps == False:
                if Contents == Contents.upper() and len(Contents) >= self.ServerControl.MinCapsLength:
                    self.SendMessage("&4Do not use caps!")
                    return
            if self.ServerControl.FloodPeriod:
                if self.ServerControl.Now - self.FloodPeriodTime >= self.ServerControl.FloodPeriod:
                    self.FloodPeriodTime = self.ServerControl.Now
                    self.FloodPeriodCount = 0
                self.FloodPeriodCount += 1
                if self.FloodPeriodCount > self.ServerControl.FloodMessageLimit:
                    self.SendMessage("&4You are sending messages too quickly. Slow down!")
                    self.FloodPeriodTime = self.ServerControl.Now #reset the count. Stops them spamming.
                    return
            self.ServerControl.SendChatMessage(self.GetColouredName(),Contents)
            if self.ServerControl.LogChat:
                TimeFormat = time.strftime("%d %b %Y [%H:%M:%S]",time.localtime())
                self.ServerControl.ChatLogHandle.write("%s <%s>: %s\n" %(TimeFormat,self.GetName(),Contents))
            if self.ServerControl.EnableIRC:
                self.ServerControl.IRCInterface.HandleIngameMessage(self.GetColouredName(),Contents)

    def HandlePrivateMessage(self,Message):
        if len(Message) == 0:
            self.SendMessage("&4Enter in a username to PM!")
            return
        Tokens = Message.split()
        Username = Tokens[0]
        Contents = ' '.join(Tokens[1:])
        Reciever = self.ServerControl.GetPlayerFromName(Username)
        if Reciever == None or Reciever.CanBeSeenBy(self) == False:
            self.SendMessage("&4That user is not online!")
            return
        if len(Contents) == 0:
            self.SendMessage("&4Enter something to say!")
            return
        if self.ServerControl.LogChat:
            TimeFormat = time.strftime("%d %b %Y [%H:%M:%S]",time.localtime())
            self.ServerControl.PMLogHandle.write("%s <%s> to <%s>: %s\n" %(TimeFormat,self.GetName(),Reciever.GetName(), Contents))
            
        Reciever.SendMessage('&bfrom %s&b: %s' %(self.GetColouredName(),Contents))
        Reciever.SetLastPM(self.Name)
        self.SendMessage('&bto %s&b: %s' %(Reciever.GetColouredName(), Contents))

    def __init__(self,PlayerSocket,SockAddress,ServerControl):
        self.PlayerSocket = PlayerSocket
        self.PlayerIP = SockAddress
        self.Name = ''
        self.ColouredName = ''
        self.IsIdentified = False
        self.Id = -1
        self.ServerControl = ServerControl
        self.World = None #Pointer to our current world.
        self.IsLoading = False
        self.AboutCmd = False
        self.PaintCmd = False
        self.TowerCmd = False
        self.Rank = 'g'
        self.Invisible = False
        self.CreatingZone = False
        self.ZoneData = dict()
        self.LoginTime = int(self.ServerControl.Now)
        self.LastPlayedTimeUpdate = self.LoginTime
        self.LastAction = self.LoginTime
        self.FloodPeriodCount = 0
        self.FloodPeriodTime = self.ServerControl.Now
        self.BlockChangeCount = 0
        self.BlockChangeTime = self.ServerControl.Now
        self.LastPmUsername = ''
        self.LastWorldChange = 0
        self.Disconnecting = False
        self.DataIsLoaded = False
        self.ChatMessageCount = 0
        self.BlocksMade = 0
        self.KickCount = 0 
        self.BlocksErased = 0
        self.LastIps = ''
        self.JoinNotifications = 1
        self.JoinTime = 0 #This it the time when the player logged in for the first time ever
        self.TimePlayed = 0
        self.LoginCount = 0
        #This is used for commands such as /lava, /water, and /grass
        self.BlockOverride = -1


        self.X,self.Y,self.Z,self.O,self.P = -1,-1,-1,-1,-1 #X,Y,Z,Orientation and pitch with the fractional position at 5 bits
        self.SpawnX,self.SpawnY,self.SpawnZ,self.SpawnO,self.SpawnP = -1,-1,-1,-1,-1 #Used to spawn at a location when chaning worlds

        self.OutBuffer = cStringIO.StringIO()
        Console.Debug("Player","Player object created. IP: %s" %SockAddress[0])
        self.SockBuffer = cStringIO.StringIO()
        self.OpcodeHandler = {
            CMSG_IDENTIFY: self.HandleIdentify,
            CMSG_BLOCKCHANGE: self.HandleBlockChange,
            CMSG_POSITIONUPDATE: self.HandleMovement,
            CMSG_MESSAGE: self.HandleChatMessage
        }


