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

from core.pluginmanager import PluginBase, Hooks
from core.commandhandler import CommandObject
from core.console import *
import os
import os.path
import shutil

class TitlePlugin(PluginBase):
    #TitlePlugin is a singleton. This acts as a kind of static reference to us.
    Instance = None
    def __init__(self, PluginMgr, ServerControl, Name):
        PluginBase.__init__(self, PluginMgr, ServerControl, Name)
        TitlePlugin.Instance = self
        self.TitlePlayers = dict()
        self.LoadTitles()
        
    def RegisterCommands(self):
        self.AddCommand("titleset", TitleSetCmd, 'admin', 'Sets the title of a user', 'Incorrect syntax! Usage: /titleset <username> <title>', 2)
        self.AddCommand("titleget", TitleGetCmd, 'admin', 'Gets the title of a user', 'Incorrect syntax! Usage: /titleget <username>', 1)
        self.AddCommand("titledel", TitleDelCmd, 'admin', 'Gets the title of a user', 'Incorrect syntax! Usage: /titledel <username>', 1)
        
    def LoadTitles(self):
        if os.path.exists("titles.txt") == False:
            open("titles.txt", "w").close()
            
        with open("titles.txt", "r") as fHandle:
            for Line in fHandle:
                Username, Title = Line.split("=")
                self.TitlePlayers[Username.lower()] = Title
                
    def SaveTitles(self):
        with open("titles.tmp", "w") as fHandle:
            for Username, Title in self.TitlePlayers.iteritems():
                fHandle.write("%s=%s\n" % (Username, Title))
        
        shutil.copy("titles.tmp", "titles.txt")
        os.remove("titles.tmp")
        
    def OnLoad(self):
        self.RegisterCommands()
        self.PluginMgr.RegisterHook(self, self.OnPlayerLogin, Hooks.ON_PLAYER_CONNECT)
        self.PluginMgr.RegisterHook(self, self.OnServerShutdown, Hooks.ON_SERVER_SHUTDOWN)
        
    def OnServerShutdown(self):
        self.SaveTitles()
    
    def OnPlayerLogin(self, pPlayer):
        Title = self.TitlePlayers.get(pPlayer.GetName().lower(), None)
        if Title is not None:
            pPlayer.SetColouredName("%s %s" % (Title, pPlayer.GetColouredName()))
                                            
    def DeleteTitle(self, Username):
        Username = Username.lower()
        
        pPlayer = self.ServerControl.GetPlayerFromName(Username)
        if pPlayer is not None:
            pPlayer.SetColouredName(pPlayer.GetColouredName().replace("%s " % self.TitlePlayers[Username], ""))
                                    
        del self.TitlePlayers[Username.lower()]                         

    def SetTitle(self, Username, Title):
        Username = Username.lower()
        self.TitlePlayers[Username] = Title
        
        pPlayer = self.ServerControl.GetPlayerFromName(Username)
        if pPlayer is not None:
            pPlayer.SetColouredName("%s %s" % (Title, pPlayer.GetColouredName()))
    
    def GetTitle(self, Username):
        return self.TitlePlayers.get(Username.lower(), None)
    
##############################
#        Commands            #
##############################

class TitleSetCmd(CommandObject):
    def Run(self, pPlayer, Args, Message):
        Username = Args[0].lower()
        Title = ' '.join(Args[1:])
        if "=" in Title:
            pPlayer.SendMessage("&RTitles may not contain the '=' symbol.")
            return
        
        if TitlePlugin.Instance.TitlePlayers.has_key(Username):
            TitlePlugin.Instance.DeleteTitle(Username)
            
        pPlayer.SendMessage("&SSet player &V%s's &Stitle to: %s" % (Username, Title))
        TitlePlugin.Instance.SetTitle(Username, Title)
        
    
class TitleGetCmd(CommandObject):
    def Run(self, pPlayer, Args, Message):
        Username = Args[0].lower()
        Title = TitlePlugin.Instance.GetTitle(Username)
        if Title is not None:
            pPlayer.SendMessage("&SPlayer &V%s's &Stitle is: %s" % (Username, Title))
        else:
            pPlayer.SendMessage("&RThat player does not have a title!")
    
class TitleDelCmd(CommandObject):
    def Run(self, pPlayer, Args, Message):
        Username = Args[0].lower()
        TitlePlugin.Instance.DeleteTitle(Username)
        pPlayer.SendMessage("&SThat players title has been deleted.")
    
