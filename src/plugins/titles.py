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
        self.PluginMgr.RegisterHook(self, self.OnChat, Hooks.ON_PLAYER_CHAT)
    
    def OnPlayerDataLoaded(self, pPlayer):
        JsonTitleData = pPlayer.GetPermanentPluginData(TitlePlugin.TITLE_KEY)
        if JsonTitleData is None:
            return
        PlayerTitle = TitleData(pPlayer)
        PlayerTitle.FromJson(JsonTitleData)
        pPlayer.SetPermanentPluginData(TitlePlugin.TITLE_KEY, PlayerTitle)
        
    def OnChat(self, pPlayer, Message):
        PlayerTitle = pPlayer.GetPermanentPluginData(TitlePlugin.TITLE_KEY)
        Title = ""
        if PlayerTitle is not None:
            Title = PlayerTitle.Title + " "
        self.ServerControl.SendChatMessage("%s%s" % (Title, pPlayer.GetColouredName()), Message)
        return False
    
##############################
#        Commands            #
##############################

class TitleCommand(CommandObject):
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden)
        self.ServerControl = self.CmdHandler.ServerControl
        
    def DeleteTitle(self, Username):
        self.ServerControl.FetchPlayerDataEntryAsync(Username, TitleCommand._DeleteTitleCallback)
    
                
    @staticmethod
    def _DeleteTitleCallback(DataEntry, kwArgs):
        if DataEntry is None:
            return
        if DataEntry.PermanentPluginData.has_key(TitlePlugin.TITLE_KEY):
            del DataEntry.PermanentPluginData[TitlePlugin.TITLE_KEY]   
            DataEntry.Save()
    
    def SetTitle(self, Username, Title):
        Username = Username.lower()
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
    
