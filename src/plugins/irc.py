from core.console import Console
from core.constants import *
from core.ircclient import IRCClient
from core.pluginmanager import PluginBase, Hooks

import asyncore

class IRCPlugin(PluginBase):
    def __init__(self, PluginMgr, ServerControl, Name):
        PluginBase.__init__(self, PluginMgr, ServerControl, Name)
        self.EnableIRC = bool(int(ServerControl.ConfigValues.GetValue("irc", "EnableIRC", "0")))
        self.IRCServer = ServerControl.ConfigValues.GetValue("irc", "Server", "irc.esper.net")
        self.IRCPort = int(ServerControl.ConfigValues.GetValue("irc", "Port", "6667"))
        self.IRCChannel = ServerControl.ConfigValues.GetValue("irc", "Channel", "#a")
        self.IRCNick = ServerControl.ConfigValues.GetValue("irc", "Nickname", "Optibot")
        self.IRCGameToIRC = bool(int(ServerControl.ConfigValues.GetValue("irc", "GameChatRelay", "0")))
        self.IRCIRCToGame = bool(int(ServerControl.ConfigValues.GetValue("irc", "IrcChatRelay", "0")))
        self.IRCRelayGameJoins = bool(int(ServerControl.ConfigValues.GetValue("irc", "GameJoinsRelay", "0")))
        self.IRCRelayIRCJoins = bool(int(ServerControl.ConfigValues.GetValue("irc", "IrcJoinsRelay", "0")))
        self.IRCIdentificationMessage = ServerControl.ConfigValues.GetValue("irc", "IdentifyCommand", "NickServ identify")
        self.IRCInterface = None
         
    def OnLoad(self):
        if self.EnableIRC:
            self.IRCInterface = RelayBot(self.IRCNick, "Opticraft", "Opticraft", self, self.ServerControl)
            self.IRCInterface.Connect()
        self.PluginMgr.RegisterHook(self, self.OnTick, Hooks.ON_SERVER_TICK)
        self.PluginMgr.RegisterHook(self, self.OnChat, Hooks.ON_PLAYER_CHAT)
        self.PluginMgr.RegisterHook(self, self.OnPlayerLogin, Hooks.ON_PLAYER_CONNECT)
        self.PluginMgr.RegisterHook(self, self.OnPlayerLogout, Hooks.ON_PLAYER_DISCONNECT)
        self.PluginMgr.RegisterHook(self, self.OnServerShutdown, Hooks.ON_SERVER_SHUTDOWN)
        self.PluginMgr.RegisterHook(self, self.OnEmote, Hooks.ON_PLAYER_EMOTE)
        
    def OnUnload(self):
        if self.EnableIRC:
            self.IRCInterface.OnUnload()
            asyncore.loop(timeout = 0.001, count = 1)
        
    def OnTick(self):
        if self.EnableIRC:
            asyncore.loop(count = 1, timeout = 0.001)
            
    def OnPlayerLogin(self, pPlayer):
        if self.EnableIRC:
            self.IRCInterface.HandleLogin(pPlayer.GetName())
    
    def OnChat(self, pPlayer, Message):
        if self.EnableIRC:
            self.IRCInterface.HandleIngameMessage(pPlayer.GetColouredName(), Message)
    
    def OnPlayerLogout(self, pPlayer):
        if self.EnableIRC:
            self.IRCInterface.HandleLogout(pPlayer.GetName())
        
    def OnServerShutdown(self):
        if self.EnableIRC:
            self.IRCInterface.OnShutdown()
            
    def OnEmote(self, pPlayer, Message):
        if self.EnableIRC:
            self.IRCInterface.HandleEmote(pPlayer.GetName(), Message)
    

class RelayBot(IRCClient):
    COLOUR_CODE = chr(0x03)
    def __init__(self, Nick, Email, RealName, Plugin, ServerControl):
        IRCClient.__init__(self, Nick, Email, RealName)
        self.ServerControl = ServerControl
        self.AddPacketHandler("001", self.OnConnection)
        self.Channel = Plugin.IRCChannel.lower()
        self.GameToIrc = Plugin.IRCGameToIRC
        self.IRCToGame = Plugin.IRCIRCToGame
        self.IRCJoinsToGame = Plugin.IRCRelayIRCJoins
        self.GameJoinsToIRC = Plugin.IRCRelayGameJoins
        self.Host = Plugin.IRCServer
        self.Port = Plugin.IRCPort
        self.IdentificationMessage = Plugin.IRCIdentificationMessage
        self.ColourMap = dict()
        self.PopulateColourMap()
        self.FloodControl = dict()
        if self.IRCToGame:
            self.AddPacketHandler("PRIVMSG", self.HandlePrivMsg)
            self.AddPacketHandler("PART", self.OnPart)
            self.AddPacketHandler("QUIT", self.OnQuit)
            self.AddPacketHandler("NICK", self.OnNickChange)
            self.AddPacketHandler("JOIN", self.OnJoin)
            
    def HandlePrivMsg(self, Data):
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
                        self.FloodControl[Username] = [self.ServerControl.Now, 1]
                Message = ' '.join(Tokens[3:])[1:]
                Message = Message.translate(None, DisabledChars)
                if Message[0:6] != "ACTION":
                    self.ServerControl.SendChatMessage('&3[IRC]&f-%s' % Username, Message)
                else:
                    self.ServerControl.SendChatMessage('&3[IRC]&5 *%s' % Username, Message[6:], NewLine = "&5", NormalStart = False)

    def Connect(self):
        Console.Out("IRC", "Connecting to irc server %s on port %d" % (self.Host, self.Port))
        self.connect((self.Host, self.Port))
        
    def OnConnection(self, Data):
        Console.Out("IRC", "Attmpting to join channel %s" % self.Channel)
        self.Write("JOIN %s" % self.Channel)
        Tokens = self.IdentificationMessage.split()
        self.SendMessage(Tokens[0], ' '.join(Tokens[1:]))
        
    def HandleIngameMessage(self, From, Message):
        if self.GameToIrc:
            for Key in self.ColourMap:
                From = From.replace(Key, self.ColourMap[Key])
                Message = Message.replace(Key, self.ColourMap[Key])
                
            self.SendMessage(self.Channel, '(%s%s): %s' % (From, RelayBot.COLOUR_CODE, Message))
            
    def HandleEmote(self, From, Message):
        if self.GameToIrc:
            self.SendMessage(self.Channel, '*%s6%s %s' % (RelayBot.COLOUR_CODE, From, Message))
            
    def HandleLogin(self, Name):
        if self.GameJoinsToIRC:
            self.SendMessage(self.Channel, '%s connected to the server' % Name)
            
    def HandleLogout(self, Name):
        if Name == "":
            return
        if self.GameJoinsToIRC and self.ServerControl.ShuttingDown == False:
            self.SendMessage(self.Channel, '%s left the server' % Name)

    def OnPart(self, Data):
        Tokens = Data.split()
        Username = Tokens[0][1:].split("!")[0]
        Channel = Tokens[2]
        if Channel[0] == ":":
            Channel = Channel[1:]
        if Channel.lower() == self.Channel:
            if self.IRCJoinsToGame:
                self.ServerControl.SendChatMessage("&3[IRC]", "&e%s has left the chat" % Username, NormalStart = False)
                
            try:
                del self.FloodControl[Username]
            except:
                pass
    
    def OnJoin(self, Data):
        Tokens = Data.split()
        Username = Tokens[0][1:].split("!")[0]
        Channel = Tokens[2]
        if Channel[0] == ":":
            Channel = Channel[1:]

        if Username != self.Nick and self.IRCJoinsToGame:
            self.ServerControl.SendChatMessage("&3[IRC]", "&e%s has joined the chat" % Username, NormalStart = False)
    
    def OnNickChange(self, Data):
        Tokens = Data.split()
        Username = Tokens[0][1:].split("!")[0]
        NewNick = Tokens[2][1:]
        if self.IRCJoinsToGame:
            self.ServerControl.SendChatMessage("&3[IRC]", "&e%s is now known as %s" % (Username, NewNick), NormalStart = False)
        try:
            self.FloodControl[NewNick] = self.FloodControl[Username]
            del self.FloodControl[Username]
        except:
            pass
        
    def OnQuit(self, Data):
        Tokens = Data.split()
        Username = Tokens[0][1:].split("!")[0]
        if self.IRCJoinsToGame:
            self.ServerControl.SendChatMessage("&3[IRC]", "&e%s has left the chat" % Username, NormalStart = False)
        try:
            del self.FloodControl[Username]
        except:
            pass
        
    def OnUnload(self):
        self.Write("QUIT :I've been unloaded!")
        
    def OnShutdown(self):
        self.Write("QUIT :Server is shutting down")

    def PopulateColourMap(self):
        self.ColourMap["&0"] = '' #Black
        self.ColourMap["&1"] = '%s2' % RelayBot.COLOUR_CODE
        self.ColourMap["&2"] = '%s3' % RelayBot.COLOUR_CODE #Dark Blue
        self.ColourMap["&3"] = '%s10' % RelayBot.COLOUR_CODE #Dark Teal
        self.ColourMap["&4"] = '%s4' % RelayBot.COLOUR_CODE #Dark red
        self.ColourMap["&5"] = '%s6' % RelayBot.COLOUR_CODE #Purple
        self.ColourMap["&6"] = '%s7' % RelayBot.COLOUR_CODE #gold
        self.ColourMap["&7"] = '%s14' % RelayBot.COLOUR_CODE #Grey
        self.ColourMap["&8"] = '%s14' % RelayBot.COLOUR_CODE #Dark Grey
        self.ColourMap["&9"] = '%s12' % RelayBot.COLOUR_CODE #blue
        self.ColourMap["&a"] = '%s3' % RelayBot.COLOUR_CODE #Green
        self.ColourMap["&b"] = '%s10' % RelayBot.COLOUR_CODE #Teal
        self.ColourMap["&c"] = '%s4' % RelayBot.COLOUR_CODE  #Red
        self.ColourMap["&d"] = '%s13' % RelayBot.COLOUR_CODE #Pink
        self.ColourMap["&e"] = '%s8' % RelayBot.COLOUR_CODE #Yellow
        self.ColourMap["&f"] = '' #white
