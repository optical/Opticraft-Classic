import random
# To change this template, choose Tools | Templates
# and open the template in the editor.
import time
import os
import os.path
from heartbeatcontrol import HeartBeatController
from opticraftpacket import OptiCraftPacket
from optisockets import SocketManager
from commandhandler import CommandHandler
from configreader import ConfigReader
from zones import Zone
from world import World
from constants import *
class ServerController(object):
    def __init__(self):
        self.ConfigValues = ConfigReader()
        self.ConfigValues.read("opticraft.cfg")
        self.Host = self.ConfigValues.GetValue("server","ListenInterface",'0.0.0.0')
        if self.Host == '0.0.0.0':
            self.Host = ''

        self.StartTime = int(time.time())
        self.Port = int(self.ConfigValues.GetValue("server","Port","6878"))
        self.Salt = self.ConfigValues.GetValue("server","ForcedSalt",str(random.randint(1,0xFFFFFFFF-1)))
        self.Name = self.ConfigValues.GetValue("server","Name","An opticraft server")
        self.Motd = self.ConfigValues.GetValue("server","Motd","Powered by opticraft!")
        self.MaxClients = int(self.ConfigValues.GetValue("server","Max",120))
        self.Public = self.ConfigValues.GetValue("server","Public","True")
        self.WorldTimeout = int(self.ConfigValues.GetValue("worlds","IdleTimeout","300"))
        self.RankedPlayers = dict()
        self.LoadRanks()
        self.HeartBeatControl = HeartBeatController(self)
        self.SockManager = SocketManager(self)
        self.PlayerSet = set() #All players logged into the server
        self.PlayerNames = dict() #All logged in players names.
        self.AuthPlayers = set() #Players without a world (Logging in)
        self.PlayersPendingRemoval = list() #Players to remove from our set at the end of a cycle.
        self.PlayerIDs = range(self.MaxClients)
        reversed(self.PlayerIDs)
        self.SocketToPlayer = dict()
        self.Running = False
        self.ActiveWorlds = list() #A list of worlds currently running.
        self.IdleWorlds = list() #Worlds which we know exist as .save data, but aren't loaded.
        self.CommandHandle = CommandHandler(self)
        self.BannedUsers = dict() #Dictionary of Username:expiry (in ctime)
        self.NumPlayers = 0
        self.PeakPlayers = 0
        #Load up banned usernames.
        if os.path.isfile("banned.txt"):
            try:
                fHandle = open("banned.txt","r")
                for line in fHandle:
                    Tokens = line.split(":")
                    self.BannedUsers[Tokens[0]] = int(Tokens[1])
                fHandle.close()
            except:
                print "Failed to load banned users.txt!"

        #Check to see we have required directory's
        if os.path.exists("Worlds") == False:
            os.mkdir("Worlds")
        if os.path.exists("Backups") == False:
            os.mkdir("Backups")
        if os.path.exists("Zones") == False:
            os.mkdir("Zones")
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
        print "World %s is being pushed to idle state" %pWorld.Name
    def GetWorlds(self):
        '''Returns a tuple of lists. First element is a list of active World pointers
        ...Second element is a list of inactive World names'''
        ActiveWorlds = [pWorld for pWorld in self.ActiveWorlds]
        InactiveWorlds = [Name for Name in self.IdleWorlds]
        return (ActiveWorlds,InactiveWorlds)

    def WorldExists(self,Name):
        Name = Name.lower()
        for pWorld in self.ActiveWorlds:
            if pWorld.Name.lower() == Name:
                return True
        for WorldName in self.IdleWorlds:
            if WorldName.lower() == Name:
                return True
        return False
    def LoadRanks(self):
        try:
            Items = self.ConfigValues.items("ranks")
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
    def DeleteZone(self,pZone):
        '''if pZone is a new zone it wont be in our list'''
        if pZone in self.Zones:
            self.Zones.remove(pZone)
        

    def GetRank(self,Username):
        return self.RankedPlayers.get(Username.lower(),'')

    def SetRank(self,Username,Rank):
        if Rank != '':
            self.RankedPlayers[Username.lower()] = Rank.lower()
            self.ConfigValues.set("ranks",Username,Rank)
            pPlayer = self.PlayerNames.get(Username,None)
            if pPlayer != None:
                pPlayer.SetRank(Rank)
                pPlayer.SendMessage("Your rank has been changed to %s!" %RankToName[Rank])
        else:
            if Username.lower() in self.RankedPlayers:
                del self.RankedPlayers[Username.lower()]
                self.ConfigValues.remove_option("ranks",Username)
                pPlayer = self.PlayerNames.get(Username.lower(),None)
                if pPlayer != None:
                    pPlayer.SetRank('')
                    pPlayer.SendMessage("You no longer have a rank.")
            else:
                return
        try:
            fHandle = open("opticraft.cfg","w")
            self.ConfigValues.write(fHandle)
            fHandle.close()
        except:
            return
    def run(self):
        '''For now, we will manage everything. Eventually these objects will manage themselves in seperate threads'''
        self.Running = True
        #Start the heartbeatcontrol thread.
        self.HeartBeatControl.start()
        while self.Running == True:
            self.SockManager.run()
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

            #TODO: Threading for worlds - Multi worlds..
            for pWorld in self.ActiveWorlds:
                pWorld.run()

            #Remove any players which need to be deleted.
            while len(self.PlayersPendingRemoval) > 0:
                pPlayer = self.PlayersPendingRemoval.pop()
                self._RemovePlayer(pPlayer)
                
            if self.LastKeepAlive + 1 < time.time():
                self.LastKeepAlive = time.time()
                Packet = OptiCraftPacket(SMSG_KEEPALIVE)
                #Send a SMSG_KEEPALIVE packet to all our clients across all worlds.
                for pPlayer in self.PlayerSet:
                    pPlayer.SendPacket(Packet)
                    
            time.sleep(0.02)
    def Shutdown(self,Crash):
        '''Starts shutting down the server. If crash is true it only saves what is needed'''
        self.SaveAllWorlds()
        self.BackupAllWorlds()
        self.SockManager.Terminate(True)
        self.HeartBeatControl.Running = False
        self.Running = False

    def GetName(self):
        return self.Name
    def GetMotd(self):
        return self.Motd
    def GetUptimeStr(self):
        return ElapsedTime((int(time.time())) - self.StartTime)

    def GetPlayerFromName(self,Username):
        '''Returns a player pointer if the user is logged else.
        ...Otherwise returns none if player is not on'''
        return self.PlayerNames.get(Username.lower(),None)

    def IsBanned(self,pPlayer):
        '''Checks if a player is banned. Also erases any expired bans!'''
        if self.BannedUsers.has_key(pPlayer.GetName().lower()):
            ExpiryTime = self.BannedUsers[pPlayer.GetName().lower()]
            if ExpiryTime == 0 or ExpiryTime > time.time():
                return True
            else:
                del self.BannedUsers[pPlayer.GetName().lower()]
                self.FlushBans()
                return False
        else:
            return False

        
    def AddBan(self,Username,expiry):
        self.BannedUsers[Username.lower()] = expiry
        self.FlushBans()
        pPlayer = self.PlayerNames.get(Username.lower(),None)
        if pPlayer != None:
            pPlayer.Disconnect("You are banned from this server")
            return True
        return False
                
    def Unban(self,Username):
        if self.BannedUsers.has_key(Username.lower()) == True:
            del self.BannedUsers[Username.lower()]
            self.FlushBans()
            return True
        else:
            return False

    def Kick(self,Operator,Username,Reason):
        pPlayer = self.PlayerNames.get(Username.lower(),None)
        if pPlayer != None:
            self.SendNotice("%s was kicked by %s. Reason: %s" %(Username,Operator.GetName(),Reason))
            pPlayer.Disconnect("You were kicked by %s. Reason: %s" %(Operator.GetName(),Reason))
            return True
        return False

    def FlushBans(self):
        try:
            fHandle = open("banned.txt","w")
            for key in self.BannedUsers:
                fHandle.write(key + ":" + str(self.BannedUsers[key]) + "\r\n")
            fHandle.close()
        except:
            pass

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
        self.PlayersPendingRemoval.append(pPlayer)
        
    def _RemovePlayer(self,pPlayer):
        '''Internally removes a player
        Note:Player poiner may not neccessarily exist in our storage'''
        if pPlayer in self.PlayerSet:
            self.PlayerSet.remove(pPlayer)
            self.PlayerIDs.append(pPlayer.GetId()) #Make the Id avaliable for use again.
            del self.SocketToPlayer[pPlayer.GetSocket()]
        if pPlayer in self.AuthPlayers:
            self.AuthPlayers.remove(pPlayer)
        else:
            self.SendNotice("%s has left the server" %pPlayer.GetName())
            
        if pPlayer.GetName().lower() in self.PlayerNames:
            del self.PlayerNames[pPlayer.GetName().lower()]

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