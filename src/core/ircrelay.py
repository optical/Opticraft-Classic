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


from core.console import Console
from core.constants import *
from core.ircclient import IRCClient

class RelayBot(IRCClient):
    COLOUR_CODE = chr(0x03)
    def __init__(self,Nick,Email,RealName,ServerControl):
        IRCClient.__init__(self,Nick,Email,RealName)
        self.AddPacketHandler("001", self.OnConnection)
        self.ServerControl = ServerControl
        self.Channel = self.ServerControl.IRCChannel.lower()
        self.GameToIrc = self.ServerControl.IRCGameToIRC
        self.IRCToGame = self.ServerControl.IRCIRCToGame
        self.Host = self.ServerControl.IRCServer
        self.Port = self.ServerControl.IRCPort
        self.IdentificationMessage = self.ServerControl.IRCIdentificationMessage
        self.ColourMap = dict()
        self.PopulateColourMap()
        self.FloodControl = dict()
        if self.IRCToGame:
            self.AddPacketHandler("PRIVMSG",self.HandlePrivMsg)
            self.AddPacketHandler("PART", self.OnPart)
            self.AddPacketHandler("QUIT", self.OnQuit)
            self.AddPacketHandler("NICK", self.OnPart)
    def HandlePrivMsg(self,Data):
        if self.IRCToGame:
            Tokens = Data.split()
            if Tokens[2].lower() == self.Channel:
                Username = Tokens[0].split("!")[0][1:]
                #Flood prevention
                if self.ServerControl.FloodPeriod:
                    if self.FloodControl.has_key(Username):
                        UserData = self.FloodControl[Username]
                        #Userdata is a list of 2 items, FloodTime and FloodCount
                        if self.ServerControl.Now - UserData[0] > self.ServerControl.FloodPeriod:
                            UserData[0] = self.ServerControl.Now
                            UserData[1] = 1
                        else:
                            #Increase message count by one
                            UserData[1] += 1
                            #If we exceed the limit, ignore the message and reset their time
                            #(This prevents them from speaking for another whole period)
                            if UserData[1] >= self.ServerControl.FloodMessageLimit:
                                UserData[0] = self.ServerControl.Now
                                return
                    else:
                        #Add them to the map
                        self.FloodControl[Username] = [self.ServerControl.Now,1]
                Message = ' '.join(Tokens[3:])[1:]
                Message = Message.translate(None,DisabledChars)
                if Message[0:6] != "ACTION":
                    self.ServerControl.SendChatMessage('&3[IRC]&f-%s' %Username,Message)
                else:
                    self.ServerControl.SendChatMessage('&3[IRC]&5 *%s' %Username, Message[6:],NewLine="&5",NormalStart=False)
    def Connect(self):
        Console.Out("IRC","Connecting to irc server %s on port %d" %(self.Host,self.Port))
        self.connect((self.Host,self.Port))
    def OnConnection(self,Data):
        Console.Out("IRC","Attmpting to join channel %s" %self.Channel)
        self.Write("JOIN %s" %self.Channel)
        Tokens = self.IdentificationMessage.split()
        self.SendMessage(Tokens[0], ' '.join(Tokens[1:]))
    def HandleIngameMessage(self,From,Message):
        if self.GameToIrc:
            for Key in self.ColourMap:
                From = From.replace(Key,self.ColourMap[Key])
            self.SendMessage(self.Channel, '(%s%s): %s' %(From,RelayBot.COLOUR_CODE,Message))
    def HandleEmote(self,From,Message):
        if self.GameToIrc:
            self.SendMessage(self.Channel, '*%s6%s %s' %(RelayBot.COLOUR_CODE,From,Message))
    def HandleLogin(self,Name):
        if self.GameToIrc:
            self.SendMessage(self.Channel,'%s connected to the server' %Name)
    def HandleLogout(self,Name):
        if self.GameToIrc and self.ServerControl.ShuttingDown == False:
            self.SendMessage(self.Channel, '%s left the server' %Name)

    def OnPart(self,Data):
        Tokens = Data.split()
        Username = Tokens[0][1:].split("!")[0]
        Channel = Tokens[2]
        if Channel[0] == ":":
            Channel = Channel[1:]
        if Channel.lower() == self.Channel:
            try:
                del self.FloodControl[Username]
            except:
                pass
    def OnNickChange(self,Data):
        Tokens = Data.split()
        Username = Tokens[0][1:].split("!")[0]
        NewNick = Tokens[2][1:]
        try:
            self.FloodControl[NewNick] = self.FloodControl[Username]
            del self.FloodControl[Username]
        except:
            pass
    def OnQuit(self,Data):
        Tokens = Data.split()
        Username = Tokens[0][1:].split("!")[0]
        try:
            del self.FloodControl[Username]
        except:
            pass
    def OnShutdown(self,Crash):
        self.Write("QUIT :Server is shutting down")

    def PopulateColourMap(self):
        self.ColourMap["&0"] = '' #Black
        self.ColourMap["&1"] = '%s2' %RelayBot.COLOUR_CODE
        self.ColourMap["&2"] = '%s3' %RelayBot.COLOUR_CODE #Dark Blue
        self.ColourMap["&3"] = '%s10' %RelayBot.COLOUR_CODE #Dark Teal
        self.ColourMap["&4"] = '%s4' %RelayBot.COLOUR_CODE #Dark red
        self.ColourMap["&5"] = '%s6' %RelayBot.COLOUR_CODE #Purple
        self.ColourMap["&6"] = '%s8' %RelayBot.COLOUR_CODE #gold
        self.ColourMap["&7"] = '%s14' %RelayBot.COLOUR_CODE #Grey
        self.ColourMap["&8"] = '%s14' %RelayBot.COLOUR_CODE #Dark Grey
        self.ColourMap["&9"] = '%s12' %RelayBot.COLOUR_CODE #blue
        self.ColourMap["&a"] = '%s3' %RelayBot.COLOUR_CODE #Green
        self.ColourMap["&b"] = '%s10' %RelayBot.COLOUR_CODE #Teal
        self.ColourMap["&c"] = '%s4' %RelayBot.COLOUR_CODE  #Red
        self.ColourMap["&d"] = '%s13' %RelayBot.COLOUR_CODE #Pink
        self.ColourMap["&e"] = '%s8' %RelayBot.COLOUR_CODE #Yellow
        self.ColourMap["&f"] = '' #white
