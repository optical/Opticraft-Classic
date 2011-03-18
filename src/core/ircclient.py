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

import asynchat
import socket
class IRCChannel(object):
    def __init__(self, Name):
        self.Users = set()
        self.Topic = ''
        self.Modes = ''
        self.Name = Name

    def GetUser(self, NickName):
        for User in self.Users:
            if User.GetName() == NickName:
                return User
        return None
    def AddUser(self, User):
        self.Users.add(User)
    def RemoveUser(self, Nickname):
        User = self.GetUser(Nickname)
        if User:
            self.Users.remove(User)
    def HasUser(self, NickName):
        return self.GetUser(NickName) is not None
    def RenameUser(self, OldNick, NewNick):
        self.GetUser(OldNick).SetName(NewNick)
    def GetName(self):
        return self.Name
    def GetUsers(self):
        return self.Users

class IRCUser(object):
    '''Per-Channel user instance'''
    def __init__(self, Name, Mode):
        self.Name = Name
        self.Mode = Mode
        self.Modes = set()
    def GetName(self):
        return self.Name
    def SetName(self, NewNick):
        self.Name = NewNick

class IRCClient(asynchat.async_chat):
    def __init__(self, Nick, Email, RealName):
        asynchat.async_chat.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.Buffer = []
        self.Host = ''
        self.Port = None
        self.Nick = Nick
        self.Email = Email
        self.RealName = RealName
        self.PacketHandlers = {}
        self._populate_handlers()
        self.set_terminator('\r\n')
        self.Channels = []
        self.Connected = False
        self.ReconnectAttempts = 0
        self.MaxReconnectAttempts = 5


    def _populate_handlers(self):
        self.AddPacketHandler("353", self._OnNames)
        self.AddPacketHandler("JOIN", self._OnJoin)
        self.AddPacketHandler("PART", self._OnPart)
        self.AddPacketHandler("NICK", self._OnNickChange)
        self.AddPacketHandler("QUIT", self._OnQuit)

    def AddPacketHandler(self, Packet, Function):
        PackList = self.PacketHandlers.get(Packet.lower(), None)
        if PackList is None:
            self.PacketHandlers[Packet.lower()] = list()
            PackList = self.PacketHandlers[Packet.lower()]
        PackList.append(Function)

    def Connect(self, Host, Port):
        self.Host = Host
        self.Port = Port
        self.connect((Host, Port))
    def SetMaxReconnectAttempts(self, Attempts):
        self.MaxReconnectAttempts = Attempts

    def collect_incoming_data(self, data):
        self.Buffer.append(data)

    def found_terminator(self):
        Packet = ''.join(self.Buffer)
        self.Buffer = list()
        Tokens = Packet.strip().split()
        if Tokens[0] == "PING":
            self.Write("PONG %s" % Tokens[1])
            return
        Handler = self.PacketHandlers.get(Tokens[1].lower(), None)
        if Handler is not None:
            for Function in Handler:
                Function(Packet)

    def handle_connect(self):
        self.Write('NICK %s' % self.Nick)
        self.Write('USER %s "" "%s" :%s' % (self.Email, self.Host, self.RealName))
    def handle_close(self):
        if self.Host != '' and self.ReconnectAttempts < self.MaxReconnectAttempts:
            self.ReconnectAttempts += 1
            try:
                self.connect((self.Host, self.Port))
            except:
                pass
            else:
                self.ReconnectAttempts = 0
        else:
            self.close()

    def Write(self, Data):
        self.push('%s\r\n' % (Data))

    def JoinChannel(self, Channel):
        self.Write("JOIN %s" % Channel)
    def PartChannel(self, Channel):
        self.Write("PART %s" % Channel)
    def SendMessage(self, Destination, Message):
        self.Write("PRIVMSG %s :%s" % (Destination, Message))


    def GetChannel(self, ChannelName):
        for Channel in self.Channels:
            if Channel.GetName() == ChannelName:
                return Channel
        return None
    def InChannel(self, ChannelName):
        return self.GetChannel(ChannelName) is not None

    def _OnJoin(self, Data):
        Tokens = Data.split()
        Username = Tokens[0][1:].split("!")[0]
        Channel = Tokens[2]
        if Channel[0] == ":":
            Channel = Channel[1:]

        if Username == self.Nick:
            if self.InChannel(Channel):
                pass
            else:
                pChannel = IRCChannel(Channel)
                pChannel.AddUser(IRCUser(self.Nick, ''))
                self.Channels.append(pChannel)
        else:
            pChannel = self.GetChannel(Channel)
            pChannel.AddUser(IRCUser(Username, ''))

    def _OnNames(self, Data):
        Tokens = Data.split()
        if Tokens[2] != self.Nick:
            return
        Channel = Tokens[4]
        Nicks = Tokens[5:]
        if len(Tokens) == 4:
            return
        pChannel = self.GetChannel(Channel)
        if pChannel is None:
            return
        Nicks[0] = Nicks[0][1:]
        for Nick in Nicks:
            if Nick[0] in ['+', '@', '%', '&', '~']:
                Mode = Nick[0]
                Nick = Nick[1:]
            else:
                Mode = ''
            pChannel.AddUser(IRCUser(Nick, Mode))


    def _OnPart(self, Data):
        Tokens = Data.split()
        Username = Tokens[0][1:].split("!")[0]
        Channel = Tokens[2]
        if Channel[0] == ":":
            Channel = Channel[1:]
        if Username == self.Nick:
            self.Channels.remove(self.GetChannel(Channel))
        else:
            self.GetChannel(Channel).RemoveUser(Username)

    def _OnNickChange(self, Data):
        Tokens = Data.split()
        Username = Tokens[0][1:].split("!")[0]
        NewNick = Tokens[2][1:]
        if Username == self.Nick:
            self.Nick = NewNick
        for Channel in self.Channels:
            if Channel.HasUser(Username):
                Channel.RenameUser(Username, NewNick)
    def _OnQuit(self, Data):
        Tokens = Data.split()
        Username = Tokens[0][1:].split("!")[0]
        Reason = ' '.join(Tokens[2:])
        Reason = Reason[1:]
        for Channel in self.Channels:
            if Channel.HasUser(Username):
                Channel.RemoveUser(Username)
