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

import random
import time
import os
import os.path
import signal
import platform
import asyncore
import sqlite3 as dbapi
import threading
import Queue
from core.heartbeatcontrol import HeartBeatController
from core.opticraftpacket import OptiCraftPacket
from core.optisockets import SocketManager
from core.commandhandler import CommandHandler
from core.configreader import ConfigReader
from core.zones import Zone
from core.world import World, WorldLoadFailedException
from core.constants import *
from core.console import *
from core.ircrelay import RelayBot
class SigkillException(Exception):
    pass
class PlayerDbThread(threading.Thread):
    '''This thread performs asynchronous querys on the player databases, specifically for loading
    and saving player data'''
    CURRENT_VERSION = 2
    def __init__(self,ServerControl):
        threading.Thread.__init__(self)
        self.ServerControl = ServerControl
        self.Tasks = Queue.Queue()
        self.Connection = None
        self.Running = True

    def SavePlayerData(self,pPlayer):
        QueryString = "REPLACE INTO Players Values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        try:
            self.Connection.execute(QueryString,(pPlayer.GetName().lower(),pPlayer.GetJoinedTime(),pPlayer.GetLoginTime(),
                                    pPlayer.GetBlocksMade(),pPlayer.GetBlocksErased(),pPlayer.GetIP(),pPlayer.GetIpLog(),
                                    pPlayer.GetJoinNotifications(),pPlayer.GetTimePlayed(),pPlayer.GetKickCount(),
                                    pPlayer.GetChatMessageCount(),pPlayer.GetLoginCount(),pPlayer.GetBannedBy(),pPlayer.GetRankedBy()))
            self.Connection.commit()
        except dbapi.OperationalError:
            #Try again later
            Console.Debug("PlayerDB","Failed to save player %s. Trying again soon" %pPlayer.GetName())
            self.Tasks.put(["SAVE_PLAYER",pPlayer])

    def Initialise(self):
        self.Connection = dbapi.connect("Player.db")
        self.Connection.text_factory = str
        self.Connection.row_factory = dbapi.Row
        Console.Out("PlayerDB","Successfully connected to Player.db")
        Result = self.Connection.execute("SELECT * FROM sqlite_master where name='Server' and type='table'")
        if Result.fetchone() == None:
            #Create the DB
            Console.Warning("PlayerDB","No data exists in Player.db. Creating Tables")
            self.Connection.execute("CREATE TABLE Server (DatabaseVersion INTEGER)")
            CreateQuery = "CREATE TABLE Players (Username TEXT UNIQUE,"
            CreateQuery += "Joined INTEGER, LastLogin INTEGER, BlocksMade INTEGER,"
            CreateQuery += "BlocksDeleted INTEGER, LastIP TEXT, IpLog TEXT, JoinNotifications INTEGER,"
            CreateQuery += "PlayedTime INTEGER, KickCount INTEGER, ChatLines INTEGER, LoginCount INTEGER, BannedBy TEXT, RankedBy TEXT)"
            self.Connection.execute(CreateQuery)
            self.Connection.execute("CREATE INDEX Username ON Players (Username)")
            self.Connection.execute("INSERT INTO Server VALUES (?)", (PlayerDbThread.CURRENT_VERSION,))
            self.Connection.commit()
        else:
            #Check the version
            Result = self.Connection.execute("SELECT * from Server")
            Version = Result.fetchone()[0]
            if Version < PlayerDbThread.CURRENT_VERSION:
                Console.Warning("PlayerDB","Player database is out of date. Updating now...")
                while Version < PlayerDbThread.CURRENT_VERSION:
                    if Version == 1:
                        self._Apply1To2()
                    Version += 1
                    Console.Warning("PlayerDB","Player database now at version %d" %Version)
                self.Connection.execute("DELETE FROM Server")
                self.Connection.execute("INSERT INTO Server VALUES (?)", (PlayerDbThread.CURRENT_VERSION,))
                self.Connection.commit()
                Console.Out("PlayerDB","Player database is now up to date.")

    def run(self):
        self.Initialise()
        while self.Running:
            Task = self.Tasks.get()
            if Task[0] == "GET_PLAYER":
                self.LoadPlayerData(Task[1])
            elif Task[0] == "SAVE_PLAYER":
                self.SavePlayerData(Task[1])
            elif Task[0] == "EXECUTE":
                self.Execute(Task[1],Task[2])
            elif Task[0] == "SHUTDOWN":
                self.Connection.commit()
                self.Running = False
                self.Connection.close()

    def Execute(self,QueryText,Args):
        '''Executes a query on the database'''
        try:
            self.Connection.execute(QueryText,Args)
            self.Connection.commit()
        except:
            pass
    def LoadPlayerData(self,Username):
        '''This function will never throw an exception, unless a plugin is incorrectly executing a query in the wrong thread'''
        Result = self.Connection.execute("SELECT * FROM Players where Username = ?", (Username,))
        Result = Result.fetchone()
        self.ServerControl.LoadResults.put((Username,Result))

    #Version updates..
    def _Apply1To2(self):
        self.Connection.execute("ALTER TABLE Players ADD COLUMN BannedBy TEXT DEFAULT ''")
        self.Connection.execute("ALTER TABLE Players ADD COLUMN RankedBy TEXT DEFAULT ''")



class ServerController(object):
    def __init__(self):
        self.StartTime = int(time.time())
        self.ConfigValues = ConfigReader()
        self.RankStore = ConfigReader()
        self.ConfigValues.read("opticraft.ini")
        self.RankStore.read("ranks.ini")
        self.Host = self.ConfigValues.GetValue("server","ListenInterface",'0.0.0.0')
        if self.Host == '0.0.0.0':
            self.Host = ''
        #Check to see we have required directory's
        if os.path.exists("Worlds") == False:
            os.mkdir("Worlds")
        if os.path.exists("Backups") == False:
            os.mkdir("Backups")
        if os.path.exists("Zones") == False:
            os.mkdir("Zones")
        if os.path.exists("Logs") == False:
            os.mkdir("Logs")
        if os.path.exists("Templates") == False:
            os.mkdir("Templates")
        Console.SetLogLevel(int(self.ConfigValues.GetValue("logs","ConsoleLogLevel",LOG_LEVEL_DEBUG)))
        Console.SetFileLogging(bool(int(self.ConfigValues.GetValue("logs","ConsoleFileLogs","0"))))
        Console.SetColour(int(self.ConfigValues.GetValue("server","ConsoleColour","1")))
        Console.Out("Startup","Opticraft is starting up.")
        self.Port = int(self.ConfigValues.GetValue("server","Port","25565"))
        self.Salt = str(random.randint(1,0xFFFFFFFF-1))
        #Check to see if we have a salt saved to disk.
        if os.path.exists("opticraft.salt"):
            #Load this salt instead.
            try:
                saltHandle = open("opticraft.salt","r")
                self.Salt = saltHandle.readline().strip()
                saltHandle.close()
            except IOError:
                Console.Warning("Startup","Failed to load salt from opticraft.salt")
        else:
            #Save this salt to disk.
            try:
                saltHandle = open("opticraft.salt","w")
                saltHandle.write(self.Salt)
                saltHandle.close()
            except IOError:
                Console.Warning("Startup","Failed to save salt to opticraft.salt")

        self.Name = self.ConfigValues.GetValue("server","Name","An opticraft server")
        self.Motd = self.ConfigValues.GetValue("server","Motd","Powered by opticraft!")
        self.MaxClients = int(self.ConfigValues.GetValue("server","Max","32"))
        self.Public = self.ConfigValues.GetValue("server","Public","True")
        self.DumpStats = int(self.ConfigValues.GetValue("server","DumpStats","0"))
        self.LanMode = bool(int(self.ConfigValues.GetValue("server","LanMode","0")))
        self.SendBufferLimit = int(self.ConfigValues.GetValue("server","SendBufferLimit","4194304")) #4MB
        self.IdlePlayerLimit = int(self.ConfigValues.GetValue("server","IdleLimit","3600"))
        self.InstantClose = int(self.ConfigValues.GetValue("server","InstantClose","0"))
        self.AllowCaps = bool(int(self.ConfigValues.GetValue("server","AllowCaps","0")))
        self.MinCapsLength = int(self.ConfigValues.GetValue("server","MinLength","10"))
        self.FloodPeriod = int(self.ConfigValues.GetValue("server","FloodPeriod","5"))
        self.MaxConnectionsPerIP = int(self.ConfigValues.GetValue("server","MaxConnections","6"))
        self.LowLatencyMode = int(self.ConfigValues.GetValue("server", "LowLatencyMode", "0"))
        self.BlockChangeCount = int(self.ConfigValues.GetValue("server","BlockChangeCount","45"))
        self.BlockChangePeriod = int(self.ConfigValues.GetValue("server", "BlockChangePeriod", "5"))
        self.IPCount = dict()
        self.FloodMessageLimit = int(self.ConfigValues.GetValue("server","FloodCount","6"))
        self.LastIdleCheck = time.time()
        self.IdleCheckPeriod = 60
        self.EnableBlockLogs = int(self.ConfigValues.GetValue("worlds","EnableBlockHistory",1))
        self.WorldTimeout = int(self.ConfigValues.GetValue("worlds","IdleTimeout","300"))
        self.PeriodicAnnounceFrequency = int(self.ConfigValues.GetValue("server","PeriodicAnnounceFrequency","0"))
        self.LogCommands = bool(int(self.ConfigValues.GetValue("logs","CommandLogs","1")))
        self.LogChat = bool(int(self.ConfigValues.GetValue("logs","ChatLogs ","1")))
        self.EnableIRC = bool(int(self.ConfigValues.GetValue("irc","EnableIRC","0")))
        self.IRCServer = self.ConfigValues.GetValue("irc","Server","irc.esper.net")
        self.IRCPort = int(self.ConfigValues.GetValue("irc","Port","6667"))
        self.IRCChannel = self.ConfigValues.GetValue("irc","Channel","#a")
        self.IRCNick = self.ConfigValues.GetValue("irc","Nickname","Optibot")
        self.IRCGameToIRC = bool(int(self.ConfigValues.GetValue("irc","GameChatRelay","0")))
        self.IRCIRCToGame = bool(int(self.ConfigValues.GetValue("irc","IrcChatRelay","0")))
        self.IRCIdentificationMessage = self.ConfigValues.GetValue("irc","IdentifyCommand","NickServ identify")
        if self.EnableIRC:
            self.IRCInterface = RelayBot(self.IRCNick,"Opticraft","Opticraft",self)
        self.RankedPlayers = dict()
        self.RankNames = list() #Names of all ranks
        self.RankLevels = dict() #Lowercase name of rank -> Rank level (int)
        self.RankDescriptions = dict() #Lowercase name of rank -> Short description of rank
        self.RankColours = dict() #Lowercase name of rank -> 2 Characters used for colour prefix
        self._ExampleRanks = str()
        self.LoadRanks()
        self.LoadPlayerRanks()
        self.AdmincreteRank = self.ConfigValues.GetValue("server","AdmincreteRank",'operator')
        if self.IsValidRank(self.AdmincreteRank) == False:
            Console.Warning("Startup","Admincreterank refers to an unknown rank %s" %self.AdmincreteRank)
            self.AdmincreteRank = 'builder'
        self.HeartBeatControl = HeartBeatController(self)
        self.SockManager = SocketManager(self)
        self.PlayerSet = set() #All players logged into the server
        self.PlayerNames = dict() #All logged in players names.
        self.AuthPlayers = set() #Players without a world (Logging in)
        self.PlayersPendingRemoval = set() #Players to remove from our set at the end of a cycle.
        self.PlayerIDs = range(self.MaxClients)
        self.ShuttingDown = False
        self.LastCpuCheck = 0
        self.InitialCpuTimes = os.times()
        self.LastCpuTimes = 0
        self.LoadResults = Queue.Queue()
        self.PlayerDBThread  = PlayerDbThread(self)
        self.PlayerDBConnection = dbapi.connect("Player.db")
        self.PlayerDBConnection.text_factory = str
        self.PlayerDBConnection.row_factory = dbapi.Row
        self.PlayerDBCursor = self.PlayerDBConnection.cursor()
        self.CurrentCpuTimes = 0
        reversed(self.PlayerIDs)
        self.SocketToPlayer = dict()
        self.Running = False
        self.ActiveWorlds = list() #A list of worlds currently running.
        self.IdleWorlds = list() #Worlds which we know exist as .save data, but aren't loaded.
        self.WorldRankCache = dict() #Dictionary of Name:Rank values for all the worlds
        self.WorldHideCache = dict() #Dictionary of Name:Hidden values for all the worlds
        self.BannedUsers = dict() #Dictionary of Username:expiry (in time)
        self.BannedIPs = dict() #dictionary of IP:expiry (in time)
        self.PeriodicNotices = list() #A list of strings of message we will periodicly announce
        if self.PeriodicAnnounceFrequency != 0:
            self.LoadAnnouncements()
        self.LastAnnounce = 0
        self.NumPlayers = 0
        self.PeakPlayers = 0
        self.Now = time.time()
        self.CommandHandle = CommandHandler(self)
        #Override default command permissions from the config file
        self.LoadCommandOverrides()
        if self.LogChat:
            try:
                self.ChatLogHandle = open("Logs/chat.log","a")
                self.PMLogHandle = open("Logs/pm.log","a")
            except IOError:
                self.ChatLogHandle = self.PMLogHandle = None
        else:
            self.ChatLogHandle = self.PMLogHandle = None
        #Load up banned usernames.
        if os.path.isfile("banned.txt"):
            try:
                fHandle = open("banned.txt","r")
                for line in fHandle:
                    Tokens = line.split(":")
                    self.BannedUsers[Tokens[0]] = int(Tokens[1])
                fHandle.close()
            except:
                Console.Error("ServerControl","Failed to load banned.txt!")
        #Load up banned IP's
        if os.path.isfile("banned-ip.txt"):
            try:
                fHandle = open("banned-ip.txt","r")
                for line in fHandle:
                    Tokens = line.split(":")
                    self.BannedIPs[Tokens[0]] = int(Tokens[1])
                fHandle.close()
            except:
                Console.Error("ServerControl", "Failed to load banned-ip.txt!")

        self.Rules = list()
        self.LoadRules()
        self.Greeting = list()
        self.LoadGreeting()
        self.Zones = list()
        self.LoadZones()
        Worlds = os.listdir("Worlds")
        for FileName in Worlds:
            if len(FileName) < 5:
                continue
            if FileName[-5:] != ".save":
                continue
            WorldName = FileName[:-5]
            self.WorldRankCache[WorldName.lower()], self.WorldHideCache[WorldName.lower()] = World.GetCacheValues(WorldName,self)
            if WorldName == self.ConfigValues.GetValue("worlds","DefaultName","Main"):
                #The default world is always loaded
                continue
            self.IdleWorlds.append(WorldName)
        self.ActiveWorlds.append(World(self,self.ConfigValues.GetValue("worlds","DefaultName","Main")))
        self.ActiveWorlds[0].SetIdleTimeout(0) #0 - never becomes idle
        #write out pid to opticraft.pid
        try:
            pidHandle = open("opticraft.pid","w")
            pidHandle.write(str(os.getpid()))
            pidHandle.close()
        except IOError:
            Console.Warning("Startup","Failed to write process id to opticraft.pid")

        self.LastKeepAlive = -1

    def LoadWorld(self,Name):
        '''Name will be a valid world name (case sensitive)'''
        try:
            pWorld = World(self,Name)
        except WorldLoadFailedException:
            return False
        self.ActiveWorlds.append(pWorld)
        self.IdleWorlds.remove(Name)
        pWorld.SetIdleTimeout(self.WorldTimeout)
        return pWorld

    def UnloadWorld(self,pWorld):
        self.ActiveWorlds.remove(pWorld)
        self.IdleWorlds.append(pWorld.Name)
        Console.Out("World","World %s has been unloaded." %pWorld.Name)
    def GetWorlds(self):
        '''Returns a tuple of lists. First element is a list of active World pointers
        ...Second element is a list of inactive World names'''
        ActiveWorlds = [pWorld for pWorld in self.ActiveWorlds]
        InactiveWorlds = [Name for Name in self.IdleWorlds]
        return (ActiveWorlds,InactiveWorlds)
    def GetActiveWorld(self,WorldName):
        '''Returns a pointer to an active world with name WorldName'''
        WorldName = WorldName.lower()
        for pWorld in self.ActiveWorlds:
            if pWorld.Name.lower() == WorldName:
                return pWorld
        return None
    def WorldExists(self,Name):
        Name = Name.lower()
        for pWorld in self.ActiveWorlds:
            if pWorld.Name.lower() == Name:
                return True
        for WorldName in self.IdleWorlds:
            if WorldName.lower() == Name:
                return True
        return False
    def SetDefaultWorld(self,pWorld):
        self.ActiveWorlds.remove(pWorld)
        self.ActiveWorlds[0].SetIdleTimeout(self.WorldTimeout)
        self.ActiveWorlds.insert(0,pWorld)
        pWorld.SetIdleTimeout(0)
        self.ConfigValues.set("worlds","DefaultName",pWorld.Name)
        try:
            fHandle = open("opticraft.ini","w")
            self.ConfigValues.write(fHandle)
            fHandle.close()
        except:
            pass
    def IsWorldHidden(self,Name):
        return self.WorldHideCache[Name.lower()]
    def SetWorldHidden(self,Name,Value):
        self.WorldHideCache[Name.lower()] = Value
    def GetWorldRank(self,Name):
        return self.WorldRankCache[Name.lower()]
    def SetWorldRank(self,Name,Rank):
        self.WorldRankCache[Name.lower()] = Rank
    def LoadCommandOverrides(self):
        Items = self.ConfigValues.items("commandoverrides")
        Console.Debug("Startup","Loading command overrides")
        for Item in Items:
            Command = Item[0]
            Permission = Item[1]
            if self.IsValidRank(Permission):
                if self.CommandHandle.OverrideCommandPermissions(Command, Permission) == False:
                    Console.Warning("Startup","Unable to override command %s as it does not exist!" %Command)
                else:
                    Console.Debug("Startup","Successfully set command %s's permission to %s" %(Command,Permission))
            else:
                Console.Warning("Startup","Unable to override command %s to %s as the rank doesn't exist!" %(Command,Permission))

    def LoadRanks(self):
        Console.Debug("Startup","Loading ranks")
        #Add defaults incase some newby trys to remove a rank.
        self.RankLevels["guest"] = 10
        self.RankLevels["builder"] = 20
        self.RankLevels["operator"] = 50
        self.RankLevels["admin"] = 100
        self.RankLevels["owner"] = 1000
        self.RankColours["guest"] = "&f"
        self.RankColours["builder"] = "&a"
        self.RankColours["operator"] = "&b"
        self.RankColours["admin"] = "&9"
        self.RankColours["owner"] = "&c"

        Items = self.ConfigValues.items("ranks")
        for Item in Items:
            self.RankNames.append(Item[0].capitalize())
            self.RankLevels[Item[0].lower()] = int(Item[1])
        Items = self.ConfigValues.items("rankcolours")
        for Item in Items:
            self.RankColours[Item[0].lower()] = Item[1]
        Items = self.ConfigValues.items("rankdescriptions")
        for Item in Items:
            self.RankDescriptions[Item[0].lower()] = Item[1]

        RankNames = ["Spectator","Guest","Builder","Operator","Admin","Owner"]
        
        ToAdd = list()
        for Rank in RankNames:
            if Rank not in self.RankNames:
                ToAdd.append(Rank)
        while len(ToAdd) > 0:
            self.RankNames.append(ToAdd.pop())
        self.RankNames.sort(key = lambda rank: self.RankLevels[rank.lower()])
        ExampleRanks = list()
        for Rank in self.RankNames:
            if Rank.lower() in self.RankDescriptions.iterkeys():
                ExampleRanks.append(Rank)
        self._ExampleRanks = ', '.join(ExampleRanks)

    def LoadPlayerRanks(self):
        try:
            Items = self.RankStore.items("ranks")
        except:
            return
        IsDirty = False
        for Username,Rank in Items:
            if Rank.capitalize() not in self.RankNames:
                IsDirty = True
                Console.Warning("Ranks","Player %s has an unknown rank, '%s'" %(Username.capitalize(),Rank.capitalize()))
                self.RankStore.remove_option("ranks",Username)
                continue
            self.RankedPlayers[Username.lower()] = Rank.lower()
        if IsDirty:
            try:
                fHandle = open("ranks.ini","w")
                self.RankStore.write(fHandle)
                fHandle.close()
            except:
                return

    def LoadZones(self):
        '''Loads up all the Zone objects into memory'''
        Files = os.listdir("Zones")
        for File in Files:
            if len(File) < 4:
                continue
            if File[-3:] != "ini":
                continue
            pZone = Zone(File,self)
            self.Zones.append(pZone)
    def AddZone(self,pZone):
        self.Zones.append(pZone)
    def AddWorld(self,WorldName):
        self.IdleWorlds.append(WorldName)
        self.WorldRankCache[WorldName.lower()], self.WorldHideCache[WorldName.lower()] = World.GetCacheValues(WorldName,self)
    def InsertZones(self,pWorld):
        '''Gives the world all its zones to worry about'''
        for pZone in self.Zones:
            if pZone.Map == pWorld.Name:
                pWorld.InsertZone(pZone)
    def GetZones(self):
        return self.Zones
    def DeleteZone(self,pZone):
        '''if pZone is a new zone it wont be in our list'''
        if pZone in self.Zones:
            self.Zones.remove(pZone)

    def LoadAnnouncements(self):
        Items = self.ConfigValues.items("announcements")
        Items.sort(key= lambda item: item[0])
        if len(Items) == 0:
            self.PeriodicAnnounceFrequency = 0
            return
        for Item in Items:
            self.PeriodicNotices.append(Item[1])
    def LoadRules(self):
        Items = self.ConfigValues.items("rules")
        Items.sort(key= lambda item: item[0])
        for Item in Items:
            self.Rules.append(Item[1])
    def LoadGreeting(self):
        Items = self.ConfigValues.items("greeting")
        Items.sort(key= lambda item: item[0])
        for Item in Items:
            self.Greeting.append(Item[1])
    def GetCurrentCpuUsage(self):
        '''Returns the last 60 seconds of cpu usage in a tuple of (Total,user,system)'''
        if self.LastCpuTimes == 0:
            return(0.0,0.0,0.0)
        User = (self.CurrentCpuTimes[0]-self.LastCpuTimes[0])/60.0 *100.0
        System = (self.CurrentCpuTimes[1]-self.LastCpuTimes[1])/60.0 *100.0
        return (User+System,User,System)
    def GetTotalCpuUsage(self):
        '''Returns the average cpu usage since startup in a tuple of (Total,user,system)'''
        User = (os.times()[0]-self.InitialCpuTimes[0])/(self.Now - self.StartTime) *100.0
        System = (os.times()[1]-self.InitialCpuTimes[1])/(self.Now - self.StartTime) *100.0
        return (User+System,User,System)

    def GetRank(self,Username):
        return self.RankedPlayers.get(Username.lower(),'guest')
    def GetRankLevel(self,Rank):
        return self.RankLevels[Rank.lower()]
    def IsValidRank(self,Rank):
        return Rank.lower() in self.RankLevels
    def GetExampleRanks(self):
        '''This returns a string of Ranks with valid descriptions'''
        return self._ExampleRanks

    def SetRank(self,Initiator,Username,Rank):
        if Rank != 'guest':
            self.RankedPlayers[Username.lower()] = Rank.lower()
            self.RankStore.set("ranks",Username,Rank)
            pPlayer = self.GetPlayerFromName(Username)
            if pPlayer != None:
                pPlayer.SetRank(Rank)
                pPlayer.SetRankedBy(Initiator.GetName())
                pPlayer.SendMessage("&aYour rank has been changed to %s!" %Rank.capitalize())
        else:
            if Username.lower() in self.RankedPlayers:
                del self.RankedPlayers[Username.lower()]
                self.RankStore.remove_option("ranks",Username)
                pPlayer = self.GetPlayerFromName(Username)
                if pPlayer != None:
                    pPlayer.SetRank('guest')
                    pPlayer.SetRankedBy(Initiator.GetName())
                    pPlayer.SendMessage("&aYour rank has been changed to %s!" %Rank.capitalize())
            else:
                return
        try:
            fHandle = open("ranks.ini","w")
            self.RankStore.write(fHandle)
            fHandle.close()
        except:
            return
        self.PlayerDBThread.Tasks.put(["EXECUTE","Update Players set RankedBy = ? where Username = ?",(Initiator.GetName(),Username.lower())])
    def HandleKill(self,SignalNumber,Frame):
        raise SigkillException()
    def Run(self):
        '''Main Thread from the application. Runs The sockets and worlds'''
        self.Running = True
        #Start the heartbeatcontrol thread.
        self.HeartBeatControl.start()
        if self.EnableIRC:
            try:
                self.IRCInterface.Connect()
            except:
                pass

        if platform.system() == 'Linux':
            signal.signal(signal.SIGTERM,self.HandleKill)
        self.PlayerDBThread.start()
        Console.Out("Startup","Startup procedure completed in %.0fms" %((time.time() -self.StartTime)*1000))
        Console.Out("Server","Press Ctrl-C at any time to shutdown the sever safely.")
        while self.Running == True:
            self.Now = time.time()
            self.SockManager.Run()
            #Remove any players which need to be deleted.
            while len(self.PlayersPendingRemoval) > 0:
                self._RemovePlayer(self.PlayersPendingRemoval.pop())
            ToRemove = list()
            for pPlayer in self.AuthPlayers:
                pPlayer.ProcessPackets()
                if pPlayer.IsAuthenticated():
                    ToRemove.append(pPlayer)
            #Remove Authenitcating players from our duty
            while len(ToRemove) > 0:
                pPlayer = ToRemove.pop()
                self.AuthPlayers.remove(pPlayer)
                #Put the player into our default world if they are identified
                self.SendJoinMessage('&e%s has connected. Joined map %s%s' %(pPlayer.GetName(),
                self.RankColours[self.ActiveWorlds[0].GetMinRank()],self.ActiveWorlds[0].Name))
                self.ActiveWorlds[0].AddPlayer(pPlayer)
                for Line in self.Greeting:
                    pPlayer.SendMessage(Line)
                    
            for pWorld in self.ActiveWorlds:
                pWorld.Run()
                
            if self.LastKeepAlive + 1 < self.Now:
                self.LastKeepAlive = self.Now
                Packet = OptiCraftPacket(SMSG_KEEPALIVE)
                #Send a SMSG_KEEPALIVE packet to all our clients across all worlds.
                for pPlayer in self.PlayerSet:
                    pPlayer.SendPacket(Packet)
            if self.LastCpuCheck + 60 < self.Now:
                self.LastCpuTimes = self.CurrentCpuTimes
                self.CurrentCpuTimes = os.times()
                self.LastCpuCheck = self.Now

            if self.PeriodicAnnounceFrequency:
                if self.LastAnnounce + self.PeriodicAnnounceFrequency < self.Now:
                    Message = self.PeriodicNotices[random.randint(0,len(self.PeriodicNotices)-1)]
                    self.SendMessageToAll(Message)
                    self.LastAnnounce = self.Now

            #Run the IRC Bot if enabled
            if self.EnableIRC:
                asyncore.loop(count=1,timeout=0.001)
            #Remove idle players
            if self.IdlePlayerLimit != 0:
                if self.LastIdleCheck + self.IdleCheckPeriod < self.Now:
                    self.RemoveIdlePlayers()
                    self.LastIdleCheck = self.Now
            #Check for SQL Results from the PlayerDBThread
            while True:
                try:
                    Result = self.LoadResults.get_nowait()
                except Queue.Empty:
                    break
                #Got a result.
                Username = Result[0]
                Rows = Result[1]
                pPlayer = self.GetPlayerFromName(Username)
                if pPlayer != None:
                    pPlayer.LoadData(Rows)

            SleepTime = 0.05 - (time.time() - self.Now)
            if 0 < SleepTime:
                time.sleep(SleepTime)
    def Shutdown(self,Crash):
        '''Starts shutting down the server. If crash is true it only saves what is needed'''
        self.ShuttingDown = True
        self.HeartBeatControl.Running = False
        self.SockManager.Terminate(True)
        for pWorld in self.ActiveWorlds:
            pWorld.Shutdown(True)
        self.Running = False
        ToRemove = list(self.PlayerSet)
        for pPlayer in ToRemove:
            self._RemovePlayer(pPlayer)
        self.PlayerDBThread.Tasks.put(["SHUTDOWN"])
        if self.EnableIRC:
            self.IRCInterface.OnShutdown(Crash)
            asyncore.loop(timeout=0.01,count=1)
    def GetName(self):
        return self.Name
    def GetMotd(self):
        return self.Motd
    def GetUptimeStr(self):
        return ElapsedTime((int(self.Now)) - int(self.StartTime))

    def GetPlayerFromName(self,Username):
        '''Returns a player pointer if the user is logged else.
        ...Otherwise returns none if player is not on'''
        return self.PlayerNames.get(Username.lower(),None)

    def IsBanned(self,pPlayer):
        '''Checks if a player is banned. Also erases any expired bans!'''
        if self.BannedUsers.has_key(pPlayer.GetName().lower()):
            ExpiryTime = self.BannedUsers[pPlayer.GetName().lower()]
            if ExpiryTime == 0 or ExpiryTime > self.Now:
                return True
            else:
                del self.BannedUsers[pPlayer.GetName().lower()]
                self.FlushBans()
                return False
        elif self.BannedIPs.has_key(pPlayer.GetIP()):
            ExpiryTime = self.BannedIPs[pPlayer.GetIP()]
            if ExpiryTime == 0 or ExpiryTime > self.Now:
                return True
            else:
                del self.BannedIPs[pPlayer.GetIP()]
                self.FlushIPBans()
                return False
        else:
            return False

    def FlushBans(self):
        try:
            fHandle = open("banned.txt","w")
            for key in self.BannedUsers:
                fHandle.write(key + ":" + str(self.BannedUsers[key]) + "\r\n")
            fHandle.close()
        except:
            pass
    def FlushIPBans(self):
        try:
            fHandle = open("banned-ip.txt","w")
            for key in self.BannedIPs:
                fHandle.write(key + ":" + str(self.BannedIPs[key]) + "\r\n")
            fHandle.close()
        except:
            pass
        
    def AddBan(self,Initiator,Username,Expiry):
        self.BannedUsers[Username.lower()] = Expiry
        self.FlushBans()
        pPlayer = self.GetPlayerFromName(Username)
        if pPlayer != None:
            pPlayer.IncreaseKickCount()
            pPlayer.SetBannedBy(Initiator.GetName())
            pPlayer.Disconnect("You are banned from this server")
            return True
        else:
            self.PlayerDBThread.Tasks.put(["EXECUTE","Update Players set BannedBy = ? where Username = ?",(Initiator.GetName(),Username.lower())])
            return False
    def AddIPBan(self,Admin,IP,Expiry):
        self.BannedIPs[IP] = Expiry
        self.FlushIPBans()
        for pPlayer in self.PlayerSet:
            if pPlayer.GetIP() == IP:
                pPlayer.IncreaseKickCount()
                pPlayer.Disconnect("You are ip-banned from this server")
                self.SendNotice("%s has been ip-banned by %s" %(pPlayer.GetName(),Admin.GetName()))
    def Unban(self,Username):
        if self.BannedUsers.has_key(Username.lower()) == True:
            del self.BannedUsers[Username.lower()]
            self.FlushBans()
            self.PlayerDBThread.Tasks.put(["EXECUTE","Update Players set BannedBy = '' where Username = ?",(Username.lower(),)])
            return True
        else:
            return False
    def UnbanIP(self,IP):
        if self.BannedIPs.has_key(IP) == True:
            del self.BannedIPs[IP]
            self.FlushIPBans()
            return True
        else:
            return False

    def Kick(self,Operator,Username,Reason):
        pPlayer = self.GetPlayerFromName(Username)
        if pPlayer != None:
            self.SendNotice("%s was kicked by %s. Reason: %s" %(Username,Operator.GetName(),Reason))
            pPlayer.IncreaseKickCount()
            pPlayer.Disconnect("You were kicked by %s. Reason: %s" %(Operator.GetName(),Reason))
            return True
        return False
    def RemoveIdlePlayers(self):
        for pPlayer in self.PlayerSet:
            if pPlayer.GetLastAction() + self.IdlePlayerLimit < self.Now:
                if pPlayer.GetRankLevel() <= self.RankLevels['guest']:
                    pPlayer.Disconnect("You were kicked for being idle")
                    if pPlayer.IsAuthenticated():
                        self.SendMessageToAll("&e%s has been kicked for being idle" %pPlayer.GetName())

    def AttemptAddPlayer(self,pPlayer):
        if len(self.PlayerIDs) == 0:
            return False, "Server is full. Try again later."
        else:
            ConnectionCount = self.IPCount.get(pPlayer.GetIP(),0) + 1
            if self.MaxConnectionsPerIP and ConnectionCount > self.MaxConnectionsPerIP:
                return False, "Too many connections from your ip-address"
            else:
                self.IPCount[pPlayer.GetIP()] = ConnectionCount
            self.SocketToPlayer[pPlayer.GetSocket()] = pPlayer
            self.PlayerSet.add(pPlayer)
            self.AuthPlayers.add(pPlayer)
            pPlayer.SetId(self.PlayerIDs.pop())
            self.HeartBeatControl.IncreaseClients()
            self.NumPlayers += 1
            if self.NumPlayers > self.PeakPlayers:
                self.PeakPlayers = self.NumPlayers
            return True,''

    def RemovePlayer(self,pPlayer):
        self.PlayersPendingRemoval.add(pPlayer)
        
    def _RemovePlayer(self,pPlayer):
        '''Internally removes a player
        Note:Player poiner may not neccessarily exist in our storage'''
        Console.Out("Player","Player %s has left the server" %pPlayer.GetName())
        if pPlayer in self.PlayerSet:
            self.PlayerSet.remove(pPlayer)
            self.PlayerIDs.append(pPlayer.GetId()) #Make the Id avaliable for use again.
            del self.SocketToPlayer[pPlayer.GetSocket()]
            self.IPCount[pPlayer.GetIP()] -= 1
        if pPlayer in self.AuthPlayers:
            self.AuthPlayers.remove(pPlayer)
        else:
            self.SendJoinMessage("&e%s has left the server" %pPlayer.GetName())
            if self.GetPlayerFromName(pPlayer.GetName()) != None:
                del self.PlayerNames[pPlayer.GetName().lower()]
            if self.EnableIRC:
                self.IRCInterface.HandleLogout(pPlayer.GetName())

        if pPlayer.GetWorld() != None:
            pPlayer.GetWorld().RemovePlayer(pPlayer)
        if pPlayer.GetNewWorld() != None:
            pPlayer.GetNewWorld().JoiningPlayers.remove(pPlayer)
            pPlayer.SetNewWorld(None)
        if pPlayer.IsDataLoaded():
            #Update the played time.
            pPlayer.UpdatePlayedTime()
            self.PlayerDBThread.Tasks.put(["SAVE_PLAYER",pPlayer])
        pPlayer.SetWorld(None)
        self.HeartBeatControl.DecreaseClients()
        self.NumPlayers -= 1

    def GetPlayerFromSocket(self,Socket):
        return self.SocketToPlayer[Socket]
    def SendNotice(self,Message):
        Packet = OptiCraftPacket(SMSG_MESSAGE)
        Packet.WriteByte(0xFF)
        Packet.WriteString(Message[:64])
        self.SendPacketToAll(Packet)
    def SendJoinMessage(self,Message):
        Packet = OptiCraftPacket(SMSG_MESSAGE)
        Packet.WriteByte(0)
        Packet.WriteString(Message[:64])
        for pPlayer in self.PlayerSet:
            if pPlayer.GetJoinNotifications():
                pPlayer.SendPacket(Packet)
    def SendMessageToAll(self,Message):
        Packet = OptiCraftPacket(SMSG_MESSAGE)
        Packet.WriteByte(0)
        Packet.WriteString(Message[:64])
        self.SendPacketToAll(Packet)
    def SendChatMessage(self,From,Message,NewLine = ">",NormalStart = True):
        Words = Message.split()
        if NormalStart:
            OutStr = '%s:&f' %From
        else:
            OutStr = '%s' %From
        for Word in Words:
            if len(Word) >= 60:
                return #Prevent crazy bugs due to this crappy string system

            if len(OutStr) + len(Words) > 63:
                self.SendMessageToAll(OutStr)
                OutStr = NewLine
            OutStr = '%s %s' %(OutStr,Word)
        self.SendMessageToAll(OutStr)

    def SendPacketToAll(self,Packet):
        '''Distributes a packet to all clients on a map
            *ANY CHANGES TO THIS FUNCTION NEED TO BE MADE TO Player::SendPacket!'''
        Data = Packet.GetOutData()
        for pPlayer in self.PlayerSet:
           pPlayer.OutBuffer.write(Data)

    def SaveAllWorlds(self):
        '''This will need to be rewritten come multi-threaded worlds!'''
        for pWorld in self.ActiveWorlds:
            pWorld.Save()
    def BackupAllWorlds(self):
        '''This will need to be rewritten come multi-threaded worlds!'''
        for pWorld in self.ActiveWorlds:
            pWorld.Backup()