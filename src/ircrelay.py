import asyncore
from console import Console
from ircclient import IRCClient

class RelayBot(IRCClient):
    COLOUR_CODE = chr(0x03)
    def __init__(self,Nick,Email,RealName,ServerControl):
        IRCClient.__init__(self,Nick,Email,RealName)
        self.AddPacketHandler("001", self.OnConnection)
        self.ServerControl = ServerControl
        self.Channel = self.ServerControl.IRCChannel
        self.GameToIrc = self.ServerControl.IRCGameToIRC
        self.IRCToGame = self.ServerControl.IRCIRCToGame
        self.Host = self.ServerControl.IRCServer
        self.Port = self.ServerControl.IRCPort
        self.ColourMap = dict()
        self.PopulateColourMap()
        if self.IRCToGame:
            self.AddPacketHandler("PRIVMSG",self.HandlePrivMsg)

    def HandlePrivMsg(self,Data):
        if self.IRCToGame:
            Tokens = Data.split()
            if Tokens[2] == self.Channel:
                Username = Tokens[0].split("!")[0][1:]
                Message = ' '.join(Tokens[3:])[1:]
                Message = Message.replace('&','')
                self.ServerControl.SendChatMessage('&3[IRC] &f%s' %Username,Message)
    def Connect(self):
        Console.Out("IRC","Connecting to irc server %s on port %d" %(self.Host,self.Port))
        self.connect((self.Host,self.Port))
    def OnConnection(self,Data):
        Console.Out("IRC","Attmpting to join channel %s" %self.Channel)
        self.Write("JOIN %s" %self.Channel)
    def HandleIngameMessage(self,From,Message):
        if self.GameToIrc:
            Message = Message.replace("\r\n",'')
            for Key in self.ColourMap:
                From = From.replace(Key,self.ColourMap[Key])
            self.SendMessage(self.Channel, '(%s%s): %s' %(From,RelayBot.COLOUR_CODE,Message))
    def HandleLogin(self,Name):
        if self.GameToIrc:
            self.SendMessage(self.Channel,'%s connected to the server' %Name)
    def HandleLogout(self,Name):
        if self.GameToIrc:
            self.SendMessage(self.Channel, '%s left the server' %Name)

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
