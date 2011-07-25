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
from core.jsondict import JsonSerializeableObject
from core.console import *
import os
import os.path
import shutil

class TitleData(JsonSerializeableObject):
    '''Simple object to store title information on a player object'''
    def __init__(self, pPlayer = None, Title = None):
        self.pPlayer = pPlayer
        self.Title = Title

class TitlePlugin(PluginBase):
    TITLE_KEY = "TITLES"

        
    def RegisterCommands(self):
        self.AddCommand("titleset", TitleSetCmd, 'admin', 'Sets the title of a user', 'Incorrect syntax! Usage: /titleset <username> <title>', 2)
        self.AddCommand("titleget", TitleGetCmd, 'admin', 'Gets the title of a user', 'Incorrect syntax! Usage: /titleget <username>', 1)
        self.AddCommand("titledel", TitleDelCmd, 'admin', 'Gets the title of a user', 'Incorrect syntax! Usage: /titledel <username>', 1)
            
    def OnLoad(self):
        self.RegisterCommands()
        self.PluginMgr.RegisterHook(self, self.OnPlayerDataLoaded, Hooks.ON_PLAYER_DATA_LOADED)
    
    def OnPlayerDataLoaded(self, pPlayer):
        JsonTitleData = pPlayer.GetPermanentPluginData(TitlePlugin.TITLE_KEY)
        if JsonTitleData is None:
            return
        PlayerTitle = TitleData(pPlayer)
        PlayerTitle.FromJson(JsonTitleData)
        pPlayer.SetPermanentPluginData(TitlePlugin.TITLE_KEY, PlayerTitle)
        pPlayer.SetColouredName("%s %s" % (PlayerTitle.Title, pPlayer.GetColouredName()))
    
##############################
#        Commands            #
##############################

class TitleCommand(CommandObject):
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Alias = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Alias)
        self.ServerControl = self.CmdHandler.ServerControl
        
    def DeleteTitle(self, Username):
        self._RemoveTitleFromName(Username)
        self.ServerControl.FetchPlayerDataEntryAsync(Username, TitleCommand._DeleteTitleCallback)
    
    def _RemoveTitleFromName(self, Username):
        '''Removes the title from a Player objects name. Does not remove it from the database!'''
        pPlayer = self.ServerControl.GetPlayerFromName(Username)
        if pPlayer is not None:
            CurrentTitle = pPlayer.GetPermanentPluginData(TitlePlugin.TITLE_KEY)
            if CurrentTitle is not None:
                pPlayer.SetColouredName(pPlayer.GetColouredName().replace("%s " % CurrentTitle.Title, ""))
                
    @staticmethod
    def _DeleteTitleCallback(DataEntry, kwArgs):
        if DataEntry is None:
            return
        if DataEntry.PermanentPluginData.has_key(TitlePlugin.TITLE_KEY):
            del DataEntry.PermanentPluginData[TitlePlugin.TITLE_KEY]   
            DataEntry.Save()
    
    def SetTitle(self, Username, Title):
        Username = Username.lower()
        
        pPlayer = self.ServerControl.GetPlayerFromName(Username)
        if pPlayer is not None:
            self._RemoveTitleFromName(Username)  
                
            pPlayer.SetColouredName("%s %s" % (Title, pPlayer.GetColouredName()))
        self.ServerControl.FetchPlayerDataEntryAsync(Username, TitleCommand._SetTitleCallback, {"Title": Title})
            
    @staticmethod
    def _SetTitleCallback(DataEntry, kwArgs):
        if DataEntry is None:
            return
        PlayerTitleData = TitleData(Title = kwArgs["Title"])
        DataEntry.PermanentPluginData[TitlePlugin.TITLE_KEY] = PlayerTitleData
        DataEntry.Save()    

class TitleSetCmd(TitleCommand):
    def Run(self, pPlayer, Args, Message):
        Username = Args[0].lower()
        Title = ' '.join(Args[1:])
             
        pPlayer.SendMessage("&SSet player &V%s's &Stitle to: %s" % (Username, Title))
        self.SetTitle(Username, Title)
        
class TitleGetCmd(TitleCommand):
    def Run(self, pPlayer, Args, Message):
        Username = Args[0].lower()
        self.ServerControl.FetchPlayerDataEntryAsync(Username, TitleGetCmd._TitleGetCallback, {"pPlayerName": pPlayer.GetName(), "ServerControl": self.ServerControl})
    
    @staticmethod
    def _TitleGetCallback(DataEntry, kwArgs):
        ServerControl = kwArgs["ServerControl"]
        pPlayer = ServerControl.GetPlayerFromName(kwArgs["pPlayerName"])
        if pPlayer is None:
            return
        if DataEntry is None:
            pPlayer.SendMessage("&RThat player does not exist!")
            return

        Title = DataEntry.PermanentPluginData.get(TitlePlugin.TITLE_KEY, None)
        
        if Title is not None:
            if type(Title) == dict:
                #Player is offline, data needs to be deserialized
                PlayerTitle = TitleData()
                PlayerTitle.FromJson(Title)
                Title = PlayerTitle
                
            pPlayer.SendMessage("&SPlayer &V%s's &Stitle is: %s" % (DataEntry.Username, Title.Title))
        else:
            pPlayer.SendMessage("&RThat player does not have a title!")

class TitleDelCmd(TitleCommand):
    def Run(self, pPlayer, Args, Message):
        Username = Args[0].lower()
        self.DeleteTitle(Username)
        pPlayer.SendMessage("&SThat players title has been deleted.")
    
