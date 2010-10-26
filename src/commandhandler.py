'''Command system for opticraft'''
from constants import *
from ordereddict import OrderedDict
class CommandObject(object):
    '''Child class for all commands'''
    def __init__(self,CmdHandler,Permissions,HelpMsg,ErrorMsg,MinArgs,Alias = False):
        self.Permissions = Permissions
        self.HelpMsg = HelpMsg
        self.ErrorMsg = ErrorMsg
        self.MinArgs = MinArgs
        self.CmdHandler = CmdHandler
        self.IsAlias = Alias

    def Execute(self,pPlayer,Message):
        '''Checks player has correct permissions and number of arguments'''
        if self.Permissions != '':
            if pPlayer.HasPermission(self.Permissions) == False:
                pPlayer.SendMessage("&4You do not have the required permissions to use that command!")
                return
        Tokens = Message.split()
        Args = len(Tokens)-1
        if Args < self.MinArgs:
            pPlayer.SendMessage(self.ErrorMsg)
            return
        else:
            self.Run(pPlayer,Message.split()[1:],Message)

    def Run(self,pPlayer,Args,Message):
        '''Subclasses will perform their work here'''
        pass
######################
#PUBLIC COMMANDS HERE#
######################
class CmdListCmd(CommandObject):
    '''Handle for the /cmdlist command'''
    def Run(self,pPlayer,Args,Message):
        Commands = ''
        for key in self.CmdHandler.CommandTable:
            CmdObj = self.CmdHandler.CommandTable[key]
            if CmdObj.IsAlias == True:
                continue
            if CmdObj.Permissions != '':
                if pPlayer.HasPermission(CmdObj.Permissions) == False:
                    continue #Don't send commands to the client if he doesn't possess the permission to use it!

            Commands += key + ' '
        pPlayer.SendMessage("&aAvailable commands:")
        pPlayer.SendMessage("&a" + Commands)

class GrassCmd(CommandObject):
    '''Command handler for /grass command. Replaces all block placed with grass'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetBlockOverride() == BLOCK_GRASS:
            pPlayer.SendMessage("You are no longer placing grass")
            pPlayer.SetBlockOverride(-1)
            return
        else:
            pPlayer.SetBlockOverride(BLOCK_GRASS)
            pPlayer.SendMessage("Every block you create will now be grass. Type /grass to disable.")

class HelpCmd(CommandObject):
    '''Returns a helpful message about a command'''
    def Run(self,pPlayer,Args,Message):
        if self.CmdHandler.CommandTable.has_key(Args[0].lower()) == False:
            pPlayer.SendMessage("&4" + "That command does not exist!")
            return
        else:
            CmdObj = self.CmdHandler.CommandTable[Args[0].lower()]
            pPlayer.SendMessage("&e" + CmdObj.HelpMsg)

class AboutCmd(CommandObject):
    '''The next block a player destroys/creates will display the blocks infromation'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.World.LogBlocks == True:
            pPlayer.SetAboutCmd(True)
            pPlayer.SendMessage("Place/destroy a block to see what was there before")
        else:
            pPlayer.SendMessage("Block history is disabled")

class JoinWorldCmd(CommandObject):
    '''Handler for the /join command. Changes the players world'''
    def Run(self,pPlayer,Args,Message):
        World = Args[0]
        if pPlayer.ServerControl.WorldExists(World) == False:
            pPlayer.SendMessage("&4That world does not exist!")
            return
        if pPlayer.GetWorld().Name.lower() == World.lower():
            pPlayer.SendMessage("&4You are already on that world!")
            return
        pPlayer.ChangeWorld(World)
class WorldsCmd(CommandObject):
    '''Handler for the /worlds command. Lists all available worlds.'''
    def Run(self,pPlayer,Args,Message):
        ActiveWorlds, IdleWorlds = pPlayer.ServerControl.GetWorlds()
        OutString = str('&a')
        pPlayer.SendMessage("&aThe following worlds are available:")
        for pWorld in ActiveWorlds:
            OutString += pWorld.Name + ' '
        for WorldName in IdleWorlds:
            OutString += WorldName + ' '
        pPlayer.SendMessage(OutString)
########################
#BUILDER COMMANDS HERE #
########################
class WaterCmd(CommandObject):
    '''Command handler for /water command. Replaces all block placed with water'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetBlockOverride() == BLOCK_STILLWATER:
            pPlayer.SendMessage("You are no longer placing water")
            pPlayer.SetBlockOverride(-1)
            return
        else:
            pPlayer.SetBlockOverride(BLOCK_STILLWATER)
            pPlayer.SendMessage("Every block you create will now be water. Type /water to disable.")

class LavaCmd(CommandObject):
    '''Command handler for /lava command. Replaces all block placed with lava'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetBlockOverride() == BLOCK_STILLLAVA:
            pPlayer.SendMessage("You are no longer placing lava")
            pPlayer.SetBlockOverride(-1)
            return
        else:
            pPlayer.SetBlockOverride(BLOCK_STILLLAVA)
            pPlayer.SendMessage("Every block you create will now be lava. Type /lava to disable.")

class AppearCmd(CommandObject):
    '''Appear command handler. Teleports user to specified players location'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target != None:
            if pPlayer.GetWorld() != Target.GetWorld():
                pPlayer.SendMessage("&4That player is not on your world. Cannot teleport to them!")
                return
            pPlayer.Teleport(Target.GetX(),Target.GetY(),Target.GetZ(),Target.GetOrientation(),Target.GetPitch())
        else:
            pPlayer.SendMessage("&4That player is not online!")

class ZoneInfoCmd(CommandObject):
    '''Zone info command handler. Returns information on a zone'''
    def Run(self,pPlayer,Args,Message):
        Name = Args[0]
        pZone = pPlayer.GetWorld().GetZone(Name)
        if pZone == None:
            pPlayer.SendMessage("&4No such zone exists on this map")
            return
        pPlayer.SendMessage("&aOwner:&e %s" %pZone.Owner)
        pPlayer.SendMessage("&aMinimum rank:&e %s" %RankToName[pZone.MinRank])
        pPlayer.SendMessage("&a---Builders---")
        Num = 0
        for Builder in pZone.Builders:
            pPlayer.SendMessage(Builder)
            Num += 1
        if Num == 0:
            pPlayer.SendMessage("This zone has no builders")
class ZoneListCmd(CommandObject):
    '''Zone list command handler. Lists all zones on a map'''
    def Run(self,pPlayer,Args,Message):
        Zones = pPlayer.GetWorld().GetZones()
        ZoneNames = str("&a")
        for pZone in Zones:
            ZoneNames += pZone.Name + ' '
        if len(Zones) > 0:
            pPlayer.SendMessage("&aThe following zones are active on this map:")
            pPlayer.SendMessage(ZoneNames)
        else:
            pPlayer.SendMessage("&aThis map has no zones!")

class AddZoneBuilderCmd(CommandObject):
    '''Add zone builder handler. This adds a builder to a zone'''
    def Run(self,pPlayer,Args,Message):
        ZoneName = Args[0]
        Username = Args[1]
        pZone = pPlayer.GetWorld().GetZone(ZoneName)
        if pZone == None:
            pPlayer.SendMessage("&4No such zone exists on this map")
            return
        if pPlayer.GetName().lower() != pZone.Owner.lower():
            if pPlayer.HasPermission('z') == False:
                pPlayer.SendMessage("&4You are not allowed to delete builders from this zone!")
                return
        Username = Username.lower()
        if Username in pZone.Builders:
            pPlayer.SendMessage("&4That user is already a builder for this zone!")
            return
        pZone.AddBuilder(Username)
        pPlayer.SendMessage("&aSuccessfully added&f %s&a as a builder for zone&f \"%s\"" %(Username,pZone.Name))
        if pPlayer.ServerControl.GetPlayerFromName(Username) != None:
            pPlayer.ServerControl.GetPlayerFromName(Username).SendMessage("&aYou have been added as a builder to zone&f %s" %pZone.Name)
class DelZoneBuilderCmd(CommandObject):
    '''Del zone builder handler. This deletes a builder from a zone'''
    def Run(self,pPlayer,Args,Message):
        ZoneName = Args[0]
        Username = Args[1]
        pZone = pPlayer.GetWorld().GetZone(ZoneName)
        if pZone == None:
            pPlayer.SendMessage("&4No such zone exists on this map")
            return
        if pPlayer.GetName().lower() != pZone.Owner.lower():
            if pPlayer.HasPermission('z') == False:
                pPlayer.SendMessage("&4You are not allowed to delete builders from this zone!")
                return
        Username = Username.lower()
        if Username not in pZone.Builders:
            pPlayer.SendMessage("&4That user is not a builder for this zone!")
            return
        pZone.DelBuilder(Username)
        pPlayer.SendMessage("&aSuccessfully removed %s as a builder for zone&f \"%s\"" %(Username,pZone.Name))
        if pPlayer.ServerControl.GetPlayerFromName(Username) != None:
            pPlayer.ServerControl.GetPlayerFromName(Username).SendMessage("&aYou have been removed as a builder from zone&f \"%s\"" %pZone.Name)

class zSetMinRankCmd(CommandObject):
    '''Handler for the zSetMinRank command. Changes the minimum rank to build in a zone'''
    def Run(self,pPlayer,Args,Message):
        ZoneName = Args[0]
        Rank = Args[1]
        Rank = Rank.lower()
        if Rank not in ["a","o","b","z"]:
            pPlayer.SendMessage("&4Invalid rank! Valid ranks are: b, o, a, z")
            return
        pZone = pPlayer.GetWorld().GetZone(ZoneName)
        if pZone == None:
            pPlayer.SendMessage("&4No such zone exists on this map")
            return
        if pPlayer.GetName().lower() != pZone.Owner.lower():
            if pPlayer.HasPermission('z') == False:
                pPlayer.SendMessage("&4You are not allowed to change the minimum rank required in this zone!")
                return
        pZone.SetMinRank(Rank)
        pPlayer.SendMessage("&aMinimum non-builder ranked required to build in zone \"%s\" is now %s" %(pZone.Name,RankToName[Rank]))

class zChangeOwnerCmd(CommandObject):
    '''zChangeOwner command handler. This changes the owner of a zone'''
    def Run(self,pPlayer,Args,Message):
        ZoneName = Args[0]
        Username = Args[1]
        pZone = pPlayer.GetWorld().GetZone(ZoneName)
        if pZone == None:
            pPlayer.SendMessage("&4No such zone exists on this map")
            return
        if pPlayer.GetName().lower() != pZone.Owner.lower():
            if pPlayer.HasPermission('z') == False:
                pPlayer.SendMessage("&4You are not allowed to change this zones owner!")
                return
        Username = Username.lower()
        pZone.ChangeOwner(Username)
        pPlayer.SendMessage("&aSuccessfully changed the owner of zone&f \"%s\"&a to &f%s" %(pZone.Name,Username))
        if pPlayer.ServerControl.GetPlayerFromName(Username) != None:
            pPlayer.ServerControl.GetPlayerFromName(Username).SendMessage("&aYou have been set as the owner of zone&f \"%s\"" %pZone.Name)

#########################
#OPERATOR COMMANDS HERE #
#########################
class BanCmd(CommandObject):
    '''Ban command handler. Bans a username (permanently)'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        if ":" in Username:
            pPlayer.SendMessage("&4That is not a valid username!")
            return
        if RankToLevel[pPlayer.ServerControl.GetRank(Username)] >= RankToLevel[pPlayer.GetRank()]:
            pPlayer.SendMessage("&4You may not ban someone with the same rank or higher then yours")
            return
        Result = pPlayer.ServerControl.AddBan(Username, 0) #TODO: Parse input so we can enter expiry!
        if Result:
            pPlayer.ServerControl.SendNotice("%s was just banned by %s" %(Username,pPlayer.GetName()))
        pPlayer.SendMessage("Successfully banned %s" %(Username))

class UnbanCmd(CommandObject):
    '''Unban command handler. Removes a ban for a username'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        Result = pPlayer.ServerControl.Unban(Username)
        if Result:
            pPlayer.SendMessage("Successfully banned %s" %(Username))
        else:
            pPlayer.SendMessage("&4That user was not banned!")

class KickCmd(CommandObject):
    '''Kick command handler. Kicks a user from the server'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        ReasonTokens = Args[1:]
        Reason = ''
        for Token in ReasonTokens:
            Reason += Token + ' '

        if Reason == '':
            Reason = "(No reason given)"

        Result = pPlayer.ServerControl.Kick(pPlayer,Username,Reason)
        if Result:
            pPlayer.SendMessage("Successfully kicked %s" %(Username))
        else:
            pPlayer.SendMessage("&4That user is not online!")

class SummonCmd(CommandObject):
    '''Summon command handler. Teleports specified player to user location'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target != None:
            if pPlayer.GetWorld() != Target.GetWorld():
                pPlayer.SendMessage("&4That player is not on your world. Cannot teleport to them!")
                return
            Target.Teleport(pPlayer.GetX(),pPlayer.GetY(),pPlayer.GetZ(),pPlayer.GetOrientation(),pPlayer.GetPitch())
            pPlayer.SendMessage("Successfully summoned %s" %Target.GetName())
        else:
            pPlayer.SendMessage("&4That player is not online!")
class UndoActionsCmd(CommandObject):
    '''Handle for the /UndoActions command - revereses all the block changes by a player for X seconds'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetWorld().LogBlocks == False:
            pPlayer.SendMessage("&4Block logging is not enabled!")
            return

        Username = Args[0]
        Time = Args[1]
        try:
            Time = int(Time)
        except:
            pPlayer.SendMessage("&4That is not a valud number of seconds")
            return
        if Time < 0:
            pPlayer.SendMessage("&4That is not a valud number of seconds")
            return
        Result = pPlayer.GetWorld().UndoActions(Username,Time)
        if Result > 0:
            self.CmdHandler.ServerControl.SendNotice("Antigrief: %s's actions have been reversed." %Username)
        else:
            pPlayer.SendMessage("&4That player has no recorded history.")

class DestroyTowerCmd(CommandObject):
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetTowerCmd():
            pPlayer.SendMessage("&aTower destruction turned off")
            pPlayer.SetTowerCmd(False)
            return
        else:
            pPlayer.SetTowerCmd(True)
            pPlayer.SendMessage("&aClick on the top-most block of the shitty tower to begin destruction")
######################
#ADMIN COMMANDS HERE #
######################
class SaveCmd(CommandObject):
    '''Handle for the /save command - saves all running worlds'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.ServerControl.SaveAllWorlds()
        pPlayer.SendMessage("Saved all worlds successfully")
class BackupCmd(CommandObject):
    '''Handle for the /backup command - backs up all running worlds'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.ServerControl.BackupAllWorlds()
        pPlayer.SendMessage("Backed up all worlds successfully")

class SetSpawnCmd(CommandObject):
    '''Handle for the /setspawn command - moves the default spawnpoint to the location you are at'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.GetWorld().SetSpawn(pPlayer.GetX(), pPlayer.GetY(), pPlayer.GetZ(), pPlayer.GetOrientation(),0)
        pPlayer.SendMessage("This worlds spawnpoint has been moved")
######################
#OWNER COMMANDS HERE #
######################
class AddRankCmd(CommandObject):
    '''Handle for the /addrank command - gives a username a rank. Can only be used by admins'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        Rank = Args[1].lower()
        PotentialRanks = ["b","o","a"]
        if Rank not in PotentialRanks:
            pPlayer.SendMessage("&4Invalid Rank! Valid ranks are: a, o, b")
            return
        pPlayer.ServerControl.SetRank(Username,Rank)
        pPlayer.SendMessage("Successfully set %s's rank to %s" %(Username,Rank))
class RemoveRankCmd(CommandObject):
    '''Handle for the /removerank command - gives a username a rank. Can only be used by admins'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        pPlayer.ServerControl.SetRank(Username,'')
        pPlayer.SendMessage("Removed %s's rank" %Username)

class PruneBlockLogCmd(CommandObject):
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetWorld().LogBlocks == False:
            pPlayer.SendMessage("&4Block logging is not enabled!")
            return
        Time = Args[0]
        try:
            Time = int(Time)
        except:
            pPlayer.SendMessage("&4That is not a valid number of seconds!")
            return
        num = pPlayer.GetWorld().PruneBlockLog(Time)
        pPlayer.SendMessage("Erased %u entry's from the block log",num)

class ZCreateCmd(CommandObject):
    def Run(self,pPlayer,Args,Message):
        Name = Args[0]
        Owner = Args[1]
        Height = Args[2]
        try:
            Height = int(Height)
        except:
            pPlayer.SendMessage("&4Height must be a valid integer")
            return
        if Height <= 0:
            pPlayer.SendMessage("&4Height must be at least 1!")
        if pPlayer.GetWorld().GetZone(Name) != None:
            pPlayer.SendMessage("&4A Zone with that name already exists!")
            return
        pPlayer.SendMessage("&aYou have started the zone creation process. Please place a block where you want the first corner of the zone to be")
        pPlayer.SendMessage("&aRemember, zones are cuboids. You will place two blocks to represent the zone")
        pPlayer.StartZone(Name,Owner,Height)
class ZDeleteCmd(CommandObject):
    '''Delete zone handler. This deletes a zone from a map'''
    def Run(self,pPlayer,Args,Message):
        ZoneName = Args[0]
        pZone = pPlayer.GetWorld().GetZone(ZoneName)
        if pZone == None:
            pPlayer.SendMessage("&4No such zone exists on this map")
            return
        pPlayer.GetWorld().DeleteZone(pZone)
        pPlayer.ServerControl.DeleteZone(pZone)
        pPlayer.SendMessage("&aSuccessfully deleted zone&f \"%s\"" %pZone.Name)
        pZone.Delete()

class CommandHandler(object):
    '''Stores all the commands avaliable on opticraft and processes any command messages'''
    def __init__(self,ServerControl):
        self.CommandTable = OrderedDict()
        self.ServerControl = ServerControl
        #Populate the command table here
        ######################
        #PUBLIC COMMANDS HERE#
        ######################
        self.AddCommand("about", AboutCmd, '', 'Displays history of a block when you destroy/create one', '', 0)
        self.AddCommand("cmdlist", CmdListCmd, '', 'Lists all commands available to you', '', 0)
        self.AddCommand("commands", CmdListCmd, '', 'Lists all commands available to you', '', 0,Alias=True)
        self.AddCommand("help", HelpCmd, '', 'Gives help on a specific command. Usage: /help <cmd>', 'Incorrect syntax! Usage: /help <cmd>', 1)
        self.AddCommand("worlds", WorldsCmd, '', 'Lists all available worlds', '', 0)
        self.AddCommand("join", JoinWorldCmd, '', 'Changes the world you are in', 'Incorrect syntax! Usage: /join <world>. Use /worlds to see a list of worlds.', 1)
        self.AddCommand("j", JoinWorldCmd, '', 'Changes the world you are in', 'Incorrect syntax! Usage: /join <world>. Use /worlds to see a list of worlds.', 1,Alias=True)
        self.AddCommand("goto", JoinWorldCmd, '', 'Changes the world you are in', 'Incorrect syntax! Usage: /join <world>. Use /worlds to see a list of worlds.', 1,Alias=True)
        self.AddCommand("grass", GrassCmd, '', 'Allows you to place grass', '', 0)
        ########################
        #BUILDER COMMANDS HERE #
        ########################
        self.AddCommand("appear", AppearCmd, 'b', 'Teleports you to a players location', 'Incorrect syntax! Usage: /appear <username>', 1)
        self.AddCommand("water", WaterCmd, 'b', 'Allows you to place water', '', 0)
        self.AddCommand("lava", LavaCmd, 'b', 'Allows you to place lava', '', 0)
        #Zone commands
        self.AddCommand("zinfo", ZoneInfoCmd, 'b', 'Returns information on a zone.', 'Incorrect syntax! Usage: /zinfo <zone>', 1)
        self.AddCommand("zlist", ZoneListCmd, 'b', 'Lists all zones on the map', '', 0)
        self.AddCommand("zaddbuilder", AddZoneBuilderCmd, 'b', 'Adds a builder to a zone', 'Incorrect syntax! Usage: /zaddbuilder <zone> <username>', 2)
        self.AddCommand("zdelbuilder", DelZoneBuilderCmd, 'b', 'Deletes a builder from a zone', 'Incorrect syntax! Usage: /zdelbuilder <zone> <username>', 2)
        self.AddCommand("zsetrank", zSetMinRankCmd, 'b', 'Changes the minimum non zone-builder rank required to build on this zone', 'Incorrect syntax! Usage: /zsetrank <zone> <rank>', 2)
        self.AddCommand("zsetowner", zChangeOwnerCmd, 'b', 'Changes the owner of a zone', 'Incorrect syntax! Usage: /zsetowner <zone> <username>', 2)

        #########################
        #OPERATOR COMMANDS HERE #
        #########################
        self.AddCommand("ban", BanCmd, 'o', 'Bans a player from the server', 'Incorrect syntax! Usage: /ban <username>', 1)
        self.AddCommand("unban", UnbanCmd, 'o', 'Unbans a player from the server', 'Incorrect syntax! Usage: /unban <username>', 1)
        self.AddCommand("kick", KickCmd, 'o', 'Kicks a player from the server', 'Incorrect syntax! Usage: /kick <username> [reason]', 1)
        self.AddCommand("summon", SummonCmd, 'o', 'Teleports a player to your location', 'Incorrect syntax! Usage: /summon <username>', 1)
        self.AddCommand("undoactions", UndoActionsCmd, 'o', 'Undoes all of a a players actions in the last X seconds', 'Incorrect Syntax! Usage: /undoactions <username> <seconds>',2)
        self.AddCommand("destroyTower",DestroyTowerCmd,'o', 'Destroys a vertical tower of shit','',0)
        ######################
        #ADMIN COMMANDS HERE #
        ######################
        self.AddCommand("save", SaveCmd, 'a', 'Saves all actively running worlds', '', 0)
        self.AddCommand("backup", BackupCmd, 'a', 'Backs up all actively running worlds', '', 0)
        self.AddCommand("setspawn", SetSpawnCmd, 'a', 'Changes the worlds default spawn location to where you are standing', '', 0)
        self.AddCommand("pruneblocklog", PruneBlockLogCmd, 'a', 'Removes all entrys from the block log older then <seconds>', 'Incorrect syntax. Usage: /pruneblocklog <seconds>', 1)
        ######################
        #OWNER COMMANDS HERE #
        ######################
        self.AddCommand("addrank", AddRankCmd, 'z', 'Promotes a player to a rank such a admin, operator, or builder', 'Incorrect syntax. Usage: /addrank <username> <a/o/b>', 2)
        self.AddCommand("removerank", RemoveRankCmd, 'z', 'Removes a players rank', 'Incorrect syntax. Usage: /removerank <username>', 1)
        self.AddCommand("zCreate", ZCreateCmd, 'z', 'Creates a restricted zone', 'Incorrect syntax. Usage: /zCreate <name> <owner> <height>', 3)
        self.AddCommand("zDelete", ZDeleteCmd, 'z', 'Deletes a restricted zone', 'Incorrect syntax. Usage: /zDelete <name>', 1)

    def HandleCommand(self,pPlayer,Message):
        '''Called when a player types a slash command'''
        if Message == '':
            pPlayer.SendMessage("&4Please enter in a command!")
            return
        Tokens = Message.split()
        Command = Tokens[0].lower()
        if self.CommandTable.has_key(Command) == False:
            pPlayer.SendMessage("&4No such command. Type /cmdlist for a list of commands")
            return
        else:
            CommandObj = self.CommandTable[Command]
            CommandObj.Execute(pPlayer,Message)

    def AddCommand(self,Command,CmdObj,Permissions,HelpMsg,ErrorMsg,MinArgs,Alias=False):
        self.CommandTable[Command.lower()] = CmdObj(self,Permissions,HelpMsg,ErrorMsg,MinArgs,Alias)
        