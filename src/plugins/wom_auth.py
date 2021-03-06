###README###
#Warning: Authenticating with WOM makes your server more vulnerable to being hacked
#If you intend to use WOM Auth, i recommend using a different salt to minecraft.net (USE_SERVER_SALT = False)
#I also recommend you do not allow anyone with op+ to login with wom auth, should WOM ever be compromised. (WOM_MAX_RANK = "builder")
###README###


##########################
#        SETTINGS        #
##########################
USE_SERVER_SALT = False #Use the same Salt for minecraft.net authentication? Not recommended!
WOM_SALT = "CHANGEME" #Salt to use to authenticate with the WOM server. Can be up to 30 characters long
WOM_MAX_RANK = "builder" #The highest rank allowed to login with wom auth. Disable with WOM_MAX_RANK = None
WOM_NAME_OVERRIDE = None #If you want a seperate name on the WOM list, put it here
###############################################
#        DO NOT EDIT BEYOND THIS LINE!        #
###############################################

from core.pluginmanager import PluginBase, Hooks
from core.commandhandler import CommandObject
from core.console import *

import time
import hashlib
import urllib
import threading

class WOMAuthenticationPlugin(PluginBase):
    LastHeartbeat = 0
    Salt = None
    MaxRankLevel = -1
    def OnLoad(self):
        if USE_SERVER_SALT == False:
            if WOM_SALT == "CHANGEME":
                Console.Error("WomAuth", "You have not set an authentication salt. WomAuth is disabled")
                return
            else:
                self.Salt = WOM_SALT
        else:
            self.Salt = self.ServerControl.Salt
            
        if WOM_MAX_RANK != None:
            self.MaxRankLevel = self.ServerControl.GetRankLevel(WOM_MAX_RANK)
        
        self.PluginMgr.RegisterHook(self, self.OnTick, Hooks.ON_SERVER_TICK)
        self.PluginMgr.RegisterHook(self, self.OnPlayerAuthCheck, Hooks.ON_PLAYER_AUTH_CHECK)
        
    def OnTick(self):
        if self.LastHeartbeat + 40 < time.time():
            self.SendHeartBeat()
            
    def OnPlayerAuthCheck(self, pPlayer, HashedPass, CorrectPass):
        Rank = self.ServerControl.GetRank(pPlayer.GetName())
        RankLevel = self.ServerControl.GetRankLevel(Rank)
        if RankLevel > self.MaxRankLevel:
            return None
        
        WomHash = hashlib.md5(self.Salt + pPlayer.GetName()).hexdigest().strip("0")
        if HashedPass == WomHash:
            return True
        else:
            return None
        
    def SendHeartBeat(self):
        data = {
            "port": int(self.ServerControl.Port.split(",")[0]),
            "max": self.ServerControl.MaxClients,
            "name": WOM_NAME_OVERRIDE if WOM_NAME_OVERRIDE is not None else self.ServerControl.Name,
            "public": self.ServerControl.Public,
            "version": 7,
            "salt": self.Salt,
            "noforward": 1,
            "users": len(self.ServerControl.PlayerSet)
        }
        url = 'http://direct.worldofminecraft.com/hb.php?%s' % urllib.urlencode(data)
        threading.Thread(name = "WOMAuth", target = WOMAuthenticationPlugin._SendHeartBeatAsync, args = (url,)).start()
        self.LastHeartbeat = time.time()
        
    @staticmethod
    def _SendHeartBeatAsync(Url):
        try:
            urllib.urlopen(Url).read()
        except:
            Console.Warning("WOMAuth", "Failed to register heartbeat")
