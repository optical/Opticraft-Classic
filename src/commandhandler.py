'''Command system for opticraft'''
from constants import *
from ordereddict import OrderedDict
import platform
import os
import os.path
import time
import sqlite3 as dbapi
import shutil
from world import World
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
            pPlayer.SendMessage('%s%s' %('&4',self.ErrorMsg))
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
            pPlayer.SendMessage("&aYou are no longer placing grass")
            pPlayer.SetBlockOverride(-1)
            return
        else:
            pPlayer.SetBlockOverride(BLOCK_GRASS)
            pPlayer.SendMessage("&aEvery block you create will now be grass. Type /grass to disable.")
class PaintCmd(CommandObject):
    '''Command handler for /paint command. When you destroy a block it is replaced with the block you are holding'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetPaintCmd():
            pPlayer.SetPaintCmd(False)
            pPlayer.SendMessage("&aPaint command has been disabled")
            return
        else:
            pPlayer.SetPaintCmd(True)
            pPlayer.SendMessage("&aPaint command enabled. Type /paint again to disable")
class HelpCmd(CommandObject):
    '''Returns a helpful message about a command'''
    def Run(self,pPlayer,Args,Message):
        if self.CmdHandler.CommandTable.has_key(Args[0].lower()) == False:
            pPlayer.SendMessage("&4" + "That command does not exist!")
            return
        else:
            CmdObj = self.CmdHandler.CommandTable[Args[0].lower()]
            pPlayer.SendMessage("&a" + CmdObj.HelpMsg)

class AboutCmd(CommandObject):
    '''The next block a player destroys/creates will display the blocks infromation'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.World.LogBlocks == True:
            pPlayer.SetAboutCmd(True)
            pPlayer.SendMessage("&aPlace/destroy a block to see what was there before")
        else:
            pPlayer.SendMessage("&4Block history is disabled")

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
class sInfoCmd(CommandObject):
    '''Handler for the /sinfo command. Returns server information'''
    def Run(self,pPlayer,Args,Message):
        System = platform.system()
        if System == "Linux":
            DistData = platform.linux_distribution()
            System = "%s-%s" %(DistData[0],DistData[1])
        WorldData = pPlayer.ServerControl.GetWorlds()
        pPlayer.SendMessage("&aThis server is running a development build of Opticraft on %s." %System)
        pPlayer.SendMessage("&aThere are currently %d users online, with a peak of %d since last restart." %(pPlayer.ServerControl.NumPlayers,pPlayer.ServerControl.PeakPlayers))
        pPlayer.SendMessage("&aThere are %d worlds, %d of which are active and %d idle." %(len(WorldData[0]) + len(WorldData[1]),len(WorldData[0]),len(WorldData[1])))
        pPlayer.SendMessage("&aCurrent uptime: %s." %pPlayer.ServerControl.GetUptimeStr())
class RanksCmd(CommandObject):
    '''Handler for the /ranks command'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.SendMessage("&aThe following ranks exist on this server")
        Items = RankToLevel.items()
        Items.sort(cmp= lambda x,y: cmp(x[1],y[1]))
        for Rank,Junk in Items:
            pPlayer.SendMessage("&e %s%s&e: %s" %(RankToColour[Rank],RankToName[Rank],RankToDescription[Rank]))

#######################
#RECRUIT COMMANDS HERE#
#######################
class WaterCmd(CommandObject):
    '''Command handler for /water command. Replaces all block placed with water'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetBlockOverride() == BLOCK_STILLWATER:
            pPlayer.SendMessage("&aYou are no longer placing water")
            pPlayer.SetBlockOverride(-1)
            return
        else:
            pPlayer.SetBlockOverride(BLOCK_STILLWATER)
            pPlayer.SendMessage("&aEvery block you create will now be water. Type /water to disable.")

class LavaCmd(CommandObject):
    '''Command handler for /lava command. Replaces all block placed with lava'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetBlockOverride() == BLOCK_STILLLAVA:
            pPlayer.SendMessage("&aYou are no longer placing lava")
            pPlayer.SetBlockOverride(-1)
            return
        else:
            pPlayer.SetBlockOverride(BLOCK_STILLLAVA)
            pPlayer.SendMessage("&aEvery block you create will now be lava. Type /lava to disable.")

########################
#BUILDER COMMANDS HERE #
########################
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
class ZoneTestCmd(CommandObject):
    '''Command handler for the /ztest command. Checks to see if you are in a zone'''
    def Run(self,pPlayer,Args,Message):
        x,y,z = pPlayer.GetX(),pPlayer.GetY(),pPlayer.GetZ()
        x /= 32
        y /= 32
        z -= 50
        z /= 32
        x = int(x)
        y = int(y)
        z = int(z)
        #O_O
        Zones = pPlayer.GetWorld().GetZones()
        for pZone in Zones:
            if pZone.IsInZone(x, y, z):
                pPlayer.SendMessage("&aIt appears you are in zone \"%s\"" %pZone.Name)
                return
        pPlayer.SendMessage("&aIt does not seem like you are in any zone.")
        
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
        pPlayer.SendMessage("&aSuccessfully added %s as a builder for zone \"%s\"" %(Username,pZone.Name))
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
        if Rank not in RankToLevel:
            pPlayer.SendMessage("&4Invalid rank! Valid ranks are: %s" %ValidRanks)
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

        ReversePlayer = Args[0]
        Time = Args[1]
        try:
            Time = int(Time)
        except:
            pPlayer.SendMessage("&4That is not a valud number of seconds")
            return
        if Time < 0:
            pPlayer.SendMessage("&4That is not a valud number of seconds")
            return
        Result = pPlayer.GetWorld().UndoActions(pPlayer.GetName(),ReversePlayer,Time)

        pPlayer.SendMessage("&a%s actions are being reversed. This may take a few moments" %ReversePlayer)

class DestroyTowerCmd(CommandObject):
    '''Handler for the /destroy tower command. This destroy a tower of blocks'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetTowerCmd():
            pPlayer.SendMessage("&aTower destruction turned off")
            pPlayer.SetTowerCmd(False)
            return
        else:
            pPlayer.SetTowerCmd(True)
            pPlayer.SendMessage("&aClick on the top-most block of the shitty tower to begin destruction")
class PromoteTrustedCmd(CommandObject):
    '''Promotes a user to the trusted rank'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        CurRank = pPlayer.ServerControl.GetRank(Username)
        if RankToLevel[CurRank] >= RankToLevel['t'] :
            pPlayer.SendMessage("&4That user already has a rank")
            return
        pPlayer.ServerControl.SetRank(Username,"t")
        pPlayer.SendMessage("&aSuccessfully set %s's rank to recruit" %(Username))

class DemoteTrustedCmd(CommandObject):
    '''Demotes a user from the trusted rank'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        CurRank = pPlayer.ServerControl.GetRank(Username)
        if CurRank != 't':
            pPlayer.SendMessage("&4That player doesn't have the recruit rank!")
            return
        pPlayer.ServerControl.SetRank(Username,"g")
        pPlayer.SendMessage("&aSuccessfully removed %s's rank." %(Username))
class MakeSpectatorCmd(CommandObject):
    '''Handler for the /makespectator command. Makes a user a spectator'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        CurRank = pPlayer.ServerControl.GetRank(Username)
        if CurRank != '':
            pPlayer.SendMessage("&4That user cannot be made a spectator")
            return
        pPlayer.ServerControl.SetRank(Username,"s")
        pPlayer.SendMessage("&aSuccessfully set %s's rank to spectator" %(Username))
class PromoteSpectatorCmd(CommandObject):
    '''Handler for the /promotespectator command. Gives the user the ability to build again'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        CurRank = pPlayer.ServerControl.GetRank(Username)
        if CurRank != 's':
            pPlayer.SendMessage("&4That user is not currently a spectator")
            return
        pPlayer.ServerControl.SetRank(Username,"s")
        pPlayer.SendMessage("&aSuccessfully removed %s's spectator restriction" %(Username))
class PlayerInfoCmd(CommandObject):
    '''Handler for the /playerinfo command. Returns info on a player'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target == None:
            pPlayer.SendMessage("&4That player is not online!")
            return
        pPlayer.SendMessage("&a%s has been online for&e %s" %(Target.GetName(), ElapsedTime(int(time.time()) -Target.GetLoginTime())))
        pPlayer.SendMessage("&aTheir ip is:&e %s" %Target.GetIP())
        pPlayer.SendMessage("They are on world&e \"%s\"" %Target.GetWorld().Name)
        if Target.GetRank() != '':
            pPlayer.SendMessage("&aTheir rank is&e %s" %RankToName[Target.GetRank()])
        else:
            pPlayer.SendMessage("&aAnd they do not have any rank")
        

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

class AddIPBanCmd(CommandObject):
    '''Handler for the /ipban command. Bans an IP Address from the server'''
    def Run(self,pPlayer,Args,Message):
         Arg = Args[0]
         #Check to see if this is a user...
         Target = pPlayer.ServerControl.GetPlayerFromName(Arg)
         if Target != None:
             if RankToLevel[Target.GetRank()] >= RankToLevel[pPlayer.GetRank()]:
                 pPlayer.SendMessage("&4You may not ban that user.")
                 return
             pPlayer.ServerControl.AddBan(Arg, 0)
             pPlayer.SendMessage("&aSuccessfully added username ban on %s" %Arg)
             #Set arg to the IP address so we can ban that too.
             Arg = Target.GetIP()
         #Check if IP is legit. If so, ban it.
         Parts = Arg.split(".")
         if len(Parts) != 4:
             pPlayer.SendMessage("&4That is not a valid ip-address!")
             return
         try:
             for Byte in Parts:
                 if len(Byte) > 3:
                     raise Exception
                 Byte = int(Byte)
                 if Byte < 0 or Byte > 255:
                     raise Exception
         except:
             pPlayer.SendMessage("&4That is not a valid ip-address!")
             return
         #Must be valid
         pPlayer.ServerControl.AddIPBan(pPlayer,Arg,0)
         pPlayer.SendMessage("&aSuccessfully banned ip %s" %Arg)

class DelIPBanCmd(CommandObject):
    '''Handler for the /delipban command. Removes an IP Address ban'''
    def Run(self,pPlayer,Args,Message):
         Arg = Args[0]
         #Verify this is a valid IP.
         Parts = Arg.split(".")
         if len(Parts) != 4:
             pPlayer.SendMessage("&4That is not a valid ip-address!")
             return
         try:
             for Byte in Parts:
                 if len(Byte) > 3:
                     raise Exception
                 Byte = int(Byte)
                 if Byte < 0 or Byte > 255:
                     raise Exception
         except:
             pPlayer.SendMessage("&4That is not a valid ip-address!")
             return
         pPlayer.ServerControl.UnbanIP(Arg)
         pPlayer.SendMessage("&aRemoved ban on ip \"%s\"" %Arg)

class WorldSetRankCmd(CommandObject):
    '''Sets the mimimum rank required to build on a world'''
    def Run(self,pPlayer,Args,Message):
        WorldName = Args[0].lower()
        Rank = Args[1]
        if Rank not in RankToName:
            pPlayer.SendMessage("&4That is not a valid rank! Valid ranks: %s" %ValidRanks)
            return
        pWorld = pPlayer.ServerControl.GetActiveWorld(WorldName)
        if pWorld == None:
            pPlayer.SendMessage("&4Could not change rank for that world.")
            pPlayer.SendMessage("&4Try joining that world then setting the rank.")
            return
        else:
            pWorld.MinRank = Rank
            pPlayer.SendMessage("&aSuccessfully set %s to be %s only" %(pWorld.Name,RankToName[Rank]))
class FlushBlockLogCmd(CommandObject):
    '''Flushes the worlds blocklog to disk'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.GetWorld().FlushBlockLog()
        pPlayer.SendMessage("&aWorld %s's Blocklog has been flushed to disk." %pPlayer.GetWorld().Name)
######################
#OWNER COMMANDS HERE #
######################
class AddRankCmd(CommandObject):
    '''Handle for the /addrank command - gives a username a rank. Can only be used by admins'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        Rank = Args[1].lower()
        if Rank not in RankToLevel:
            pPlayer.SendMessage("&4Invalid Rank! Valid ranks are: %s" %ValidRanks)
            return
        #Check to see we can set this rank.
        NewRank = RankToLevel[Rank]
        if NewRank >= RankToLevel[pPlayer.GetRank()]:
            pPlayer.SendMessage("&4You do not have permission to add this rank")
            return
        Target = pPlayer.ServerControl.GetRank(Username)
        if RankToLevel[Target] > RankToLevel[Rank]:
            pPlayer.SendMessage("&4You may not set that players rank!")
            return
        pPlayer.ServerControl.SetRank(Username,Rank)
        pPlayer.SendMessage("&aSuccessfully set %s's rank to %s" %(Username,Rank))
class RemoveRankCmd(CommandObject):
    '''Handle for the /removerank command - gives a username a rank. Can only be used by admins'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        CurRank = pPlayer.ServerControl.GetRank(Username)
        RankLevel = RankToLevel[CurRank]
        if RankToLevel[pPlayer.GetRank()] <= RankLevel:
            pPlayer.SendMessage("&4You do not have permission to remove that users rank")
            return
        pPlayer.ServerControl.SetRank(Username,'g')
        pPlayer.SendMessage("Removed %s's rank" %Username)

class ZCreateCmd(CommandObject):
    def Run(self,pPlayer,Args,Message):
        Name = Args[0]
        if Name.isalnum() == False:
            pPlayer.SendMessage("&4Invalid name!")
            return
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
class CreateWorldCmd(CommandObject):
    '''Handles the world cretion command'''
    def Run(self,pPlayer,Args,Message):
        Name = Args[0]
        if Name.isalnum() == False:
            pPlayer.SendMessage("&4That is not a valid name!")
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
            pPlayer.SendMessage("&4Please enter a valid X, Y, and Z coordinates!")
            return
        if pPlayer.ServerControl.WorldExists(Name):
            pPlayer.SendMessage("&4That world already exists!")
            return
        pWorld = World(pPlayer.ServerControl,Name,True,X,Y,Z)
        pPlayer.ServerControl.ActiveWorlds.append(pWorld)
        pWorld.SetIdleTimeout(pPlayer.ServerControl.WorldTimeout)
        pPlayer.SendMessage("Successfully created the world!")

class SetDefaultWorldCmd(CommandObject):
    '''Handler for the /setdefaultworld command'''
    def Run(self,pPlayer,Args,Message):
        WorldName = Args[0]
        pWorld = pPlayer.ServerControl.GetActiveWorld(WorldName)
        if pWorld == None:
            pPlayer.SendMessage("&4Could not set world to default world.")
            pPlayer.SendMessage("&4Try joining the world and trying again.")
            return
        pPlayer.ServerControl.SetDefaultWorld(pWorld)
        pPlayer.SendMessage("&aDefault world changed to&f \"%s\"" %pWorld.Name)

class RenameWorldCmd(CommandObject):
    '''Handler for the /renameworld command'''
    def Run(self,pPlayer,Args,Message):
        OldName = Args[0].lower()
        NewName = Args[1]
        if NewName.isalnum() == False:
            pPlayer.SendMessage("&4That is not a valid name!")
            return
        if pPlayer.ServerControl.WorldExists(OldName) == False:
            pPlayer.SendMessage("&4That world does not exist!")
            return
        if pPlayer.ServerControl.WorldExists(NewName):
            pPlayer.SendMessage("&4There is already a world with that name!")
            return

        #Is it an idle world?
        ActiveWorlds,IdleWorlds = pPlayer.ServerControl.GetWorlds()
        FoundWorld = False
        for WorldName in IdleWorlds:
            if WorldName.lower() == OldName:
                #Sure is
                os.rename("Worlds/%s.save" %WorldName, "Worlds/%s.save" %NewName)
                if os.path.isfile("Worlds/BlockLogs/%s.db" %WorldName):
                    os.rename("Worlds/BlockLogs/%s.db" %WorldName, "Worlds/BlockLogs/%s.db" %NewName)
                pPlayer.ServerControl.IdleWorlds.remove(WorldName)
                pPlayer.ServerControl.IdleWorlds.append(NewName)
                FoundWorld = True
                break

        #Is it an active world?
        if FoundWorld == False:
            for pWorld in ActiveWorlds:
                if pWorld.Name.lower() == OldName:
                    os.rename("Worlds/%s.save" %pWorld.Name, "Worlds/%s.save" %NewName)
                    #Close the SQL Connection if its active
                    if pWorld.DBConnection != None:
                        pWorld.DBConnection.commit()
                        pWorld.DBConnection.close()
                        pWorld.DBCursor = None
                        pWorld.DBConnection = None
                        shutil.copy("Worlds/BlockLogs/%s.db" %pWorld.Name, "Worlds/BlockLogs/%s.db" %NewName)
                        #The copy will be removed by the IO Thread for the world.
                        pWorld.DBConnection = dbapi.connect("Worlds/BlockLogs/%s.db" %NewName)
                        pWorld.DBCursor = pWorld.DBConnection.cursor()
                        #Get the IO Thread to reconnect.
                        pWorld.IOThread.SetWorldName(NewName)
                        pWorld.IOThread.Tasks.put(["CONNECT"])
                    pWorld.Name = NewName
                    #Are we the default map?
                    if pPlayer.ServerControl.ConfigValues.GetValue("worlds","DefaultName","Main").lower() == OldName:
                        #<_<
                        pPlayer.ServerControl.ConfigValues.set("worlds","DefaultName",NewName)
                        fHandle = open("opticraft.cfg","w")
                        pPlayer.ServerControl.ConfigValues.write(fHandle)
                        fHandle.close()
                    break

        #Finally, change zones.
        for pZone in pPlayer.ServerControl.GetZones():
            if pZone.Map.lower() == OldName:
                pZone.SetMap(NewName)
        pPlayer.SendMessage("&aSuccessfully renamed map %s to %s" %(OldName,NewName))


class CommandHandler(object):
    '''Stores all the commands avaliable on opticraft and processes any command messages'''
    def __init__(self,ServerControl):
        self.CommandTable = OrderedDict()
        self.ServerControl = ServerControl
        #Populate the command table here
        ######################
        #PUBLIC COMMANDS HERE#
        ######################
        self.AddCommand("about", AboutCmd, 'g', 'Displays history of a block when you destroy/create one', '', 0)
        self.AddCommand("cmdlist", CmdListCmd, 'g', 'Lists all commands available to you', '', 0)
        self.AddCommand("commands", CmdListCmd, 'g', 'Lists all commands available to you', '', 0,Alias=True)
        self.AddCommand("help", HelpCmd, 'g', 'Gives help on a specific command. Usage: /help <cmd>', 'Incorrect syntax! Usage: /help <cmd>', 1)
        self.AddCommand("worlds", WorldsCmd, 'g', 'Lists all available worlds', '', 0)
        self.AddCommand("join", JoinWorldCmd, 'g', 'Changes the world you are in', 'Incorrect syntax! Usage: /join <world>. Use /worlds to see a list of worlds.', 1)
        self.AddCommand("j", JoinWorldCmd, 'g', 'Changes the world you are in', 'Incorrect syntax! Usage: /join <world>. Use /worlds to see a list of worlds.', 1,Alias=True)
        self.AddCommand("goto", JoinWorldCmd, 'g', 'Changes the world you are in', 'Incorrect syntax! Usage: /join <world>. Use /worlds to see a list of worlds.', 1,Alias=True)
        self.AddCommand("grass", GrassCmd, 'g', 'Allows you to place grass', '', 0)
        self.AddCommand("paint", PaintCmd, 'g', 'When you destroy a block it will be replaced by what you are currently holding', '', 0)
        self.AddCommand("sinfo", sInfoCmd, 'g', 'Displays information about the server', '', 0)
        self.AddCommand("ranks", RanksCmd, 'g', 'Displays information on all the ranks', '', 0)
        #######################
        #RECRUIT COMMANDS HERE#
        #######################
        self.AddCommand("water", WaterCmd, 't', 'Allows you to place water', '', 0)
        self.AddCommand("lava", LavaCmd, 't', 'Allows you to place lava', '', 0)
        ########################
        #BUILDER COMMANDS HERE #
        ########################
        self.AddCommand("appear", AppearCmd, 'b', 'Teleports you to a players location', 'Incorrect syntax! Usage: /appear <username>', 1)
        self.AddCommand("tp", AppearCmd, 'b', 'Teleports you to a players location', 'Incorrect syntax! Usage: /appear <username>', 1, Alias=True)
        #Zone commands
        self.AddCommand("zinfo", ZoneInfoCmd, 'b', 'Returns information on a zone.', 'Incorrect syntax! Usage: /zinfo <zone>', 1)
        self.AddCommand("zlist", ZoneListCmd, 'b', 'Lists all zones on the map', '', 0)
        self.AddCommand("ztest", ZoneTestCmd, 'b', 'Checks to see if you are in a zone.', '', 0)
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
        self.AddCommand("whois", PlayerInfoCmd, 'o', 'Returns information on a player', 'Incorrect syntax! Usage: /playerinfo <username>',1)
        self.AddCommand("playerinfo", PlayerInfoCmd, 'o', 'Returns information on a player', 'Incorrect syntax! Usage: /playerinfo <username>',1,Alias=True)
        self.AddCommand("summon", SummonCmd, 'o', 'Teleports a player to your location', 'Incorrect syntax! Usage: /summon <username>', 1)
        self.AddCommand("undoactions", UndoActionsCmd, 'o', 'Undoes all of a a players actions in the last X seconds', 'Incorrect Syntax! Usage: /undoactions <username> <seconds>',2)
        self.AddCommand("promote", PromoteTrustedCmd, 'o', 'Promotes a player to the recruit rank', 'Incorrect syntax! Usage: /promote <username>', 1)
        self.AddCommand("demote", DemoteTrustedCmd, 'o', 'Demotes a player from the recruit rank', 'Incorrect syntax! Usage: /demote <username>', 1)
        self.AddCommand("makespectator",MakeSpectatorCmd, 'o', 'Demotes a player to a spectator which cannot build','Incorrect syntax! Usage: /makespectator <username>',1)
        self.AddCommand("promotespectator",PromoteSpectatorCmd, 'o', 'Gives the player the ability to build again','Incorrect syntax! Usage: /promotespectator <username>',1)
        self.AddCommand("destroytower",DestroyTowerCmd,'o', 'Destroys a vertical tower of shit','',0,Alias=True) #Hidden command
        self.AddCommand("flushblocklog",FlushBlockLogCmd,'o', 'Flushes the worlds blocklog to disk','',0)
        ######################
        #ADMIN COMMANDS HERE #
        ######################
        self.AddCommand("addipban", AddIPBanCmd, 'a', 'Ip bans a player from the server.', 'Incorrect syntax! Usage: /addipban <ip/username>', 1)
        self.AddCommand("delipban", DelIPBanCmd, 'a', 'Removes an IP ban', 'Incorrect syntax! Usage: /delipban <ip/username>', 1)
        self.AddCommand("save", SaveCmd, 'a', 'Saves all actively running worlds', '', 0)
        self.AddCommand("backup", BackupCmd, 'a', 'Backs up all actively running worlds', '', 0)
        self.AddCommand("setspawn", SetSpawnCmd, 'a', 'Changes the worlds default spawn location to where you are standing', '', 0)
        self.AddCommand("addrank", AddRankCmd, 'a', 'Promotes a player to a rank such a admin, operator, or builder', 'Incorrect syntax. Usage: /addrank <username> <t/a</o/b>', 2)
        self.AddCommand("removerank", RemoveRankCmd, 'a', 'Removes a players rank', 'Incorrect syntax. Usage: /removerank <username>', 1)
        self.AddCommand("worldsetrank", WorldSetRankCmd, 'a', 'Sets the minimum rank to build on a world', 'Incorrect syntax. Usage: /worldsetrank <world> <t/b/o/a>', 1)
        self.AddCommand("zCreate", ZCreateCmd, 'a', 'Creates a restricted zone', 'Incorrect syntax. Usage: /zCreate <name> <owner> <height>', 3)
        self.AddCommand("zDelete", ZDeleteCmd, 'a', 'Deletes a restricted zone', 'Incorrect syntax. Usage: /zDelete <name>', 1)
        ######################
        #OWNER COMMANDS HERE #
        ######################
        self.AddCommand("createworld", CreateWorldCmd, 'z', 'Creates a new world.', 'Incorrect syntax. Usage: /createworld <name> <x> <y> <z>', 4)
        self.AddCommand("setdefaultworld", SetDefaultWorldCmd, 'z', 'Sets the world you specify to be the default one', 'Incorrect syntax. Usage: /setdefaultworld <name>', 1)
        self.AddCommand("RenameWorld", RenameWorldCmd, 'z', 'Renames a world', 'Incorrect syntax! Usage: /renameworld <oldname> <newname>', 2)
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
        