# To change this template, choose Tools | Templates
# and open the template in the editor.
import time
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
        self.MaxClients = 100
        self.Public = True
        self.HeartBeatController = HeartBeatController(self)
        self.SockManager = SocketManager(self)
        self.PlayerSet = set() #All players logged into the server
        self.AuthPlayers = set() #Players without a world (Logging in)
        self.PlayersPendingRemoval = list() #Players to remove from our set at the end of a cycle.
        self.PlayerIDs = range(self.MaxClients)
        reversed(self.PlayerIDs)
        self.SocketToPlayer = dict()
        self.Running = False
        self.DefaultWorld = World("OptiCraft Default World",True,True)
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
                self.DefaultWorld.AddPlayer(pPlayer)

            #TODO: Threading for worlds - Multi worlds..
            self.DefaultWorld.run()

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
                    
            time.sleep(0.05)

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
        if pPlayer.GetWorld() != None:
            pPlayer.GetWorld.RemovePlayer(pPlayer)
        self.HeartBeatController.DecreaseClients()

    def GetPlayerFromSocket(self,Socket):
        return self.SocketToPlayer[Socket]

    def SendPacketToAll(self,Packet):
        for pPlayer in self.PlayerSet:
            pPlayer.SendPacket(Packet)