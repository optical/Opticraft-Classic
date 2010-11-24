import asyncore
from ircclient import IRCClient

class RelayBot(IRCClient):
    def __init__(self,Nick,Email,RealName,ServerControl):
        IRCClient.__init__(self,Nick,Email,RealName)
        self.AddPacketHandler("001", self.OnConnection)
        self.ServerControl = ServerControl
        self.Channel = self.ServerControl.IRCChannel
        self.GameToIrc = self.ServerControl.IRCGameToIRC
        self.IRCToGame = self.ServerControl.IRCIRCToGame
        self.Host = self.ServerControl.IRCServer
        self.Port = self.ServerControl.IRCPort
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
        self.connect((self.Host,self.Port))
    def OnConnection(self,Data):
        self.Write("JOIN %s" %self.Channel)
    def HandleIngameMessage(self,From,Message):
        if self.GameToIrc:
            Message = Message.replace("\r\n",'')
            self.SendMessage(self.Channel, '(%s): %s' %(From,Message))
    def HandleLogin(self,Name):
        if self.GameToIrc:
            self.SendMessage(self.Channel,'%s connected to the server' %Name)
    def HandleLogout(self,Name):
        if self.GameToIrc:
            self.SendMessage(self.Channel, '%s left the server' %Name)