# To change this template, choose Tools | Templates
# and open the template in the editor.
import time
import os
import os.path
from heartbeatcontrol import HeartBeatController
from opticraftpacket import OptiCraftPacket
from optisockets import SocketManager
from world import World
from opcodes import *

class ServerController(object):
    def __init__(self):
        #TODO: Replace these hard-coded values with config file results
        self.Host = ''
        self.Port = 9999
        self.Salt = "SOMESALT"
        self.Name = "OptiCraft Dev Server"
        self.Motd = "-hax"
        self.MaxClients = 100
        self.Public = True
        self.HeartBeatController = HeartBeatController(self)
        self.SockManager = SocketManager(self)
        self.PlayerSet = set() #All players logged into the server
        self.PlayerNames = set() #All logged in players names.
        self.AuthPlayers = set() #Players without a world (Logging in)
        self.PlayersPendingRemoval = list() #Players to remove from our set at the end of a cycle.
        self.PlayerIDs = range(self.MaxClients)
        reversed(self.PlayerIDs)
        self.SocketToPlayer = dict()
        self.Running = False
        self.ActiveWorlds = []
        #Check to see we have required directory's
        if os.path.exists("Worlds") == False:
            os.mkdir("Worlds")
        if os.path.exists("Backups") == False:
            os.mkdir("Backups")
        self.ActiveWorlds.append(World("Default_World",True))
        self.LastKeepAlive = -1

    def run(self):
        '''For now, we will manage everything. Eventually these objects will manage themselves in seperate threads'''
        self.Running = True
        while self.Running == True:
            self.HeartBeatController.run()
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
                    
            time.sleep(0.001)

    def GetName(self):
        return self.Name
    def GetMotd(self):
        return self.Motd

    def AttemptAddPlayer(self,pPlayer):
        if len(self.PlayerIDs) == 0:
            return False
        else:
            self.SocketToPlayer[pPlayer.GetSocket()] = pPlayer
            self.PlayerSet.add(pPlayer)
            self.AuthPlayers.add(pPlayer)
            pPlayer.SetId(self.PlayerIDs.pop())
            self.HeartBeatController.IncreaseClients()

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
            
        if pPlayer.GetName() in self.PlayerNames:
            self.PlayerNames.remove(pPlayer.GetName())

        if pPlayer.GetWorld() != None:
            pPlayer.GetWorld().RemovePlayer(pPlayer)
        self.HeartBeatController.DecreaseClients()

    def GetPlayerFromSocket(self,Socket):
        return self.SocketToPlayer[Socket]
    def SendNotice(self,Message):
        Packet = OptiCraftPacket(SMSG_MESSAGE)
        Packet.WriteByte(0xFF)
        Packet.WriteString(Message)
        self.SendPacketToAll(Packet)

    def SendPacketToAll(self,Packet):
        for pPlayer in self.PlayerSet:
            pPlayer.SendPacket(Packet)