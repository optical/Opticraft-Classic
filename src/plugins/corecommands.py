from core.pluginmanager import PluginBase
from core.commandhandler import CommandObject
from core.world import MetaDataKey
from core.console import *
from core.constants import *
#from core.servercontroller import ServerController

from core.world import World
import os.path
import sqlite3 as dbapi
import shutil
import threading
import multiprocessing

class Commands(PluginBase):
    def OnLoad(self):
        self.RegisterCommands()

    def RegisterCommands(self):
        #Populate the command table here
        ######################
        #PUBLIC COMMANDS HERE#
        ######################
        self.AddCommand("rules", RulesCmd, 'guest', 'Displays a list of rules for this server', '', 0)
        self.AddCommand("about", AboutCmd, 'guest', 'Displays history of a block when you destroy/create one', '', 0)
        self.AddCommand("cmdlist", CmdListCmd, 'guest', 'Lists all commands available to you', '', 0)
        self.AddCommand("help", HelpCmd, 'guest', 'Gives help on a specific command. Usage: /help <cmd>', 'Incorrect syntax! Usage: /help <cmd>. /cmdlist for a list of commands', 1)
        self.AddCommand("worlds", WorldsCmd, 'guest', 'Lists all available worlds', '', 0)
        self.AddCommand("join", JoinWorldCmd, 'guest', 'Changes the world you are in', 'Incorrect syntax! Usage: /join <world>. Use /worlds to see a list of worlds.', 1)
        self.AddCommand("gps", GPSCmd, 'guest', 'Returns your current position', '', 0)
        self.AddCommand("grass", GrassCmd, 'guest', 'Allows you to place grass', '', 0)
        self.AddCommand("place", PlaceCommand, 'guest', 'Places a block where you are standing', '', 0)
        self.AddCommand("paint", PaintCmd, 'guest', 'When you destroy a block it will be replaced by what you are currently holding', '', 0)
        self.AddCommand("sinfo", sInfoCmd, 'guest', 'Displays information about the server', '', 0)
        self.AddCommand("winfo", wInfoCmd, 'guest', 'Displays information about a world', '', 0)
        self.AddCommand("version", VersionCmd, 'guest', 'Displays information about the server', '', 0, Hidden = True) #Hidden
        self.AddCommand("credits", CreditsCmd, 'guest', 'Displays information about the server', '', 0, Hidden = True) #Hidden
        self.AddCommand("stats", StatsCmd, 'guest', 'Displays a players statistics. Usage: /stats [Username]', '', 0)
        self.AddCommand("togglenotifications", ToggleNotificationsCmd, 'guest', 'Turns join/leave messages on or off', '', 0)
        self.AddCommand("deafen", DeafenCmd, 'guest', 'Deafens yourself to other players chat messages', '', 0)
        self.AddCommand("ranks", RanksCmd, 'guest', 'Displays information on all the ranks', '', 0)
        self.AddCommand("whois", PlayerInfoCmd, 'guest', 'Returns information on a player', 'Incorrect syntax! Usage: /whois <username>', 1)
        self.AddCommand("players", PlayerListCmd, 'guest', 'Lists all online players', '', 0)
        self.AddCommand("me", EmoteCmd, 'guest', 'Emotes an aceiont', 'Incorrect syntax! Usage: /me <message>', 1)
        self.AddCommand("r", ReplyCmd, 'guest', 'Replys to the last person who sent you a PM', 'Incorrect syntax! Usage: /reply <Message>', 1)
        self.AddCommand("time", TimeCmd, 'guest', 'Returns current server time', '', 0)

        ########################
        #BUILDER COMMANDS HERE #
        ########################
        self.AddCommand("tp", AppearCmd, 'builder', 'Teleports you to a players location', 'Incorrect syntax! Usage: /appear <username>', 1)
        #########################
        #OPERATOR COMMANDS HERE #
        #########################
        self.AddCommand("ban", BanCmd, 'operator', 'Bans a player from the server', 'Incorrect syntax! Usage: /ban <username> <duration>', 1)
        self.AddCommand("unban", UnbanCmd, 'operator', 'Unbans a player from the server', 'Incorrect syntax! Usage: /unban <username>', 1)
        self.AddCommand("kick", KickCmd, 'operator', 'Kicks a player from the server', 'Incorrect syntax! Usage: /kick <username> [reason]', 1)
        self.AddCommand("freeze", FreezeCmd, 'operator', 'Freezes and unfreezes a player in place, preventing movement', 'Incorrect syntax! Usage: /freeze <username>', 1)
        self.AddCommand("mute", MuteCmd, 'operator', 'Mutes and unmutes a player, temporarily preventing them from talking', 'Incorrect syntax! Usage: /mute <username>', 1)
        self.AddCommand("summon", SummonCmd, 'operator', 'Teleports a player to your location', 'Incorrect syntax! Usage: /summon <username>', 1)
        self.AddCommand("undoactions", UndoActionsCmd, 'operator', 'Undoes all of a a players actions in the last X seconds', 'Incorrect Syntax! Usage: /undoactions <username> <seconds>', 2)
        self.AddCommand("invisible", InvisibleCmd, 'operator', "Makes you invisible to other players", "", 0)
        self.AddCommand("ModifyRank", ModifyRankCmd, 'operator', 'Modify\'s a players rank.', 'Incorrect syntax. Usage: /modifyrank <username> <rank>', 2)
        ######################
        #ADMIN COMMANDS HERE #
        ######################
        self.AddCommand("serversay", ServerSayCmd, 'admin', 'Sends a message to the whole server, like an announcement', 'Enter a message to announce', 1)
        self.AddCommand("ipban", AddIPBanCmd, 'admin', 'Ip bans a player from the server.', 'Incorrect syntax! Usage: /addipban <ip/username> <duration>', 1)
        self.AddCommand("delipban", DelIPBanCmd, 'admin', 'Removes an IP ban', 'Incorrect syntax! Usage: /delipban <ip/username>', 1)
        self.AddCommand("save", SaveCmd, 'admin', 'Saves all actively running worlds', '', 0)
        self.AddCommand("backup", BackupCmd, 'admin', 'Backs up all actively running worlds', '', 0)
        self.AddCommand("setspawn", SetSpawnCmd, 'admin', 'Changes the worlds default spawn location to where you are standing', '', 0)
        self.AddCommand("tempop", TempOpCmd, 'admin', 'Grants a user operator privledges until they log off', 'Incorrect syntax! Usage: /tempop <username>', 1)
        self.AddCommand("wbuildrank", WorldSetBuildRankCmd, 'admin', 'Sets the minimum rank to build on a world', 'Incorrect syntax. Usage: /wbuildrank <world> <rank>', 2)
        self.AddCommand("wjoinrank", WorldSetAccessRankCmd, 'admin', 'Sets the minimum rank to join a world', 'Incorrect syntax. Usage: /wjoinrank <world> <rank>', 2)
        self.AddCommand("createworld", CreateWorldCmd, 'admin', 'Creates a new world.', 'Incorrect syntax. Usage: /createworld <name> <length> <width> <height>', 4)
        self.AddCommand("setdefaultworld", SetDefaultWorldCmd, 'admin', 'Sets the world you specify to be the default one', 'Incorrect syntax. Usage: /setdefaultworld <name>', 1)
        self.AddCommand("renameworld", RenameWorldCmd, 'admin', 'Renames a world', 'Incorrect syntax! Usage: /renameworld <oldname> <newname>', 2)
        self.AddCommand("hideworld", HideWorldCmd, 'admin', 'Hides a world from the /worlds list', 'Incorrect syntax! Usage: /hideworld <worldname>', 1)
        self.AddCommand("unhideworld", UnHideWorldCmd, 'admin', 'Unhides a world from the /worlds list', 'Incorrect syntax! Usage: /unhideworld <worldname>', 1)
        self.AddCommand("loadworld", LoadWorldCmd, 'admin', 'Loads a world which has been added to the Worlds folder', 'Incorrect syntax! Usage: /loadworld <name>', 1)
        self.AddCommand("loadtemplate", LoadTemplateCmd, 'admin', 'Loads a template world from the Templates directory', 'Incorrect syntax! Usage: /loadtemplate <templatename> <worldname>', 2)
        self.AddCommand("showtemplates", ShowTemplatesCmd, 'admin', 'Lists all the available world templates', '', 0)
        self.AddCommand("maketemplate", MakeTemplateCmd, 'admin', 'Shelves a world as a template for later use', 'Incorrect syntax! Usage: /maketemplate <worldname> <templatename>', 2)
        self.AddCommand("deletetemplate", DeleteTemplateCmd, 'admin', 'Erases a template for disk', 'Incorrect syntax! Usage: /deletetemplate <templatename>', 1)
        self.AddCommand("plugin", PluginCmd, 'admin', 'Provides the ability to list, load, unload and reload plugins', 'Incorrect syntax! Usage: /plugins <list/load/unload/reload> [plugin]', 1)
        ######################
        #OWNER COMMANDS HERE #
        ######################
        self.AddCommand("flushblocklog", FlushBlockLogCmd, 'owner', 'Flushes the worlds blocklog to disk', '', 0)
        self.AddCommand("removeworld", DeleteWorldCmd, 'owner', 'Deletes a world from the server', 'Incorrect syntax! Usage: /removeworld <worldname>', 1)
        self.AddCommand("worldsummon", WorldSummonCmd, 'owner', 'Summons everyone on your world to your position', '', 0)
        self.AddCommand("masssummon", MassSummonCmd, 'owner', 'Summons everyone on the server to your position', '', 0)

        ######################
        #CONFIG COMMANDS HERE#
        ######################
        self.AddCommand("water", WaterCmd, self.ServerControl.WaterRank, 'Allows you to place water', '', 0)
        self.AddCommand("lava", LavaCmd, self.ServerControl.LavaRank, 'Allows you to place lava', '', 0)        
        self.AddCommand("solid", SolidCmd, self.ServerControl.PlaceAdmincreteRank, 'Allows you to place bedrock', '', 0)


######################
#PUBLIC COMMANDS HERE#
######################
class CmdListCmd(CommandObject):
    '''Handle for the /cmdlist command'''
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name)
        self.Aliases = set(["commands"])
        
    
    def Run(self, pPlayer, Args, Message):
        Commands = ''
        for key in self.CmdHandler.CommandTable:
            CmdObj = self.CmdHandler.CommandTable[key]
            if CmdObj.Hidden == True or key in CmdObj.Aliases:
                continue
            if CmdObj.Permissions != '':
                if pPlayer.HasPermission(CmdObj.Permissions) == False:
                    continue #Don't send commands to the client if he doesn't possess the permission to use it!

            Commands += key + ' '
        pPlayer.SendMessage("&SAvailable commands:")
        pPlayer.SendMessage("&S" + Commands)
        pPlayer.SendMessage("&SType /help <cmd> for more specific help on a command.")

class GrassCmd(CommandObject):
    '''Command handler for /grass command. Replaces all block placed with grass'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.GetBlockOverride() == BLOCK_GRASS:
            pPlayer.SendMessage("&SYou are no longer placing grass")
            pPlayer.SetBlockOverride(-1)
            return
        else:
            pPlayer.SetBlockOverride(BLOCK_GRASS)
            pPlayer.SendMessage("&SEvery block you create will now be grass. Type /grass to disable.")
            
class PaintCmd(CommandObject):
    '''Command handler for /paint command. When you destroy a block it is replaced with the block you are holding'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.GetPaintCmd():
            pPlayer.SetPaintCmd(False)
            pPlayer.SendMessage("&SPaint command has been disabled")
            return
        else:
            pPlayer.SetPaintCmd(True)
            pPlayer.SendMessage("&SPaint command enabled. Type /paint again to disable")
            
class HelpCmd(CommandObject):
    '''Returns a helpful message about a command'''
    def Run(self, pPlayer, Args, Message):
        if self.CmdHandler.CommandTable.has_key(Args[0].lower()) == False:
            pPlayer.SendMessage("&R" + "That command does not exist!")
            return
        else:
            CmdObj = self.CmdHandler.CommandTable[Args[0].lower()]
            pPlayer.SendMessage("&S" + CmdObj.HelpMsg)
            
class RulesCmd(CommandObject):
    '''Lists all of the servers rules'''
    def Run(self, pPlayer, Args, Message):
        if len(pPlayer.ServerControl.Rules) == 0:
            pPlayer.SendMessage("&SThis server has no rules!")
            return
        pPlayer.SendMessage("&SThe rules for this server are as follows:")
        for line in pPlayer.ServerControl.Rules:
            pPlayer.SendMessage(line)

class AboutCmd(CommandObject):
    '''The next block a player destroys/creates will display the blocks infromation'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.World.LogBlocks == True:
            pPlayer.SetAboutCmd(True)
            pPlayer.SendMessage("&SPlace/destroy a block to see what was there before")
        else:
            pPlayer.SendMessage("&RBlock history is disabled")

class PlaceCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):
        Block = pPlayer.GetBlockOverride() if pPlayer.GetBlockOverride() != -1 else pPlayer.LastBlock
        pPlayer.GetWorld().AttemptSetBlock(pPlayer, pPlayer.GetX() / 32, pPlayer.GetY() / 32, pPlayer.GetZ() / 32, Block, ResendToClient = True)
        pPlayer.SendMessage("&SBlock placed")
        
class JoinWorldCmd(CommandObject):
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name)
        self.Aliases = set(["j", "warp", "goto"])
            
    '''Handler for the /join command. Changes the players world'''
    def Run(self, pPlayer, Args, Message):
        World = Args[0]
        if pPlayer.IsFrozen:
            pPlayer.SendMessage("&RYou cannot change worlds while frozen!")
            return
        if pPlayer.ServerControl.WorldExists(World) == False:
            pPlayer.SendMessage("&RThat world does not exist!")
            return
        if pPlayer.GetWorld().Name.lower() == World.lower():
            pPlayer.SendMessage("&RYou are already on that world!")
            return
        if pPlayer.ServerControl.Now - pPlayer.GetLastWorldChange() < 5:
            pPlayer.SendMessage("&RYou cannot change worlds that often!")
            return
        if pPlayer.HasPermission(pPlayer.ServerControl.GetWorldJoinRank(World)) == False:
            pPlayer.SendMessage("&RYou do not have the required rank to join that world")
            return
        for pWorld in pPlayer.ServerControl.ActiveWorlds:
            if pWorld.Name.lower() == World.lower():
                if pWorld.IsFull():
                    pPlayer.SendMessage("&RThat world is full. Try again later")
                    return

        pPlayer.ChangeWorld(World)
        
class GPSCmd(CommandObject):
    '''Handler for the /gps command. Returns current coordinates on the world'''
    def Run(self, pPlayer, Args, Message):
        pPlayer.SendMessage("&SYour current position is: &V(%d,%d,%d)" % (pPlayer.GetX() / 32, pPlayer.GetY() / 32, pPlayer.GetZ() / 32))   
             
class WorldsCmd(CommandObject):
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name)
        self.Aliases = set(["maps"])
            
    '''Handler for the /worlds command. Lists all available worlds.'''
    def Run(self, pPlayer, Args, Message):
        ActiveWorlds, IdleWorlds = pPlayer.ServerControl.GetWorlds()
        All = len(Args) > 0
        if All:
            pPlayer.SendMessage("&SDisplaying all worlds")
        pPlayer.SendMessage("&SThe following worlds are available:")
        WorldList = [(pPlayer.ServerControl.RankColours[pWorld.GetMinimumBuildRank()], pWorld.Name) for pWorld in ActiveWorlds if not pWorld.IsHidden() or All]
        WorldList += [(pPlayer.ServerControl.RankColours[pPlayer.ServerControl.GetWorldBuildRank(pWorld)], pWorld) for pWorld in IdleWorlds if not pPlayer.ServerControl.IsWorldHidden(pWorld) or All]
        WorldList.sort(key = lambda world: world[1].lower())
        OutString = bytearray()
        for WorldItem in WorldList:
            OutString += ''.join(WorldItem) + ' '
        pPlayer.SendMessage(str(OutString), False)
        if not All:
            pPlayer.SendMessage("&STo see all worlds, type /worlds all.")

class StatsCmd(CommandObject):
    '''Handler for the /stats command. Returns information'''
    def Run(self, pPlayer, Args, Message):
        TargetName = None
        if len(Args) == 0:
            TargetName = pPlayer.GetName()
        else:
            TargetName = Args[0]
    
        pPlayer.SendMessage("&SLooking up stats...")
        pPlayer.ServerControl.FetchPlayerDataEntryAsync(TargetName, StatsCmd.StatsLookupCallback, {"ServerControl": pPlayer.ServerControl, "pPlayerName": pPlayer.GetName()})
            
    @staticmethod
    def StatsLookupCallback(DataEntry, kwArgs):
        ServerControl = kwArgs["ServerControl"]
        pPlayer = ServerControl.GetPlayerFromName(kwArgs["pPlayerName"])
        if pPlayer is None:
            return
        
        if DataEntry is None:
            pPlayer.SendMessage("&RThat player does not exist!")
            return
            
        pPlayer.SendMessage("&S%s's join date was: &V%s" % (DataEntry.Username, time.ctime(DataEntry.JoinTime)))
        pPlayer.SendMessage("&SSince then they have logged in &V%d &Stimes" % DataEntry.LoginCount)
        pPlayer.SendMessage("&SAnd have created &V%d &Sblocks and deleted &V%d" % (DataEntry.BlocksMade, DataEntry.BlocksErased))
        pPlayer.SendMessage("&STheir played time is &V%s" % ElapsedTime(DataEntry.TimePlayed))
        pPlayer.SendMessage("&SAnd they have spoken &V%d &Slines thus far" % DataEntry.ChatMessageCount)       
        
class ToggleNotificationsCmd(CommandObject):
    '''Handler for the /togglenotifications command. Enables/Disables join notices'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.GetJoinNotifications():
            pPlayer.SetJoinNotifications(False)
            pPlayer.SendMessage("&SJoin/Leave notifications have been disabled")
        else:
            pPlayer.SetJoinNotifications(True)
            pPlayer.SendMessage("&SJoin/Leave notifications have been enabled")

class DeafenCmd(CommandObject):
    '''Handler for the /deafen command. Enables/Disables player messages'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.GetDeafened() == False:
            pPlayer.SendMessage("&SYou are now deaf to other players")
            pPlayer.SetDeafened(True)
        else:
            pPlayer.SendMessage("&SYou are no longer deaf")
            pPlayer.SetDeafened(False)

class sInfoCmd(CommandObject):
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name)
        self.Aliases = set(["info", "serverreport"])    
    
    '''Handler for the /sinfo command. Returns server information'''
    def Run(self, pPlayer, Args, Message):
        System = platform.system()
        if System == "Linux":
            DistData = platform.linux_distribution()
            System = "%s-%s" % (DistData[0], DistData[1])
        WorldData = pPlayer.ServerControl.GetWorlds()
        D = multiprocessing.cpu_count() if len(Args) == 0 else 1
        pPlayer.SendMessage("&SThis server is running %s on &V%s." % (pPlayer.ServerControl.VersionString, System), False)
        pPlayer.SendMessage("&SCurrently &V%d &Susers online. Peak online: &V%d" % (pPlayer.ServerControl.NumPlayers, pPlayer.ServerControl.PeakPlayers), False)
        pPlayer.SendMessage("&SUsing &V%.2f%% &Scpu in the last minute, &V%.2f%% &Soverall." % (pPlayer.ServerControl.GetCurrentCpuUsage()[0] / D, pPlayer.ServerControl.GetTotalCpuUsage()[0] / D))
        pPlayer.SendMessage("&V%dMB &Sof memory used with &V%d &Sactive threads." % (pPlayer.ServerControl.GetMemoryUsage(), threading.activeCount()))
        pPlayer.SendMessage("&SBandwidth in the last minute. Down: &V%s&S. Up: &V%s" % (pPlayer.ServerControl.GetCurrentBwRate(False), pPlayer.ServerControl.GetCurrentBwRate(True)))
        pPlayer.SendMessage("&STotal worlds: &V%d &S(&V%d &Sactive, &V%d &Sidle)" % (len(WorldData[0]) + len(WorldData[1]), len(WorldData[0]), len(WorldData[1])), False)
        pPlayer.SendMessage("&SCurrent uptime: &V%s." % pPlayer.ServerControl.GetUptimeStr(), False)

class wInfoCmd(CommandObject):
    '''Handler for the /winfo command. Returns world information'''
    def Run(self, pPlayer, Args, Message):
        if len(Args) == 0:
            pWorld = pPlayer.GetWorld()
            WorldName = pWorld.Name
            MetaData = pPlayer.GetWorld().MetaData
        else:
            WorldName = Args[0]
            if pPlayer.ServerControl.WorldExists(WorldName) == False:
                pPlayer.SendMessage("&RThat world does not exist!")
                return
            pWorld = pPlayer.ServerControl.GetActiveWorld(WorldName)
            MetaData = pPlayer.ServerControl.WorldMetaDataCache[WorldName.lower()]
        
        pPlayer.SendMessage("&SInformation for world &V%s&S:" % WorldName)
        if pWorld is not None:
            pPlayer.SendMessage("&SCurrent players: &V%d" % len(pWorld.Players))
        
        pPlayer.SendMessage("&SDimensions: &V%d &Sx &V%d &Sx &V%d" % (MetaData[MetaDataKey.X], MetaData[MetaDataKey.Y], MetaData[MetaDataKey.Z]))
        pPlayer.SendMessage("&SCreated on &V%s" % time.ctime(MetaData[MetaDataKey.CreationDate]))
        pPlayer.SendMessage("&SJoin rank: &V%s&S. Build rank: &V%s" % (MetaData[MetaDataKey.MinimumJoinRank], MetaData[MetaDataKey.MinimumBuildRank]))
        
class VersionCmd(CommandObject):
    '''Handler for the /version command. Returns version information'''
    def Run(self, pPlayer, Args, Message):
        pPlayer.SendMessage("&SThis server is running &V%s" % pPlayer.ServerControl.VersionString)
        
class CreditsCmd(CommandObject):
    '''Handler for the /credits command. Returns credit information'''
    def Run(self, pPlayer, Args, Message):
        pPlayer.SendMessage("&SOpticraft was developed by Jared Klopper using the Python programming language, version 2.6+")
        
class RanksCmd(CommandObject):
    '''Handler for the /ranks command'''
    def Run(self, pPlayer, Args, Message):
        pPlayer.SendMessage("&SThe following ranks exist on this server")
        Items = pPlayer.ServerControl.RankNames
        for Rank in Items:
            Description = pPlayer.ServerControl.RankDescriptions.get(Rank.lower(), None)
            if Description is not None:
                Colour = pPlayer.ServerControl.RankColours[Rank.lower()]
                pPlayer.SendMessage("&V %s%s&V: %s" % (Colour, Rank, Description))

class PlayerInfoCmd(CommandObject):
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name)
        self.Aliases = set(["playerinfo"])
    '''Handler for the /whois command. Returns info on a player'''
    def Run(self, pPlayer, Args, Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target is None or Target.CanBeSeenBy(pPlayer) == False:
            #Player is not online, so we will actually query db which can take time. let user know.
            pPlayer.SendMessage("&SLooking up players information. One moment.")
        pPlayer.ServerControl.FetchPlayerDataEntryAsync(Username, PlayerInfoCmd.RowCallbackHandler, kwArgs = {"pPlayerName": pPlayer.GetName(), "ServerControl": pPlayer.ServerControl})
        
    @staticmethod
    def RowCallbackHandler(DataEntry, kwArgs):
        ServerControl = kwArgs["ServerControl"]
        pPlayer = ServerControl.GetPlayerFromName(kwArgs["pPlayerName"])
        if pPlayer is None:
            return
        if DataEntry is None:
            pPlayer.SendMessage("&RThat player does not exist!")
            return
        Username = DataEntry.Username
        Target = ServerControl.GetPlayerFromName(Username)
        
        if Target is None:
            #Offline player - use past tense.
            pPlayer.SendMessage("&S%s is &ROffline. &SRank: &V%s" % (Username, ServerControl.GetRank(Username).capitalize()))
            pPlayer.SendMessage("&SLast login was: &V%s &Sago" % (ElapsedTime(int(time.time()) - DataEntry.LoginTime)))
            pPlayer.SendMessage("&SJoined on: &V%s" % (time.ctime(DataEntry.JoinTime)))
            if pPlayer.HasPermission('operator'):
                pPlayer.SendMessage("&STheir last ip was &V%s" % (DataEntry.LastIP))
                if DataEntry.BannedBy != "":
                    pPlayer.SendMessage("&SThey were banned by &V%s" % (DataEntry.BannedBy))
                Date = ServerControl.GetUsernameBanExpiryDate(Username)
                
                if Date is not None:
                    if Date == 0:
                        pPlayer.SendMessage("&SThis is a &Vpermanent &Sban")
                    else:
                        try:
                            pPlayer.SendMessage("&SBan expires on &V%s" % (time.ctime(Date)))
                        except ValueError:
                            #This happens when a bans is so long, it goes beyond the platforms time_t size (32/64bits). The ban is basically permanent if this happens.
                            pPlayer.SendMessage("&SThis is a &Vpermanent &SBan")
                
                if DataEntry.RankedBy != "":
                    pPlayer.SendMessage("&STheir rank was set by &V%s" % DataEntry.RankedBy)
        else:
            #Online player - Use present tense
            pPlayer.SendMessage("&S%s has been online for &V%s" % (Target.GetName(), ElapsedTime(int(time.time()) - Target.GetLoginTime())))
            pPlayer.SendMessage("&SJoined on: &V%s" % (time.ctime(DataEntry.JoinTime)))
            if pPlayer.HasPermission('operator'):
                pPlayer.SendMessage("&SCurrent IP: &V%s" % (Target.GetIP()))
                if Target.GetRankedBy() != '':
                    pPlayer.SendMessage("&STheir rank was set by &V%s" % Target.GetRankedBy())
            if Target.GetWorld() is not None:
                pPlayer.SendMessage("&SThey are on world &V\"%s\"" % Target.GetWorld().Name)
            pPlayer.SendMessage("&STheir rank is &V%s" % Target.GetRank().capitalize())
            if Target.IsInvisible(): #Dont check CanBeSeenBy() - thats been done already.
                pPlayer.SendMessage("&SThey are currently invisible")            
                        



class TimeCmd(CommandObject):
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name)
        self.Aliases = set(["date"])
    
    '''Handler for the /time command. Returns server time'''
    def Run(self, pPlayer, Args, Message):
        pPlayer.SendMessage("&SCurrent server time: &V%s" % time.ctime(time.time()))
        
class PlayerListCmd(CommandObject):
    '''Handler for the /players command. Lists all online players'''
    def Run(self, pPlayer, Args, Message):
        pPlayer.SendMessage("&SThe following players are online:")
        OutStr = bytearray()
        PlayerList = sorted(pPlayer.ServerControl.PlayerSet, key = lambda player: player.GetName().lower())
        PlayerList.sort(key = lambda player: player.GetRankLevel())
        for oPlayer in PlayerList:
            if oPlayer.IsAuthenticated() == False:
                continue
            if oPlayer.CanBeSeenBy(pPlayer) == False:
                continue
            #1 = space
            if len(oPlayer.GetColouredName()) + 1 + len(OutStr) < 63:
                OutStr += ' '
                OutStr += oPlayer.GetColouredName()
            else:
                pPlayer.SendMessage(str(OutStr))
                OutStr = bytearray(oPlayer.GetColouredName())
        OutStr = str(OutStr)
        if OutStr != '':
            pPlayer.SendMessage(OutStr)

class EmoteCmd(CommandObject):    
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name)
        self.Aliases = set(["emote"])
        

    '''Handler for the /me command. Emotes an action'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.IsMuted:
            pPlayer.SendMessage("&RYou cannot emote while muted!")
            return
        pPlayer.ServerControl.SendMessageToAll('&5*%s %s' % (pPlayer.GetName(), ' '.join(Args)))
        pPlayer.ServerControl.PluginMgr.OnEmote(pPlayer, ' '.join(Args))

class ReplyCmd(CommandObject):
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name)
        self.Aliases = set(["reply"])    
    '''Handler for the /reply command. Shortcut command to reply to a PM'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.IsMuted:
            pPlayer.SendMessage("&RYou cannot chat while muted!")
            return
        if pPlayer.GetLastPM() == '':
            pPlayer.SendMessage("&RNo one recently sent you a PM!")
            return
        pPlayer.HandlePrivateMessage("%s %s" % (pPlayer.GetLastPM(), ' '.join(Args)))
########################
#BUILDER COMMANDS HERE #
########################
           
class AppearCmd(CommandObject):
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name)
        self.Aliases = set(["appear"])
    '''Appear command handler. Teleports user to specified players location'''
    def Run(self, pPlayer, Args, Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target is not None and Target.CanBeSeenBy(pPlayer) and Target.GetWorld() is not None:
            if pPlayer.GetWorld() != Target.GetWorld():
                if Target.GetWorld().IsFull():
                    pPlayer.SendMessage("&SYou cannot teleport to a world that is full")
                    return
                if pPlayer.HasPermission(pPlayer.ServerControl.GetWorldJoinRank(Target.GetWorld().Name)) == False:
                    pPlayer.SendMessage("&RYou do not have the required rank to join that world")
                    return                
                pPlayer.ChangeWorld(Target.GetWorld().Name)
                pPlayer.SetSpawnPosition(Target.GetX(), Target.GetY(), Target.GetZ(), Target.GetOrientation(), Target.GetPitch())
                return
            pPlayer.Teleport(Target.GetX(), Target.GetY(), Target.GetZ(), Target.GetOrientation(), Target.GetPitch())
        else:
            pPlayer.SendMessage("&RThat player is not online!")
#########################
#OPERATOR COMMANDS HERE #
#########################
class ModifyRankCmd(CommandObject):
    '''Handle for the /addrank command - gives a username a rank. Can only be used by admins'''
    def Run(self, pPlayer, Args, Message):
        Username = Args[0]
        Rank = Args[1].lower()
        if pPlayer.ServerControl.IsValidRank(Rank) == False:
            pPlayer.SendMessage("&RInvalid Rank! Valid ranks are:&V %s" % pPlayer.ServerControl.GetExampleRanks())
            return
        #Check to see we can set this rank.
        NewRank = pPlayer.ServerControl.GetRankLevel(Rank)
        if NewRank >= pPlayer.GetRankLevel():
            pPlayer.SendMessage("&RYou do not have permission to add this rank")
            return
        Target = pPlayer.ServerControl.GetRank(Username)
        if pPlayer.ServerControl.GetRankLevel(Target) >= pPlayer.GetRankLevel():
            pPlayer.SendMessage("&RYou may not set that players rank!")
            return
        pPlayer.ServerControl.SetRank(pPlayer.GetName(), Username, Rank)
        pPlayer.SendMessage("&SSuccessfully set &V%s's &Srank to &V%s" % (Username, Rank.capitalize()))

class BanCmd(CommandObject):
    '''Ban command handler. Bans a username (permanently)'''
    def Run(self, pPlayer, Args, Message):
        Username = Args[0]
        if pPlayer.ServerControl.GetRankLevel(pPlayer.ServerControl.GetRank(Username)) >= pPlayer.GetRankLevel():
            pPlayer.SendMessage("&RYou may not ban someone with the same rank or higher than yours")
            return
        if len(Args) == 1:
            pPlayer.SendMessage("&RBans require a duration. Eg: /ban joe 1day. 0 for permanent")
            return
        Duration = Args[1]
        Timespan = ''
        if Duration != '0':
            try:
                Duration = ParseWordAsTime(Args[1])
            except:
                pPlayer.SendMessage("&RThat is an invalid timespan. Eg: 1d2h for 1 day and 2 hours")
                return
            Timespan = ElapsedTime(Duration)
            Duration += int(pPlayer.ServerControl.Now)
        else:
            Duration = 0
            Timespan = 'permanent'
        
        Result = pPlayer.ServerControl.AddBan(pPlayer.GetName(), Username, Duration)
        if Result:
            pPlayer.ServerControl.SendNotice("%s was banned by %s" % (Username, pPlayer.GetName()))
        pPlayer.SendMessage("&SSuccessfully banned &V%s&S. Duration: &V%s" % (Username, Timespan))

class UnbanCmd(CommandObject):
    '''Unban command handler. Removes a ban for a username'''
    def Run(self, pPlayer, Args, Message):
        Username = Args[0]
        Result = pPlayer.ServerControl.Unban(Username)
        if Result:
            pPlayer.SendMessage("&SSuccessfully unbanned &V%s" % (Username))
        else:
            pPlayer.SendMessage("&RThat user was not banned!")

class KickCmd(CommandObject):
    '''Kick command handler. Kicks a user from the server'''
    def Run(self, pPlayer, Args, Message):
        Username = Args[0]
        ReasonTokens = Args[1:]
        if pPlayer.ServerControl.GetRankLevel(pPlayer.ServerControl.GetRank(Username)) >= pPlayer.GetRankLevel():
            pPlayer.SendMessage("&RYou may not kick someone with the same rank or higher than yours")
            return
        Reason = ''
        for Token in ReasonTokens:
            Reason += Token + ' '

        if Reason == '':
            Reason = "(No reason given)"

        Result = pPlayer.ServerControl.Kick(pPlayer.GetName(), Username, Reason)
        if Result:
            pPlayer.SendMessage("&SSuccessfully kicked &V%s" % (Username))
        else:
            pPlayer.SendMessage("&RThat user is not online!")

class MuteCmd(CommandObject):
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name)
        self.Aliases = set(["unmute"])
        
    '''Mutes a player from talking'''
    def Run(self, pPlayer, Args, Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target is not None:
            if Target.IsMuted == False:
                Target.IsMuted = True
                Target.SendMessage("&SYou have been temporarily muted")
                pPlayer.SendMessage("&SYou have temporarily muted \"&V%s&S\"" % Target.GetName())
            else:
                Target.IsMuted = False
                Target.SendMessage("&SYou are no longer muted.")
                pPlayer.SendMessage("&S\"&V%s&S\" is no longer muted" % Target.GetName())
        else:
            pPlayer.SendMessage("&RThat player is not online!")


class FreezeCmd(CommandObject):
    '''Freezes a player in place'''
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name)
        self.Aliases = set(["unfreeze", "defreeze"])
        
    def Run(self, pPlayer, Args, Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target is not None:
            if Target.IsFrozen == False:
                Target.IsFrozen = True
                Target.SendMessage("&SYou have been frozen in place by \"&V%s&S\"" % pPlayer.GetName())
                pPlayer.SendMessage("&SYou have frozen \"&V%s&S\" in place" % Target.GetName())
            else:
                Target.IsFrozen = False
                Target.SendMessage("&SYou are no longer frozen.")
                pPlayer.SendMessage("&S\"&V%s&S\" is no longer frozen" % Target.GetName())
        else:
            pPlayer.SendMessage("&RThat player is not online!")

class SummonCmd(CommandObject):
    '''Summon command handler. Teleports specified player to user location'''
    def Run(self, pPlayer, Args, Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target is not None and Target.GetWorld() is not None and Target.CanBeSeenBy(pPlayer):
            if pPlayer.GetWorld() != Target.GetWorld():
                if pPlayer.GetWorld().IsFull():
                    pPlayer.SendMessage("&RSummon failed. Your world is full.")
                    return
                Target.SetSpawnPosition(pPlayer.GetX(), pPlayer.GetY(), pPlayer.GetZ(), pPlayer.GetOrientation(), pPlayer.GetPitch())
                Target.ChangeWorld(pPlayer.GetWorld().Name)
            else:
                Target.Teleport(pPlayer.GetX(), pPlayer.GetY(), pPlayer.GetZ(), pPlayer.GetOrientation(), pPlayer.GetPitch())
            pPlayer.SendMessage("&SSuccessfully summoned %s" % Target.GetName())
        else:
            pPlayer.SendMessage("&RThat player is not online!")
                          
class UndoActionsCmd(CommandObject):
    '''Handle for the /UndoActions command - revereses all the block changes by a player for X seconds'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.GetWorld().LogBlocks == False:
            pPlayer.SendMessage("&RBlock logging is not enabled!")
            return

        ReversePlayer = Args[0]
        Time = Args[1]
        try:
            Time = int(Time)
        except:
            pPlayer.SendMessage("&RThat is not a valid number of seconds")
            return
        if Time < 0:
            pPlayer.SendMessage("&RThat is not a valid number of seconds")
            return
        pPlayer.GetWorld().UndoActions(pPlayer.GetName(), ReversePlayer, Time)

        pPlayer.SendMessage("&S%s actions are being reversed. This may take a few moments" % ReversePlayer)

    def LogCommand(self, pPlayer, Command, Args):
        '''Override the default log handler'''
        TimeFormat = time.strftime("%d %b %Y [%H:%M:%S]", time.localtime())
        OutStr = "%s User %s (%s) used command %s on world %s with args: %s\n" % (TimeFormat, pPlayer.GetName(), pPlayer.GetIP(), Command, pPlayer.GetWorld().Name, ' '.join(Args))
        self.CmdHandler.LogFile.write(OutStr)

class InvisibleCmd(CommandObject):
    '''Handles the /invisible command'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.IsInvisible():
            pPlayer.SetInvisible(False)
            pPlayer.SendMessage("&SYou are no longer invisible")
        else:
            pPlayer.SetInvisible(True)
            pPlayer.SendMessage("&SYou are now invisible to all users with a lower rank than yours.")
######################
#ADMIN COMMANDS HERE #
######################
class SaveCmd(CommandObject):
    '''Handle for the /save command - saves all running worlds'''
    def Run(self, pPlayer, Args, Message):
        pPlayer.ServerControl.SaveAllWorlds()
        pPlayer.SendMessage("&SSaved all worlds successfully")
class BackupCmd(CommandObject):
    '''Handle for the /backup command - backs up all running worlds'''
    def Run(self, pPlayer, Args, Message):
        pPlayer.ServerControl.BackupAllWorlds()
        pPlayer.SendMessage("&SBacked up all worlds successfully")

class SetSpawnCmd(CommandObject):
    '''Handle for the /setspawn command - moves the default spawnpoint to the location you are at'''
    def Run(self, pPlayer, Args, Message):
        pPlayer.GetWorld().SetSpawn(pPlayer.GetX(), pPlayer.GetY(), pPlayer.GetZ(), pPlayer.GetOrientation(), 0)
        pPlayer.SendMessage("&SThis worlds spawnpoint has been moved")

class ServerSayCmd(CommandObject):
    '''Handler for the /serversay command. Announces a message to the server'''
    def Run(self, pPlayer, Args, Message):
        pPlayer.ServerControl.SendChatMessage("", ' '.join(Args), NormalStart = False)
        pPlayer.SendMessage("&SMessage sent.")

class AddIPBanCmd(CommandObject):
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        CommandObject.__init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name)
        self.Aliases = set(["addipban"])
        
    '''Handler for the /ipban command. Bans an IP Address from the server'''
    def Run(self, pPlayer, Args, Message):
        Arg = Args[0]
        if len(Args) == 1:
            pPlayer.SendMessage("&RBans require a duration. Eg: /ban joe 1day. 0 for permanent")
            return        
        Duration = Args[1]
        Timespan = ''
        if Duration != '0':
            try:
                Duration = ParseWordAsTime(Args[1])
            except:
                pPlayer.SendMessage("&RThat is an invalid timespan. Eg: 1d2h for 1 day and 2 hours")
                return
            Timespan = ElapsedTime(Duration)
            Duration += int(pPlayer.ServerControl.Now)
        else:
            Timespan = 'permanent'
            Duration = 0        
        #Check to see if this is a user...
        Target = pPlayer.ServerControl.GetPlayerFromName(Arg)
        if Target is not None:
            if Target.GetRankLevel() >= pPlayer.GetRankLevel():
                pPlayer.SendMessage("&RYou may not ban that user.")
                return
            pPlayer.ServerControl.AddBan(pPlayer.GetName(), Arg, Duration)
            pPlayer.SendMessage("&SSuccessfully added username ban on \"&V%s&S\". Duration: &V%s" % (Arg, Timespan))
            #Set arg to the IP address so we can ban that too.
            Arg = Target.GetIP()
        #Check if IP is legit. If so, ban it.
        Parts = Arg.split(".")
        if len(Parts) != 4:
            pPlayer.SendMessage("&RThat is not a valid ip-address!")
            return
        try:   
            for Byte in Parts:
                Byte = int(Byte)
                assert(Byte >= 0 and Byte <= 255)
        except:
            pPlayer.SendMessage("&RThat is not a valid ip-address!")
            return
        
        
        #Check to see it wont affect anyone of higher rank than us currently connected.
        for aPlayer in pPlayer.ServerControl.PlayerSet:
            if aPlayer.GetIP() == Arg and aPlayer.GetRankLevel() >= pPlayer.GetRankLevel():
                pPlayer.SendMessage("&RYou may not ban that user.")
                return
        pPlayer.ServerControl.AddIPBan(pPlayer.GetName(), Arg, Duration)
        pPlayer.SendMessage("&SSuccessfully banned ip \"&V%s\"&S. Duration: &V%s" % (Arg, Timespan))

class DelIPBanCmd(CommandObject):
    '''Handler for the /delipban command. Removes an IP Address ban'''
    def Run(self, pPlayer, Args, Message):
        Arg = Args[0]
        #Verify this is a valid IP.
        Parts = Arg.split(".")
        if len(Parts) != 4:
            pPlayer.SendMessage("&RThat is not a valid ip-address!")
            return
        try:
            for Byte in Parts:
                Byte = int(Byte)
                assert(Byte >= 0 and Byte <= 255)
        except:
            pPlayer.SendMessage("&RThat is not a valid ip-address!")
            return
        
        if pPlayer.ServerControl.UnbanIP(Arg):
            pPlayer.SendMessage("&SRemoved ban on ip \"&V%s&S\"" % Arg)
        else:
            pPlayer.SendMessage("&RThat IP is not banned!")
        

class WorldSetBuildRankCmd(CommandObject):
    '''Sets the mimimum rank required to build on a world'''
    def Run(self, pPlayer, Args, Message):
        WorldName = Args[0].lower()
        Rank = Args[1]
        if pPlayer.ServerControl.IsValidRank(Rank) == False:
            pPlayer.SendMessage("&RThat is not a valid rank! Valid ranks:&V %s" % pPlayer.ServerControl.GetExampleRanks())
            return
        if pPlayer.ServerControl.WorldExists(WorldName):
            pPlayer.ServerControl.SetWorldBuildRank(WorldName, Rank.lower())
            pPlayer.SendMessage("&SWorld \"&V%s&S\" minimum build rank is now &V%s" % (WorldName, Rank))
        else:
            pPlayer.SendMessage("&RThat world does not exist!")

class WorldSetAccessRankCmd(CommandObject):
    '''Sets the mimimum rank required to join a world'''
    def Run(self, pPlayer, Args, Message):
        WorldName = Args[0].lower()
        Rank = Args[1]
        if pPlayer.ServerControl.IsValidRank(Rank) == False:
            pPlayer.SendMessage("&RThat is not a valid rank! Valid ranks:&V %s" % pPlayer.ServerControl.GetExampleRanks())
            return
        if pPlayer.ServerControl.WorldExists(WorldName):
            pPlayer.ServerControl.SetWorldJoinRank(WorldName, Rank.lower())
            pPlayer.SendMessage("&SWorld \"&V%s&S\" minimum join rank is now &V%s" % (WorldName, Rank))
        else:
            pPlayer.SendMessage("&RThat world does not exist!")

            
class TempOpCmd(CommandObject):
    '''Handle for the /tempop command - gives a username temporary operator status'''
    def Run(self, pPlayer, Args, Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target is None:
            pPlayer.SendMessage("&RThat player is not online!")
            return
        if Target.GetRankLevel() > pPlayer.ServerControl.GetRankLevel('operator'):
            pPlayer.SendMessage("&RYou may not set that players rank!")
            return
        Target.SetRank('operator')
        Target.SendMessage("&SYou have been granted temporary operator privlidges by &V%s" % pPlayer.GetName())
        pPlayer.SendMessage("&V%s &Sis now a temporary operator" % Username)


class CreateWorldCmd(CommandObject):
    '''Handles the world cretion command'''
    def Run(self, pPlayer, Args, Message):
        Name = Args[0]
        if Name.isalnum() == False:
            pPlayer.SendMessage("&RThat is not a valid name!")
            return
        X = Args[1]
        Y = Args[2]
        Z = Args[3]
        try:
            X = int(X)
            Y = int(Y)
            Z = int(Z)
            if X <= 0 or Y <= 0 or Z <= 0:
                raise Exception()
        except:
            pPlayer.SendMessage("&RPlease enter valid length, width, and height coordinates!")
            return
        try:
            assert(X % 16 == 0)
            assert(Y % 16 == 0)
            assert(Z % 16 == 0)
        except AssertionError:
            pPlayer.SendMessage("&RYour length, width and height coordinates need to be a multiple of 16")
            return
        if pPlayer.ServerControl.WorldExists(Name):
            pPlayer.SendMessage("&RThat world already exists!")
            return
        pWorld = World(pPlayer.ServerControl, Name, True, X, Y, Z)
        pPlayer.ServerControl.ActiveWorlds.append(pWorld)
        pWorld.SetIdleTimeout(pPlayer.ServerControl.WorldTimeout)
        pPlayer.SendMessage("&SSuccessfully created world \"&V%s&S\"" % Name)

class LoadWorldCmd(CommandObject):
    '''Handler for the /worldload command'''
    def Run(self, pPlayer, Args, Message):
        WorldName = Args[0]
        if os.path.isfile("Worlds/%s.save" % WorldName) == False:
            pPlayer.SendMessage("&RThat world doesn't exist. Check that you spelt it correctly")
            return
        if pPlayer.ServerControl.WorldExists(WorldName):
            pPlayer.SendMessage("&RThat world is already loaded!")
            return
        pPlayer.ServerControl.AddWorld(WorldName)
        pPlayer.SendMessage("&SSuccessfully loaded world \"&V%s&S\"!" % WorldName)
        
class LoadTemplateCmd(CommandObject):
    '''Handler for the /loadtemplate command'''
    def Run(self, pPlayer, Args, Message):
        TemplateName = Args[0]
        WorldName = Args[1]
        if os.path.isfile("Templates/%s.save" % TemplateName) == False:
            pPlayer.SendMessage("&RThat template doesn't exist. Check that you spelt it correctly")
            return
        if pPlayer.ServerControl.WorldExists(WorldName):
            pPlayer.SendMessage("&RA world with that name already exists!")
            return
        shutil.copy("Templates/%s.save" % TemplateName, "Worlds/%s.save" % WorldName)
        pPlayer.ServerControl.AddWorld(WorldName)
        pPlayer.ServerControl.WorldMetaDataCache[WorldName.lower()][MetaDataKey.CreationDate] = int(time.time())
        pPlayer.SendMessage("&SSuccessfully loaded template \"&V%s&S\"!" % TemplateName)
        
class ShowTemplatesCmd(CommandObject):
    '''Handler for the /showtemplates command'''
    def Run(self, pPlayer, Args, Message):
        OutStr = bytearray()
        for File in os.listdir("Templates"):
            if File.endswith(".save") == False:
                continue
            TemplateName = File[:-5]
            OutStr += TemplateName
            OutStr += ' '
            
        OutStr = str(OutStr)
        if OutStr != '':
            pPlayer.SendMessage("&SThe following templates exist:")
            pPlayer.SendMessage("&S%s" % OutStr)
        else:
            pPlayer.SendMessage("&SThere are no templates!")
            
class MakeTemplateCmd(CommandObject):
    '''Handler for the /maketemplate command'''
    def Run(self, pPlayer, Args, Message):
        WorldName = Args[0]
        TemplateName = Args[1]
        if TemplateName.isalnum() == False:
            pPlayer.SendMessage("&RInvalid name for the template!")
            return
        
        if os.path.isfile("Templates/%s.save" % TemplateName):
            pPlayer.SendMessage("&RA template with that name already exists!")
            return
        
        if pPlayer.ServerControl.WorldExists(WorldName) == False:
            pPlayer.SendMessage("&RThat world does not exist!")
            return
        
        pWorld = pPlayer.ServerControl.GetActiveWorld(WorldName)
        if pWorld is not None:
            #Make sure the file on disk is the most up to date (blocking)
            pWorld.Save()
            pWorld.CurrentSaveThread.join()
        try:
            shutil.copy("Worlds/%s.save" % WorldName, "Templates/%s.save" % TemplateName)
        except Exception, e:
            pPlayer.SendMessage("&RFailed to make template. Error: %s" % e)
        else:
            pPlayer.SendMessage("&SSuccessfully created template")
            
class DeleteTemplateCmd(CommandObject):
    def Run(self, pPlayer, Args, Message):
        TemplateName = Args[0]
        if os.path.isfile("Templates/%s.save" % TemplateName) == False:
            pPlayer.SendMessage("&RThat template does not exist!")
            return
        try:
            os.remove("Templates/%s.save" % TemplateName)
        except Exception, e:
            pPlayer.SendMessage("&RCould not remove: %s" % e)
        else:
            pPlayer.SendMessage("&SSuccessfully deleted template")
        
class SetDefaultWorldCmd(CommandObject):
    '''Handler for the /setdefaultworld command'''
    def Run(self, pPlayer, Args, Message):
        WorldName = Args[0]
        pWorld = pPlayer.ServerControl.GetActiveWorld(WorldName)
        if pWorld is None:
            pPlayer.SendMessage("&RCould not set world to default world.")
            pPlayer.SendMessage("&RTry joining the world and trying again.")
            return
        pPlayer.ServerControl.SetDefaultWorld(pWorld)
        pPlayer.SendMessage("&SDefault world changed to &V\"%s\"" % pWorld.Name)
        
class HideWorldCmd(CommandObject):
    '''Handler for the /hideworld command'''
    def Run(self, pPlayer, Args, Message):
        WorldName = Args[0]
        if pPlayer.ServerControl.WorldExists(WorldName):
            pPlayer.ServerControl.SetWorldHidden(WorldName, True)
            pPlayer.SendMessage("&SWorld \"&V%s&S\" is now being hidden" % WorldName)
        else:
            pPlayer.SendMessage("&RThat world does not exist!")

class UnHideWorldCmd(CommandObject):
    '''Handler for the /unhideworld command'''
    def Run(self, pPlayer, Args, Message):
        WorldName = Args[0]
        if pPlayer.ServerControl.WorldExists(WorldName):
            pPlayer.ServerControl.SetWorldHidden(WorldName, False)
            pPlayer.SendMessage("&SWorld \"&V%s&S\" is no long hidden" % WorldName)
        else:
            pPlayer.SendMessage("&RThat world does not exist!")


class RenameWorldCmd(CommandObject):
    '''Handler for the /renameworld command'''
    def Run(self, pPlayer, Args, Message):
        OldName = Args[0].lower()
        NewName = Args[1]
        if NewName.isalnum() == False:
            pPlayer.SendMessage("&RThat is not a valid name!")
            return
        if pPlayer.ServerControl.WorldExists(OldName) == False:
            pPlayer.SendMessage("&RThat world does not exist!")
            return
        if pPlayer.ServerControl.WorldExists(NewName):
            pPlayer.SendMessage("&RThere is already a world with that name!")
            return
        try:
            pPlayer.ServerControl.RenameWorld(OldName, NewName)
            pPlayer.SendMessage("&SSuccessfully renamed map %s to %s" % (OldName, NewName))
        except Exception, e:
            pPlayer.SendMessage("&RFailed to rename world. Error: %s" % e)
            

class PluginCmd(CommandObject):
    '''Handler for the /plugins command'''
    def Run(self, pPlayer, Args, Message):
        Args = [Arg.lower() for Arg in Args]
        if Args[0] == "list":
            self.ListPlugins(pPlayer, Args)
        elif Args[0] == "load":
            self.LoadPlugin(pPlayer, Args)
        elif Args[0] == "unload":
            self.UnloadPlugin(pPlayer, Args)
        elif Args[0] == "reload":
            if len(Args) == 1:
                pPlayer.SendMessage("&RSpecify the name of the plugin you want to reload!")
                return
            self.UnloadPlugin(pPlayer, Args)
            self.LoadPlugin(pPlayer, Args)
        else:
            pPlayer.SendMessage("&RUnrecognized command. Valid commands are /plugins <list, load, unload, reload>")

    def ListPlugins(self, pPlayer, Args):
        if len(pPlayer.ServerControl.PluginMgr.PluginModules) == 0:
            pPlayer.SendMessage("&SThere are no plugins currently loaded!")
            return
        pPlayer.SendMessage("&SThe following plugins are currently loaded:")
        for pPlugin in pPlayer.ServerControl.PluginMgr.PluginModules:
            pPlayer.SendMessage("&SPlugin: &V%s" % pPlugin)

    def LoadPlugin(self, pPlayer, Args):
        if len(Args) == 1:
            pPlayer.SendMessage("&RSpecify the name of the plugin you want to load!")
            return
        PluginName = Args[1]
        if PluginName in pPlayer.ServerControl.PluginMgr.PluginModules:
            pPlayer.SendMessage("&RThat plugin is already loaded!")
            return
        Result = pPlayer.ServerControl.PluginMgr.LoadPlugin(PluginName)
        if Result:
            pPlayer.SendMessage("&SSuccessfully loaded plugin \"&V%s&S\"" % PluginName)
        else:
            pPlayer.SendMessage("&RUnable to load plugin \"%s\"" % PluginName)

    def UnloadPlugin(self, pPlayer, Args):
        if len(Args) == 1:
            pPlayer.SendMessage("&RSpecify the name of the plugin you want to unload!")
            return
        PluginName = Args[1]
        if PluginName not in pPlayer.ServerControl.PluginMgr.PluginModules:
            pPlayer.SendMessage("&RThat plugin is not loaded!")
            return
        Result = pPlayer.ServerControl.PluginMgr.UnloadPlugin(PluginName)
        if Result:
            pPlayer.SendMessage("&SSuccessfully unloaded plugin \"&V%s&S\"" % PluginName)
        else:
            pPlayer.SendMessage("&RUnable to unload plugin \"%s\"" % PluginName)

######################
#OWNER COMMANDS HERE #
######################

class FlushBlockLogCmd(CommandObject):
    '''Flushes the worlds blocklog to disk'''
    def Run(self, pPlayer, Args, Message):
        pPlayer.GetWorld().FlushBlockLog()
        pPlayer.SendMessage("&SWorld %s's Blocklog has been flushed to disk." % pPlayer.GetWorld().Name)
        
class DeleteWorldCmd(CommandObject):
    '''Deletes a world from the server'''
    def Run(self, pPlayer, Args, Message):
        WorldName = Args[0].lower()
        if pPlayer.ServerControl.WorldExists(WorldName) == False:
            pPlayer.SendMessage("&RThat world does not exist!")
            return
        #Is it an idle world? (Easy)
        ActiveWorlds, IdleWorlds = pPlayer.ServerControl.GetWorlds()
        if ActiveWorlds[0].Name.lower() == WorldName:
            pPlayer.SendMessage("&RYou cannot delete the default world!")
            return
        
        try:
            pPlayer.ServerControl.DeleteWorld(WorldName)
            pPlayer.SendMessage("&SSuccessfully deleted world \"&V%s&S\"" % WorldName)
        except Exception, e:
            pPlayer.SendMessage("&RFailed to erase world. Error: %s" % e)

class WorldSummonCmd(CommandObject):
    '''Summons all players on your world to you'''
    def Run(self, pPlayer, Args, Message):
        for Target in pPlayer.GetWorld().Players:
            Target.Teleport(pPlayer.GetX(), pPlayer.GetY(), pPlayer.GetZ(), pPlayer.GetOrientation(), pPlayer.GetPitch())
            
        pPlayer.SendMessage("&SEveryone on your world has been summoned to you.")
        
class MassSummonCmd(CommandObject):
    '''Summons everyone on the server to your position, or until the world is full'''
    def Run(self, pPlayer, Args, Message):
        for Target in pPlayer.ServerControl.PlayerSet:
            if Target.GetWorld() is not None:
                if Target.GetWorld() == pPlayer.GetWorld():
                    Target.Teleport(pPlayer.GetX(), pPlayer.GetY(), pPlayer.GetZ(), pPlayer.GetOrientation(), pPlayer.GetPitch())
                else:
                    if pPlayer.GetWorld().IsFull():
                        pPlayer.SendMessage("&SSummon completed. Ran out of space on your world.")
                        return
                    else:
                        Target.SetSpawnPosition(pPlayer.GetX(), pPlayer.GetY(), pPlayer.GetZ(), pPlayer.GetOrientation(), pPlayer.GetPitch())
                        Target.ChangeWorld(pPlayer.GetWorld().Name)
                        
        pPlayer.SendMessage("&SMass summon completed.")    


class SolidCmd(CommandObject):
    '''Command handler for /solid command. Replaces all block placed with adminium/admincrete'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.GetBlockOverride() == BLOCK_HARDROCK:
            pPlayer.SendMessage("&SYou are no longer placing adminium")
            pPlayer.SetBlockOverride(-1)
            return
        else:
            pPlayer.SetBlockOverride(BLOCK_HARDROCK)
            pPlayer.SendMessage("&SEvery block you create will now be adminium. Type /solid to disable.")

class WaterCmd(CommandObject):
    '''Command handler for /water command. Replaces all block placed with water'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.GetBlockOverride() == BLOCK_STILLWATER:
            pPlayer.SendMessage("&SYou are no longer placing water")
            pPlayer.SetBlockOverride(-1)
            return
        else:
            pPlayer.SetBlockOverride(BLOCK_STILLWATER)
            pPlayer.SendMessage("&SEvery block you create will now be water. Type /water to disable.")

class LavaCmd(CommandObject):
    '''Command handler for /lava command. Replaces all block placed with lava'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.GetBlockOverride() == BLOCK_STILLLAVA:
            pPlayer.SendMessage("&SYou are no longer placing lava")
            pPlayer.SetBlockOverride(-1)
            return
        else:
            pPlayer.SetBlockOverride(BLOCK_STILLLAVA)
            pPlayer.SendMessage("&SEvery block you create will now be lava. Type /lava to disable.")
