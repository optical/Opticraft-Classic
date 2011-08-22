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

##########################
#        SETTINGS        #
##########################
DUMP_INTERVAL = 60 #The time between dumping out JSON statistics to disk
DUMP_PATH = "" #The path to dump the statistics to. If left blank it will dump to opticraft's working directory
DUMP_FILE = "ServerStatus.json" #Filename to write the statistics in JSON format out to.
###############################################
#        DO NOT EDIT BEYOND THIS LINE!        #
###############################################

from core.constants import *
from core.pluginmanager import PluginBase, Hooks, PluginManager
from core.jsondict import JsonSerializeableObject
from core.world import MetaDataKey
from core.console import *
import platform
import multiprocessing
import time
import os.path
import json

class StatusDumperPlugin(PluginBase):
    def __init__(self, PluginMgr, ServerControl, Name):
        PluginBase.__init__(self, PluginMgr, ServerControl, Name)
        self.LastStatisticsDump = 0
        
    def OnLoad(self):
        self.PluginMgr.RegisterHook(self, self.OnTick, Hooks.ON_SERVER_TICK)
        
    def OnTick(self):
        if time.time() > self.LastStatisticsDump + DUMP_INTERVAL:
            self.DumpStatistics()
            self.LastStatisticsDump = time.time()
            
    def DumpStatistics(self):
        with open(os.path.join(DUMP_PATH, DUMP_FILE), "w") as fHandle:
            Stats = ServerStatus(self.ServerControl)._AsJson()
            json.dump(Stats, fHandle, indent = 1)
        Console.Out("Statistics", "Successfully wrote %s to disk" % DUMP_FILE)
        
class ServerStatus(JsonSerializeableObject):
    def __init__(self, ServerControl):
        self.PlayersOnline = len(ServerControl.PlayerSet)
        self.PeakPlayers = ServerControl.PeakPlayers
        self.UptimeString = ServerControl.GetUptimeStr()
        
        self.CurrentCpuUsage, self.CurrentCpuUserTime, self.CurrentCpuSysTime = ServerControl.GetCurrentCpuUsage()
        self.OverallCpuUsage, self.OverallCpuUserTime, self.OverallCpuSysTime = ServerControl.GetTotalCpuUsage()
        self.CurrentCpuUsage /= multiprocessing.cpu_count()
        self.CurrentCpuUserTime /= multiprocessing.cpu_count()
        self.CurrentCpuSysTime /= multiprocessing.cpu_count()
        self.OverallCpuUsage /= multiprocessing.cpu_count()
        self.OverallCpuUserTime /= multiprocessing.cpu_count()
        self.OverallCpuSysTime /= multiprocessing.cpu_count()

        self.UploadRate = ServerControl.GetCurrentBwRate(IsUpload = True)
        self.DownloadRate = ServerControl.GetCurrentBwRate(IsUpload = False)
        self.VersionString = ServerControl.VersionString
        
        self.Platform = platform.system()
        if self.Platform == "Linux":
            DistData = platform.linux_distribution()
            self.Platform = "%s-%s" % (DistData[0], DistData[1])
        
        
        self.Players = []
        self.Worlds = []
        self.GeneratePlayerData(ServerControl)
        self.GenerateWorldData(ServerControl)
        
    def GeneratePlayerData(self, ServerControl):
        for pPlayer in ServerControl.PlayerSet:
            self.Players.append(PlayerData(pPlayer))
    
    def GenerateWorldData(self, ServerControl):
        for WorldName, MetaData in ServerControl.GetWorldMetaDataCache().iteritems():
            pWorld = ServerControl.GetActiveWorld(WorldName)
            self.Worlds.append(WorldData(MetaData, WorldName, pWorld))
            

class PlayerData(JsonSerializeableObject):
    def __init__(self, pPlayer):
        self.Name = pPlayer.GetName()
        self.BlocksMade = pPlayer.GetBlocksMade()
        self.BlocksErased = pPlayer.GetBlocksErased()
        self.LoginTime = pPlayer.GetLoginTime()
        self.Rank = pPlayer.GetRank()
        self.LoginCount = pPlayer.GetLoginCount()
        self.ChatLines = pPlayer.GetChatMessageCount()
        pPlayer.UpdatePlayedTime()
        self.PlayedTime = pPlayer.GetTimePlayed()
        self.JoinDate = pPlayer.GetJoinedTime()
    
class WorldData(JsonSerializeableObject):
    def __init__(self, WorldMetaData, WorldName, pWorld):
        if pWorld is None:
            self.PlayerCount = 0
        else:
            self.PlayerCount = len(pWorld.Players)
            
        self.Name = WorldName
        self.CreationDate = WorldMetaData[MetaDataKey.CreationDate]
        self.Hidden = WorldMetaData[MetaDataKey.IsHidden]
        self.JoinRank = WorldMetaData[MetaDataKey.MinimumJoinRank]
        self.BuildRank = WorldMetaData[MetaDataKey.MinimumBuildRank]
        self.X = WorldMetaData[MetaDataKey.X]
        self.Y = WorldMetaData[MetaDataKey.Y]
        self.Z = WorldMetaData[MetaDataKey.Z]
