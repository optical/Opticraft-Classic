import random
import time
import os
import os.path
import signal
import platform
import asyncore
from heartbeatcontrol import HeartBeatController
from opticraftpacket import OptiCraftPacket
from optisockets import SocketManager
from commandhandler import CommandHandler
from configreader import ConfigReader
from zones import Zone
from world import World
from constants import *
from console import *
from ircrelay import RelayBot
class SigkillException(Exception):
    pass
#This is used for writing to the command line (Console, stdout)
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
        Console.SetLogLevel(int(self.ConfigValues.GetValue("logs","ConsoleLogLevel",LOG_LEVEL_DEBUG)))
        Console.SetFileLogging(bool(int(self.ConfigValues.GetValue("logs","ConsoleFileLogs","0"))))
        Console.SetColour(int(self.ConfigValues.GetValue("server","ConsoleColour","1")))
        Console.Out("Startup","Opticraft is starting up.")
        self.Port = int(self.ConfigValues.GetValue("server","Port","6878"))
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
        self.MaxClients = int(self.ConfigValues.GetValue("server","Max",120))
        self.Public = self.ConfigValues.GetValue("server","Public","True")
        self.DumpStats = int(self.ConfigValues.GetValue("server","DumpStats","0"))
        self.LanMode = bool(int(self.ConfigValues.GetValue("server","LanMode","0")))
        self.SendBufferLimit = int(self.ConfigValues.GetValue("server","SendBufferLimit","4194304")) #4MB
        self.IdlePlayerLimit = int(self.ConfigValues.GetValue("server","IdleLimit","3600"))
        self.LastIdleCheck = time.time()
        self.IdleCheckPeriod = 60
        self.EnableBlockLogs = int(self.ConfigValues.GetValue("worlds","EnableBlockHistory",1))
        self.WorldTimeout = int(self.ConfigValues.GetValue("worlds","IdleTimeout","300"))
        self.PeriodicAnnounceFrequency = int(self.ConfigValues.GetValue("server","PeriodicAnnounceFrequency","0"))
        self.LogCommands = bool(int(self.ConfigValues.GetValue("logs","CommandLogs","1")))
        self.LogChat = bool(int(self.ConfigValues.GetValue("logs","CommandLogs","1")))
        self.EnableIRC = bool(int(self.ConfigValues.GetValue("irc","EnableIRC","0")))
        self.IRCServer = self.ConfigValues.GetValue("irc","Server","irc.esper.net")
        self.IRCPort = int(self.ConfigValues.GetValue("irc","Port","6667"))
        self.IRCChannel = self.ConfigValues.GetValue("irc","Channel","#a")
        self.IRCNick = self.ConfigValues.GetValue("irc","Nickname","Optibot")
        self.IRCGameToIRC =   bool(int(self.ConfigValues.GetValue("irc","GameChatRelay","0")))
        self.IRCIRCToGame =  bool(int(self.ConfigValues.GetValue("irc","IrcChatRelay","0")))
        if self.EnableIRC:
            self.IRCInterface = RelayBot(self.IRCNick,"Opticraft","Opticraft",self)
        self.RankedPlayers = dict()
        self.LoadRanks()
        self.HeartBeatControl = HeartBeatController(self)
        self.SockManager = SocketManager(self)
        self.PlayerSet = set() #All players logged into the server
        self.PlayerNames = dict() #All logged in players names.
        self.AuthPlayers = set() #Players without a world (Logging in)
        self.PlayersPendingRemoval = set() #Players to remove from our set at the end of a cycle.
        self.PlayerIDs = range(self.MaxClients)
        reversed(self.PlayerIDs)
        self.SocketToPlayer = dict()
        self.Running = False
        self.ActiveWorlds = list() #A list of worlds currently running.
        self.IdleWorlds = list() #Worlds which we know exist as .save data, but aren't loaded.
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
        self.Zones = list()
        self.LoadZones()
        Worlds = os.listdir("Worlds")
        for FileName in Worlds:
            if len(FileName) < 5:
                continue
            if FileName[-5:] != ".save":
                continue
            WorldName = FileName[:-5]
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
        pWorld = World(self,Name)
        self.ActiveWorlds.append(pWorld)
        self.IdleWorlds.remove(Name)
        pWorld.SetIdleTimeout(self.WorldTimeout)
        return pWorld

    def UnloadWorld(self,pWorld):
        self.ActiveWorlds.remove(pWorld)
        self.IdleWorlds.append(pWorld.Name)
        Console.Out("World","World %s is being pushed to idle state" %pWorld.Name)
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
    def LoadRanks(self):
        try:
            Items = self.RankStore.items("ranks")
        except:
            return
        for Username,Rank in Items:
            self.RankedPlayers[Username.lower()] = Rank.lower()

    def LoadZones(self):
        '''Loads up all the Zone objects into memory'''
        Files = os.listdir("Zones")
        for File in Files:
            if len(File) < 4:
                continue
            if File[-3:] != "ini":
                continue
            pZone = Zone(File)
            self.Zones.append(pZone)
    def AddZone(self,pZone):
        self.Zones.append(pZone)
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
        if len(Items) == 0:
            self.PeriodicAnnounceFrequency = 0
            return
        for Item in Items:
            self.PeriodicNotices.append(Item[1])
        

    def GetRank(self,Username):
        return self.RankedPlayers.get(Username.lower(),'g')

    def SetRank(self,Username,Rank):
        if Rank != 'g':
            self.RankedPlayers[Username.lower()] = Rank.lower()
            self.RankStore.set("ranks",Username,Rank)
            pPlayer = self.GetPlayerFromName(Username)
            if pPlayer != None:
                pPlayer.SetRank(Rank)
                pPlayer.SendMessage("Your rank has been changed to %s!" %RankToName[Rank])
        else:
            if Username.lower() in self.RankedPlayers:
                del self.RankedPlayers[Username.lower()]
                self.RankStore.remove_option("ranks",Username)
                pPlayer = self.GetPlayerFromName()
                if pPlayer != None:
                    pPlayer.SetRank('g')
                    pPlayer.SendMessage("You no longer have a rank.")
            else:
                return
        try:
            fHandle = open("ranks.ini","w")
            self.RankStore.write(fHandle)
            fHandle.close()
        except:
            return
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

        if platform.system() == 'linux':
            signal.signal(signal.SIGTERM,self.HandleKill)
        Console.Out("Startup","Startup procedure completed in %.0fms" %((time.time() -self.StartTime)*1000))
        while self.Running == True:
            self.Now = time.time()
            self.SockManager.Run()
            ToRemove = list()
            for pPlayer in self.AuthPlayers:
                pPlayer.ProcessPackets()
                if pPlayer.IsIdentified == True:
                    ToRemove.append(pPlayer)

            #Remove Authenitcating players from our duty
            while len(ToRemove) > 0:
                pPlayer = ToRemove.pop()
                self.AuthPlayers.remove(pPlayer)
                #Put the player into our default world
                self.ActiveWorlds[0].AddPlayer(pPlayer)

            for pWorld in self.ActiveWorlds:
                pWorld.Run()

            #Remove any players which need to be deleted.
            while len(self.PlayersPendingRemoval) > 0:
                pPlayer = self.PlayersPendingRemoval.pop()
                self._RemovePlayer(pPlayer)
                
            if self.LastKeepAlive + 1 < self.Now:
                self.LastKeepAlive = self.Now
                Packet = OptiCraftPacket(SMSG_KEEPALIVE)
                #Send a SMSG_KEEPALIVE packet to all our clients across all worlds.
                for pPlayer in self.PlayerSet:
                    pPlayer.SendPacket(Packet)

            if self.PeriodicAnnounceFrequency:
                if self.LastAnnounce + self.PeriodicAnnounceFrequency < self.Now:
                    Message = self.PeriodicNotices[random.randint(0,len(self.PeriodicNotices)-1)]
                    self.SendMessageToAll(Message)
                    self.LastAnnounce = self.Now

            #Run the IRC Bot if enabled
            if self.EnableIRC:
                asyncore.loop(count=1,timeout=0.005)
            #Remove idle players
            if self.IdlePlayerLimit != 0:
                if self.LastIdleCheck + self.IdleCheckPeriod < self.Now:
                    self.RemoveIdlePlayers()
                    self.LastIdleCheck = self.Now
            SleepTime = 0.02 - (time.time() - self.Now)
            if 0 < SleepTime:
                time.sleep(0.02)
    def Shutdown(self,Crash):
        '''Starts shutting down the server. If crash is true it only saves what is needed'''
        self.HeartBeatControl.Running = False
        self.SockManager.Terminate(True)
        for pWorld in self.ActiveWorlds:
            pWorld.Shutdown(True)
        self.Running = False

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
        
    def AddBan(self,Username,Expiry):
        self.BannedUsers[Username.lower()] = Expiry
        self.FlushBans()
        pPlayer = self.GetPlayerFromName(Username)
        if pPlayer != None:
            pPlayer.Disconnect("You are banned from this server")
            return True
        return False
    def AddIPBan(self,Admin,IP,Expiry):
        self.BannedIPs[IP] = Expiry
        self.FlushIPBans()
        for pPlayer in self.PlayerSet:
            if pPlayer.GetIP() == IP:
                pPlayer.Disconnect("You are ip-banned from this server")
                self.SendNotice("%s has been ip-banned by %s" %(pPlayer.GetName(),Admin.GetName()))
                
    def Unban(self,Username):
        if self.BannedUsers.has_key(Username.lower()) == True:
            del self.BannedUsers[Username.lower()]
            self.FlushBans()
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
            pPlayer.Disconnect("You were kicked by %s. Reason: %s" %(Operator.GetName(),Reason))
            return True
        return False
    def RemoveIdlePlayers(self):
        for pPlayer in self.PlayerSet:
            if pPlayer.GetLastAction() + self.IdlePlayerLimit < self.Now:
                if RankToLevel['g'] >= RankToLevel[pPlayer.GetRank()]:
                    pPlayer.Disconnect("You were kicked for being idle")
                    self.SendMessageToAll("%s&e has been kicked for being idle" %pPlayer.GetColouredName())

    def AttemptAddPlayer(self,pPlayer):
        if len(self.PlayerIDs) == 0:
            return False
        else:
            self.SocketToPlayer[pPlayer.GetSocket()] = pPlayer
            self.PlayerSet.add(pPlayer)
            self.AuthPlayers.add(pPlayer)
            pPlayer.SetId(self.PlayerIDs.pop())
            self.HeartBeatControl.IncreaseClients()
            self.NumPlayers += 1
            if self.NumPlayers > self.PeakPlayers:
                self.PeakPlayers = self.NumPlayers

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
        if pPlayer in self.AuthPlayers:
            self.AuthPlayers.remove(pPlayer)
        else:
            self.SendNotice("%s has left the server" %pPlayer.GetName())
            if self.GetPlayerFromName(pPlayer.GetName()) != None:
                del self.PlayerNames[pPlayer.GetName().lower()]
            if self.EnableIRC:
                self.IRCInterface.HandleLogout(pPlayer.GetName())


        if pPlayer.GetWorld() != None:
            pPlayer.GetWorld().RemovePlayer(pPlayer)
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
    def SendMessageToAll(self,Message):
        Packet = OptiCraftPacket(SMSG_MESSAGE)
        Packet.WriteByte(0)
        Packet.WriteString(Message[:64])
        self.SendPacketToAll(Packet)
    def SendChatMessage(self,From,Message):
        Words = Message.split()
        OutStr = '%s:&f' %From
        for Word in Words:
            if len(Word) >= 60:
                return #Prevent crazy bugs due to this crappy string system

            if len(OutStr) + len(Words) > 63:
                self.SendMessageToAll(OutStr)
                OutStr = ">"
            OutStr = '%s %s' %(OutStr,Word)
        self.SendMessageToAll(OutStr)

    def SendPacketToAll(self,Packet):
        for pPlayer in self.PlayerSet:
            pPlayer.SendPacket(Packet)

    def SaveAllWorlds(self):
        '''This will need to be rewritten come multi-threaded worlds!'''
        for pWorld in self.ActiveWorlds:
            pWorld.Save()
    def BackupAllWorlds(self):
        '''This will need to be rewritten come multi-threaded worlds!'''
        for pWorld in self.ActiveWorlds:
            pWorld.Backup()