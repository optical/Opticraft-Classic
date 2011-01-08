'''Command system for opticraft'''
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

from core.constants import *
from core.ordereddict import OrderedDict
import platform
import os
import os.path
import time
import sqlite3 as dbapi
import shutil
from core.world import World
from core.console import *
class CommandObject(object):
    '''Child class for all commands'''
    def __init__(self,CmdHandler,Permissions,HelpMsg,ErrorMsg,MinArgs,Name,Alias = False):
        self.Permissions = Permissions
        self.PermissionLevel = CmdHandler.ServerControl.GetRankLevel(Permissions)
        self.Name = Name
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
        Tokens = Message.split()[1:]
        Args = len(Tokens)
        if Args < self.MinArgs:
            pPlayer.SendMessage('%s%s' %('&4',self.ErrorMsg))
            return
        else:
            self.Run(pPlayer,Tokens,Message)
            if self.CmdHandler.LogFile != None and self.PermissionLevel >= self.CmdHandler.ServerControl.GetRankLevel('operator'):
                #Log all operator+ commands
                self.LogCommand(pPlayer, self.Name, Tokens)
    def LogCommand(self,pPlayer,Command, Args):
        TimeFormat = time.strftime("%d %b %Y [%H:%M:%S]",time.localtime())
        OutStr = "%s User %s (%s) used command %s with args: %s\n" %(TimeFormat,pPlayer.GetName(),pPlayer.GetIP(), Command, ' '.join(Args))
        self.CmdHandler.LogFile.write(OutStr)
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
        pPlayer.SendMessage("&aType /help <cmd> for more specific help on a command.")

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
class RulesCmd(CommandObject):
    '''Lists all of the servers rules'''
    def Run(self,pPlayer,Args,Message):
        if len(pPlayer.ServerControl.Rules) == 0:
            pPlayer.SendMessage("&aThis server has no rules!")
            return
        pPlayer.SendMessage("&aThe rules for this server are as follows:")
        for line in pPlayer.ServerControl.Rules:
            pPlayer.SendMessage(line)
            
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
        if pPlayer.ServerControl.Now - pPlayer.GetLastWorldChange() < 5:
            pPlayer.SendMessage("&4You cannot change worlds that often!")
            return

        pPlayer.ChangeWorld(World)
class WorldsCmd(CommandObject):
    '''Handler for the /worlds command. Lists all available worlds.'''
    def Run(self,pPlayer,Args,Message):
        ActiveWorlds, IdleWorlds = pPlayer.ServerControl.GetWorlds()
        All = len(Args) > 0
        OutString = str()
        if All:
            pPlayer.SendMessage("&aDisplaying all worlds")
        pPlayer.SendMessage("&aThe following worlds are available:")
        for pWorld in ActiveWorlds:
            if pWorld.IsHidden() == 0 or All:
                OutString = '%s%s%s ' %(OutString,pPlayer.ServerControl.RankColours[pWorld.GetMinRank()],pWorld.Name)
        for WorldName in IdleWorlds:
            if pPlayer.ServerControl.IsWorldHidden(WorldName) == 0 or All:
                OutString = OutString = '%s%s%s ' %(OutString,pPlayer.ServerControl.RankColours[pPlayer.ServerControl.GetWorldRank(WorldName)],WorldName)
        pPlayer.SendMessage(OutString,False)
        if not All:
            pPlayer.SendMessage("&aTo see all worlds, type /worlds all.")
        
class StatsCmd(CommandObject):
    '''Handler for the /stats command. Returns information'''
    def Run(self,pPlayer,Args,Message):
        if len(Args) == 0:
            Target = pPlayer
        else:
            Target = pPlayer.ServerControl.GetPlayerFromName(Args[0])
            if Target == None or Target.CanBeSeenBy(pPlayer) == False:
                pPlayer.SendMessage("&4That player is not online")
                return

        if Target.IsDataLoaded():
            Target.UpdatePlayedTime()
            pPlayer.SendMessage("&a%s's join date was: &e%s" %(Target.GetName(),time.ctime(Target.GetJoinedTime())))
            pPlayer.SendMessage("&aSince then they have logged in &e%d &atimes" %Target.GetLoginCount())
            pPlayer.SendMessage("&aAnd have created &e%d &ablocks and deleted &e%d" %(Target.GetBlocksMade(),Target.GetBlocksErased()))
            pPlayer.SendMessage("&aTheir played time is &e%s" %ElapsedTime(Target.GetTimePlayed()))
            pPlayer.SendMessage("&aAnd they have spoken &e%d &alines thus far" %Target.GetChatMessageCount())
        else:
            pPlayer.SendMessage("&4Database is loading data. Try again soon!")
class ToggleNotificationsCmd(CommandObject):
    '''Handler for the /togglenotifications command. Enables/Disables join notices'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetJoinNotifications():
            pPlayer.SetJoinNotifications(False)
            pPlayer.SendMessage("&aJoin/Leave notifications have been disabled")
        else:
            pPlayer.SetJoinNotifications(True)
            pPlayer.SendMessage("&aJoin/Leave notifications have been enabled")

class sInfoCmd(CommandObject):
    '''Handler for the /sinfo command. Returns server information'''
    def Run(self,pPlayer,Args,Message):
        System = platform.system()
        if System == "Linux":
            DistData = platform.linux_distribution()
            System = "%s-%s" %(DistData[0],DistData[1])
        WorldData = pPlayer.ServerControl.GetWorlds()
        pPlayer.SendMessage("&aThis server is running Opticraft-DEV on &e%s." %System,False)
        pPlayer.SendMessage("&aCurrently &e%d &ausers online. Peak online: &e%d" %(pPlayer.ServerControl.NumPlayers,pPlayer.ServerControl.PeakPlayers),False)
        pPlayer.SendMessage("&aTotal worlds: &e%d &a(&e%d &aactive, &e%d &aidle)" %(len(WorldData[0]) + len(WorldData[1]),len(WorldData[0]),len(WorldData[1])),False)
        pPlayer.SendMessage("&aCpu usage in the last minute: &e%.1f%% (us: %.1f%% sys: %.1f%%)" %pPlayer.ServerControl.GetCurrentCpuUsage(),False)
        pPlayer.SendMessage("&aCpu usage overall &e%.1f%% (us: %.1f%% sys: %.1f%%)" %pPlayer.ServerControl.GetTotalCpuUsage(),False)
        pPlayer.SendMessage("&aCurrent uptime: &e%s." %pPlayer.ServerControl.GetUptimeStr(),False)
class VersionCmd(CommandObject):
    '''Handler for the /version command. Returns version information'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.SendMessage("&aThis server is running Opticraft-DEV")
class CreditsCmd(CommandObject):
    '''Handler for the /credits command. Returns credit information'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.SendMessage("&aOpticraft was developed by Jared Klopper using the Python programming language, vers                  ion 2.6")
class RanksCmd(CommandObject):
    '''Handler for the /ranks command'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.SendMessage("&aThe following ranks exist on this server")
        Items = pPlayer.ServerControl.RankNames
        for Rank in Items:
            Description = pPlayer.ServerControl.RankDescriptions.get(Rank.lower(),None)
            if Description != None:
                Colour = pPlayer.ServerControl.RankColours[Rank.lower()]
                pPlayer.SendMessage("&e %s%s&e: %s" %(Colour,Rank,Description))

class PlayerInfoCmd(CommandObject):
    '''Handler for the /whois command. Returns info on a player'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target == None or Target.CanBeSeenBy(pPlayer) == False:
            #Try load some data from the DB
            try:
                Result = pPlayer.ServerControl.PlayerDBConnection.execute("SELECT * FROM Players where Username = ?", (Username.lower(),))
                Row = Result.fetchone()
                if Row == None:
                    pPlayer.SendMessage("&4That player does not exist!")
                    return
                pPlayer.SendMessage("&a%s is &4Offline. &aRank: &e%s" %(Username,pPlayer.ServerControl.GetRank(Username).capitalize()))
                pPlayer.SendMessage("&aLast login was: &e%s &aago" %(ElapsedTime(int(pPlayer.ServerControl.Now)-Row["LastLogin"])))
                pPlayer.SendMessage("&aJoined on: &e%s" %(time.ctime(Row["Joined"])))
                if pPlayer.HasPermission('operator'):
                    pPlayer.SendMessage("&aTheir last ip was &e%s" %(Row["LastIp"]))
                    if Row["BannedBy"] != '':
                        pPlayer.SendMessage("&aThey were banned by &e%s" %(Row["BannedBy"]))
                    if Row["RankedBy"] != '':
                        pPlayer.SendMessage("&aTheir rank was set by &e%s" %(Row["RankedBy"]))

            except dbapi.OperationalError:
                pPlayer.SendMessage("&4The database is busy. Try again soon")
        else:
            pPlayer.SendMessage("&a%s has been online for &e%s" %(Target.GetName(), ElapsedTime(int(pPlayer.ServerControl.Now) -Target.GetLoginTime())))
            if pPlayer.HasPermission('operator'):
                pPlayer.SendMessage("&aCurrent IP: &e%s" %(Target.GetIP()))
                if Target.GetRankedBy() != '':
                    pPlayer.SendMessage("&aTheir rank was set by &e%s" %Target.GetRankedBy())
            pPlayer.SendMessage("&aThey are on world &e\"%s\"" %Target.GetWorld().Name)
            pPlayer.SendMessage("&aTheir rank is &e%s" %Target.GetRank().capitalize())
            if Target.IsInvisible(): #Dont check CanBeSeenBy() - thats been done already.
                pPlayer.SendMessage("&aThey are currently invisible")


class PlayerListCmd(CommandObject):
    '''Handler for the /players command. Lists all online players'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.SendMessage("&aThe following players are online:")
        OutStr = ''
        PlayerList = sorted(pPlayer.ServerControl.PlayerSet,key=lambda player: player.GetName().lower())
        for oPlayer in PlayerList:
            if oPlayer.IsAuthenticated() == False:
                continue
            if oPlayer.CanBeSeenBy(pPlayer) == False:
                continue
            #1 = space
            if len(oPlayer.GetColouredName()) + 1 + len(OutStr) < 63:
                OutStr = '%s %s' %(OutStr,oPlayer.GetColouredName())
            else:
                pPlayer.SendMessage(OutStr)
                OutStr = '%s' %(oPlayer.GetColouredName())
        if OutStr != '':
            pPlayer.SendMessage(OutStr)

class EmoteCmd(CommandObject):
    '''Handler for the /me command. Emotes an action'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.ServerControl.SendMessageToAll('&5*%s %s' %(pPlayer.GetName(),' '.join(Args)))
        if pPlayer.ServerControl.EnableIRC:
            pPlayer.ServerControl.IRCInterface.HandleEmote(pPlayer.GetName(), ' '.join(Args))

class ReplyCmd(CommandObject):
    '''Handler for the /reply command. Shortcut command to reply to a PM'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetLastPM() == '':
            pPlayer.SendMessage("&4No one recently sent you a PM!")
            return
        pPlayer.HandlePrivateMessage("%s %s" %(pPlayer.GetLastPM(),' '.join(Args)))

class ZoneInfoCmd(CommandObject):
    '''Zone info command handler. Returns information on a zone'''
    def Run(self,pPlayer,Args,Message):
        Name = Args[0]
        pZone = pPlayer.GetWorld().GetZone(Name)
        if pZone == None:
            pPlayer.SendMessage("&4No such zone exists on this map")
            return
        pPlayer.SendMessage("&aOwner: &e%s" %pZone.Owner)
        pPlayer.SendMessage("&aMinimum rank: &e%s" %pZone.MinRank.capitalize())
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
            pPlayer.ServerControl.GetPlayerFromName(Username).SendMessage("&aYou have been added as a builder to zone &f%s" %pZone.Name)
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
        pPlayer.SendMessage("&aSuccessfully removed %s as a builder for zone &f\"%s\"" %(Username,pZone.Name))
        if pPlayer.ServerControl.GetPlayerFromName(Username) != None:
            pPlayer.ServerControl.GetPlayerFromName(Username).SendMessage("&aYou have been removed as a builder from zone &f\"%s\"" %pZone.Name)

class zSetMinRankCmd(CommandObject):
    '''Handler for the zSetMinRank command. Changes the minimum rank to build in a zone'''
    def Run(self,pPlayer,Args,Message):
        ZoneName = Args[0]
        Rank = Args[1]
        if pPlayer.ServerControl.IsValidRank(Rank) != True:
            pPlayer.SendMessage("&4Invalid rank! Valid ranks are: %s" %pPlayer.ServerControl.GetExampleRanks())
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
        pPlayer.SendMessage("&aMinimum non-builder ranked required to build in zone \"%s\" is now %s" %(pZone.Name,Rank.capitalize()))

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
        pPlayer.SendMessage("&aSuccessfully changed the owner of zone &f\"%s\" &ato &f%s" %(pZone.Name,Username))
        if pPlayer.ServerControl.GetPlayerFromName(Username) != None:
            pPlayer.ServerControl.GetPlayerFromName(Username).SendMessage("&aYou have been set as the owner of zone &f\"%s\"" %pZone.Name)

########################
#BUILDER COMMANDS HERE #
########################
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
class AppearCmd(CommandObject):
    '''Appear command handler. Teleports user to specified players location'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target != None and Target.CanBeSeenBy(pPlayer):
            if pPlayer.GetWorld() != Target.GetWorld():
                pPlayer.ChangeWorld(Target.GetWorld().Name)
                pPlayer.SetSpawnPosition(Target.GetX(),Target.GetY(),Target.GetZ(),Target.GetOrientation(),Target.GetPitch())
                return
            pPlayer.Teleport(Target.GetX(),Target.GetY(),Target.GetZ(),Target.GetOrientation(),Target.GetPitch())
        else:
            pPlayer.SendMessage("&4That player is not online!")
#########################
#OPERATOR COMMANDS HERE #
#########################
class SolidCmd(CommandObject):
    '''Command handler for /solid command. Replaces all block placed with adminium/admincrete'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.GetBlockOverride() == BLOCK_HARDROCK:
            pPlayer.SendMessage("&aYou are no longer placing adminium")
            pPlayer.SetBlockOverride(-1)
            return
        else:
            pPlayer.SetBlockOverride(BLOCK_HARDROCK)
            pPlayer.SendMessage("&aEvery block you create will now be adminium. Type /grass to disable.")
class ModifyRankCmd(CommandObject):
    '''Handle for the /addrank command - gives a username a rank. Can only be used by admins'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        Rank = Args[1].lower()
        if pPlayer.ServerControl.IsValidRank(Rank) == False:
            pPlayer.SendMessage("&4Invalid Rank! Valid ranks are: %s" %pPlayer.ServerControl.GetExampleRanks())
            return
        #Check to see we can set this rank.
        NewRank = pPlayer.ServerControl.GetRankLevel(Rank)
        if NewRank >= pPlayer.GetRankLevel():
            pPlayer.SendMessage("&4You do not have permission to add this rank")
            return
        Target = pPlayer.ServerControl.GetRank(Username)
        if pPlayer.ServerControl.GetRankLevel(Target) > pPlayer.GetRankLevel():
            pPlayer.SendMessage("&4You may not set that players rank!")
            return
        pPlayer.ServerControl.SetRank(pPlayer,Username,Rank)
        pPlayer.SendMessage("&aSuccessfully set %s's rank to %s" %(Username,Rank.capitalize()))

class BanCmd(CommandObject):
    '''Ban command handler. Bans a username (permanently)'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        if ":" in Username:
            pPlayer.SendMessage("&4That is not a valid username!")
            return
        if pPlayer.ServerControl.GetRankLevel(pPlayer.ServerControl.GetRank(Username)) >= pPlayer.GetRankLevel():
            pPlayer.SendMessage("&4You may not ban someone with the same rank or higher then yours")
            return
        Result = pPlayer.ServerControl.AddBan(pPlayer,Username, 0) #TODO: Parse input so we can enter expiry!
        if Result:
            pPlayer.ServerControl.SendNotice("%s was banned by %s" %(Username,pPlayer.GetName()))
        pPlayer.SendMessage("&aSuccessfully banned %s" %(Username))

class UnbanCmd(CommandObject):
    '''Unban command handler. Removes a ban for a username'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        Result = pPlayer.ServerControl.Unban(Username)
        if Result:
            pPlayer.SendMessage("&aSuccessfully unbanned %s" %(Username))
        else:
            pPlayer.SendMessage("&4That user was not banned!")

class KickCmd(CommandObject):
    '''Kick command handler. Kicks a user from the server'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        ReasonTokens = Args[1:]
        if pPlayer.ServerControl.GetRankLevel(pPlayer.ServerControl.GetRank(Username)) >= pPlayer.GetRankLevel():
            pPlayer.SendMessage("&4You may not kick someone with the same rank or higher then yours")
            return
        Reason = ''
        for Token in ReasonTokens:
            Reason += Token + ' '

        if Reason == '':
            Reason = "(No reason given)"

        Result = pPlayer.ServerControl.Kick(pPlayer,Username,Reason)
        if Result:
            pPlayer.SendMessage("&aSuccessfully kicked %s" %(Username))
        else:
            pPlayer.SendMessage("&4That user is not online!")

class SummonCmd(CommandObject):
    '''Summon command handler. Teleports specified player to user location'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target != None and Target.CanBeSeenBy(pPlayer):
            if pPlayer.GetWorld() != Target.GetWorld():
                Target.SetSpawnPosition(pPlayer.GetX(),pPlayer.GetY(),pPlayer.GetZ(),pPlayer.GetOrientation(),pPlayer.GetPitch())
                Target.ChangeWorld(pPlayer.GetWorld().Name)
            else:
                Target.Teleport(pPlayer.GetX(),pPlayer.GetY(),pPlayer.GetZ(),pPlayer.GetOrientation(),pPlayer.GetPitch())
            pPlayer.SendMessage("&aSuccessfully summoned %s" %Target.GetName())
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

    def LogCommand(self,pPlayer,Command, Args):
        '''Override the default log handler'''
        TimeFormat = time.strftime("%d %b %Y [%H:%M:%S]",time.localtime())
        OutStr = "%s User %s (%s) used command %s on world %s with args: %s\n" %(TimeFormat,pPlayer.GetName(),pPlayer.GetIP(),Command, pPlayer.GetWorld().Name, ' '.join(Args))
        self.CmdHandler.LogFile.write(OutStr)

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
class InvisibleCmd(CommandObject):
    '''Handles the /invisible command'''
    def Run(self,pPlayer,Args,Message):
        if pPlayer.IsInvisible():
            pPlayer.SetInvisible(False)
            pPlayer.SendMessage("&aYou are no longer invisible")
        else:
            pPlayer.SetInvisible(True)
            pPlayer.SendMessage("&aYou are now invisible to all users with a lower rank then yours.")
######################
#ADMIN COMMANDS HERE #
######################
class SaveCmd(CommandObject):
    '''Handle for the /save command - saves all running worlds'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.ServerControl.SaveAllWorlds()
        pPlayer.SendMessage("&aSaved all worlds successfully")
class BackupCmd(CommandObject):
    '''Handle for the /backup command - backs up all running worlds'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.ServerControl.BackupAllWorlds()
        pPlayer.SendMessage("&aBacked up all worlds successfully")

class SetSpawnCmd(CommandObject):
    '''Handle for the /setspawn command - moves the default spawnpoint to the location you are at'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.GetWorld().SetSpawn(pPlayer.GetX(), pPlayer.GetY(), pPlayer.GetZ(), pPlayer.GetOrientation(),0)
        pPlayer.SendMessage("&aThis worlds spawnpoint has been moved")

class AddIPBanCmd(CommandObject):
    '''Handler for the /ipban command. Bans an IP Address from the server'''
    def Run(self,pPlayer,Args,Message):
         Arg = Args[0]
         #Check to see if this is a user...
         Target = pPlayer.ServerControl.GetPlayerFromName(Arg)
         if Target != None:
             if Target.GetRankLevel() >= pPlayer.GetRankLevel():
                 pPlayer.SendMessage("&4You may not ban that user.")
                 return
             pPlayer.ServerControl.AddBan(pPlayer,Arg, 0)
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
        if pPlayer.ServerControl.IsValidRank(Rank) == False:
            pPlayer.SendMessage("&4That is not a valid rank! Valid ranks: %s" %pPlayer.ServerControl.GetExampleRanks())
            return
        pWorld = pPlayer.ServerControl.GetActiveWorld(WorldName)
        if pWorld == None:
            pPlayer.SendMessage("&4Could not change rank for that world.")
            pPlayer.SendMessage("&4Try joining that world then setting the rank.")
            return
        else:
            pWorld.SetMinRank(Rank.lower())
            pPlayer.ServerControl.SetWorldRank(pWorld.Name, Rank)
            pPlayer.SendMessage("&aSuccessfully set %s to be %s only" %(pWorld.Name,Rank.capitalize()))
class TempOpCmd(CommandObject):
    '''Handle for the /tempop command - gives a username temporary operator status'''
    def Run(self,pPlayer,Args,Message):
        Username = Args[0]
        Target = pPlayer.ServerControl.GetPlayerFromName(Username)
        if Target == None:
            pPlayer.SendMessage("&4Tahat player is not online!")
            return
        if Target.GetRankLevel() > pPlayer.ServerControl.GetRankLevel('operator'):
            pPlayer.SendMessage("&4You may not set that players rank!")
            return
        Target.SetRank('operator')
        Target.SendMessage("&aYou have been granted temporary operator privlidges by %s" %pPlayer.GetName())
        pPlayer.SendMessage("&a%s is now a temporary operator" %Username)

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
        pPlayer.SendMessage("&aSuccessfully deleted zone &f\"%s\"" %pZone.Name)
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
            pPlayer.SendMessage("&4Please enter a valid length, width, and height coordinates!")
            return
        try:
            assert(X%16==0)
            assert(Y%16==0)
            assert(Z%16==0)
        except AssertionError:
            pPlayer.SendMessage("&4Your length, width and height coorinates need to be a multiple of 16")
            return
        if pPlayer.ServerControl.WorldExists(Name):
            pPlayer.SendMessage("&4That world already exists!")
            return
        pWorld = World(pPlayer.ServerControl,Name,True,X,Y,Z)
        pPlayer.ServerControl.ActiveWorlds.append(pWorld)
        pPlayer.ServerControl.SetWorldRank(pWorld.Name, pWorld.GetMinRank())
        pPlayer.ServerControl.SetWorldHidden(pWorld.Name, pWorld.IsHidden())
        pWorld.SetIdleTimeout(pPlayer.ServerControl.WorldTimeout)
        pPlayer.SendMessage("&aSuccessfully created world \"&f%s&a\"" %Name)

class LoadWorldCmd(CommandObject):
    '''Handler for the /worldload command'''
    def Run(self,pPlayer,Args,Message):
        WorldName = Args[0]
        if os.path.isfile("Worlds/%s.save" %WorldName) == False:
            pPlayer.SendMessage("&4That world doesn't exist. Check that you spelt it correctly")
            return
        if pPlayer.ServerControl.WorldExists(WorldName):
            pPlayer.SendMessage("&4That world is already loaded!")
            return
        pPlayer.ServerControl.AddWorld(WorldName)
        pPlayer.SendMessage("&aSuccessfully loaded world \"&f%s&a\"!" %WorldName)
class LoadTemplateCmd(CommandObject):
    '''Handler for the /loadtemplate command'''
    def Run(self,pPlayer,Args,Message):
        TemplateName = Args[0]
        WorldName = Args[1]
        if os.path.isfile("Templates/%s.save" %TemplateName) == False:
            pPlayer.SendMessage("&4That template doesn't exist. Check that you spelt it correctly")
            return
        if pPlayer.ServerControl.WorldExists(WorldName):
            pPlayer.SendMessage("&4A world with that name already exists!")
            return
        shutil.copy("Templates/%s.save" %TemplateName,"Worlds/%s.save" %WorldName)
        pPlayer.ServerControl.AddWorld(WorldName)
        pPlayer.SendMessage("&aSuccessfully loaded template \"&f%s&a\"!" %TemplateName)
class ShowTemplatesCmd(CommandObject):
    '''Handler for the /showtemplates command'''
    def Run(self,pPlayer,Args,Message):
        OutStr = ''
        for File in os.listdir("Templates"):
            if len(File) < 5:
                continue
            if File[-5:] != ".save":
                continue
            TemplateName = File[:-5]
            OutStr = '%s%s ' %(OutStr,TemplateName)
        if OutStr != '':
            pPlayer.SendMessage("&aThe following templates exist:")
            pPlayer.SendMessage("&a%s" %OutStr)
        else:
            pPlayer.SendMessage("&aThere are no templates!")
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
        pPlayer.SendMessage("&aDefault world changed to &f\"%s\"" %pWorld.Name)
class HideWorldCmd(CommandObject):
    '''Handler for the /hideworld command'''
    def Run(self,pPlayer,Args,Message):
        WorldName = Args[0]
        pWorld = pPlayer.ServerControl.GetActiveWorld(WorldName)
        if pWorld == None:
            pPlayer.SendMessage("&4Could not set world to hidden.")
            pPlayer.SendMessage("&4Try joining the world and trying again.")
            return
        pWorld.SetHidden(1)
        pPlayer.ServerControl.SetWorldHidden(pWorld.Name, 1)
        pPlayer.SendMessage("&aWorld \"&e%s&a\" is now being hidden" %pWorld.Name)

class UnHideWorldCmd(CommandObject):
    '''Handler for the /unhideworld command'''
    def Run(self,pPlayer,Args,Message):
        WorldName = Args[0]
        pWorld = pPlayer.ServerControl.GetActiveWorld(WorldName)
        if pWorld == None:
            pPlayer.SendMessage("&4Could not unhide world.")
            pPlayer.SendMessage("&4Try joining the world and trying again.")
            return
        pWorld.SetHidden(0)
        pPlayer.ServerControl.SetWorldHidden(pWorld.Name, 0)
        pPlayer.SendMessage("&aWorld \"&e%s&a\" is no longer being hidden" %pWorld.Name)


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
        #Rename Backups
        if os.path.exists("Backups/%s" %OldName):
            shutil.move("Backups/%s" %OldName, "Backups/%s" %NewName)

        #Update the rank-cache
        pPlayer.ServerControl.SetWorldRank(NewName, pPlayer.ServerControl.GetWorldRank(OldName))
        pPlayer.ServerControl.SetWorldHidden(NewName, pPlayer.ServerControl.IsWorldHidden(OldName))
        del pPlayer.ServerControl.WorldRankCache[OldName.lower()]
        del pPlayer.ServerControl.WorldHideCache[OldName.lower()]
        #Finally, change zones.
        for pZone in pPlayer.ServerControl.GetZones():
            if pZone.Map.lower() == OldName:
                pZone.SetMap(NewName)
        pPlayer.SendMessage("&aSuccessfully renamed map %s to %s" %(OldName,NewName))

######################
#OWNER COMMANDS HERE #
######################

class FlushBlockLogCmd(CommandObject):
    '''Flushes the worlds blocklog to disk'''
    def Run(self,pPlayer,Args,Message):
        pPlayer.GetWorld().FlushBlockLog()
        pPlayer.SendMessage("&aWorld %s's Blocklog has been flushed to disk." %pPlayer.GetWorld().Name)
class DeleteWorldCmd(CommandObject):
    '''Deletes a world from the server'''
    def Run(self,pPlayer,Args,Message):
        WorldName = Args[0].lower()
        if pPlayer.ServerControl.WorldExists(WorldName) == False:
            pPlayer.SendMessage("&4That world does not exist!")
            return
        #Is it an idle world? (Easy)
        ActiveWorlds,IdleWorlds = pPlayer.ServerControl.GetWorlds()
        if ActiveWorlds[0].Name.lower() == WorldName:
            pPlayer.SendMessage("&4You cannot delete the default world!")
            return

        for pWorld in ActiveWorlds:
            if pWorld.Name.lower() == WorldName:
                pWorld.Unload()
        #Get the lists again, they may of changed at this stage of the process
        #(If the world was active, it will now be in the idle list due to being unloaded)
        ActiveWorlds,IdleWorlds = pPlayer.ServerControl.GetWorlds()
        #The world should now be in an unloading/unloaded state.
        for IdleWorldName in IdleWorlds:
            if IdleWorldName.lower() == WorldName:
                #erasing time
                WorldName = IdleWorldName
                os.remove("Worlds/%s.save" %WorldName)
                ZoneList = pPlayer.ServerControl.GetZones()[:] #Copy so we can erase from the list during iteration
                for pZone in ZoneList:
                    if pZone.Map == WorldName:
                        pPlayer.ServerControl.DeleteZone(pZone)
                        pZone.Delete()
                if pPlayer.ServerControl.EnableBlockLogs:
                    #This can fail due to multi-threaded context, unfortunately.
                    #Design flaw.
                    try:
                        os.remove("Worlds/BlockLogs/%s.db" %WorldName)
                    except:
                        pass
                pPlayer.ServerControl.IdleWorlds.remove(WorldName)
                del pPlayer.ServerControl.WorldRankCache[WorldName.lower()]
                del pPlayer.ServerControl.WorldHideCache[WorldName.lower()]
                pPlayer.SendMessage("&aSuccessfully deleted world \"&f%s&a\"" %WorldName)
                return #Done...


class CommandHandler(object):
    '''Stores all the commands avaliable on opticraft and processes any command messages'''
    def __init__(self,ServerControl):
        self.CommandTable = OrderedDict()
        self.ServerControl = ServerControl
        self.LogFile = None
        if ServerControl.LogCommands:
            try:
                self.LogFile = open("Logs/commands.log","a")
            except IOError:
                Console.Warning("Logging","Unable to open file \"Logs/commands.log\" - logging disabled")
        #Populate the command table here
        ######################
        #PUBLIC COMMANDS HERE#
        ######################
        self.AddCommand("rules", RulesCmd, 'guest', 'Displays a list of rules for this server', '', 0)
        self.AddCommand("about", AboutCmd, 'guest', 'Displays history of a block when you destroy/create one', '', 0)
        self.AddCommand("cmdlist", CmdListCmd, 'guest', 'Lists all commands available to you', '', 0)
        self.AddCommand("commands", CmdListCmd, 'guest', 'Lists all commands available to you', '', 0,Alias=True)
        self.AddCommand("help", HelpCmd, 'guest', 'Gives help on a specific command. Usage: /help <cmd>', 'Incorrect syntax! Usage: /help <cmd>. /cmdlist for a list of commands', 1)
        self.AddCommand("worlds", WorldsCmd, 'guest', 'Lists all available worlds', '', 0)
        self.AddCommand("maps", WorldsCmd, 'guest', 'Lists all available worlds', '', 0,Alias=True)
        self.AddCommand("join", JoinWorldCmd, 'guest', 'Changes the world you are in', 'Incorrect syntax! Usage: /join <world>. Use /worlds to see a list of worlds.', 1)
        self.AddCommand("j", JoinWorldCmd, 'guest', 'Changes the world you are in', 'Incorrect syntax! Usage: /join <world>. Use /worlds to see a list of worlds.', 1,Alias=True)
        self.AddCommand("warp", JoinWorldCmd, 'guest', 'Changes the world you are in', 'Incorrect syntax! Usage: /join <world>. Use /worlds to see a list of worlds.', 1,Alias=True)
        self.AddCommand("goto", JoinWorldCmd, 'guest', 'Changes the world you are in', 'Incorrect syntax! Usage: /join <world>. Use /worlds to see a list of worlds.', 1,Alias=True)
        self.AddCommand("grass", GrassCmd, 'guest', 'Allows you to place grass', '', 0)
        self.AddCommand("paint", PaintCmd, 'guest', 'When you destroy a block it will be replaced by what you are currently holding', '', 0)
        self.AddCommand("sinfo", sInfoCmd, 'guest', 'Displays information about the server', '', 0)
        self.AddCommand("info", sInfoCmd, 'guest', 'Displays information about the server', '', 0,Alias = True)
        self.AddCommand("version", VersionCmd, 'guest', 'Displays information about the server', '', 0,Alias = True) #Hidden
        self.AddCommand("credits", CreditsCmd, 'guest', 'Displays information about the server', '', 0,Alias = True) #Hidden
        self.AddCommand("stats", StatsCmd, 'guest', 'Displays a players statistics. Usage: /stats [Username]', '', 0)
        self.AddCommand("togglenotifications", ToggleNotificationsCmd, 'guest', 'Turns join/leave messages on or off', '', 0)
        self.AddCommand("ranks", RanksCmd, 'guest', 'Displays information on all the ranks', '', 0)
        self.AddCommand("whois", PlayerInfoCmd, 'guest', 'Returns information on a player', 'Incorrect syntax! Usage: /whois <username>',1)
        self.AddCommand("players", PlayerListCmd, 'guest', 'Lists all online players', '',0)
        self.AddCommand("me", EmoteCmd, 'guest', 'Emotes an aceiont', 'Incorrect syntax! Usage: /me <message>',1)
        self.AddCommand("emote", EmoteCmd, 'guest', 'Emotes an aceiont', 'Incorrect syntax! Usage: /emote <message>',1,Alias=True)
        self.AddCommand("r", ReplyCmd, 'guest', 'Replys to the last person who sent you a PM', 'Incorrect syntax! Usage: /reply <Message>',1)
#Zone commands
        self.AddCommand("zinfo", ZoneInfoCmd, 'guest', 'Returns information on a zone.', 'Incorrect syntax! Usage: /zinfo <zone>', 1)
        self.AddCommand("zlist", ZoneListCmd, 'guest', 'Lists all zones on the map', '', 0)
        self.AddCommand("ztest", ZoneTestCmd, 'guest', 'Checks to see if you are in a zone.', '', 0)
        self.AddCommand("zaddbuilder", AddZoneBuilderCmd, 'guest', 'Adds a builder to a zone', 'Incorrect syntax! Usage: /zaddbuilder <zone> <username>', 2)
        self.AddCommand("zdelbuilder", DelZoneBuilderCmd, 'guest', 'Deletes a builder from a zone', 'Incorrect syntax! Usage: /zdelbuilder <zone> <username>', 2)
        self.AddCommand("zsetrank", zSetMinRankCmd, 'guest', 'Changes the minimum non zone-builder rank required to build on this zone', 'Incorrect syntax! Usage: /zsetrank <zone> <rank>', 2)
        self.AddCommand("zsetowner", zChangeOwnerCmd, 'guest', 'Changes the owner of a zone', 'Incorrect syntax! Usage: /zsetowner <zone> <username>', 2)

        ########################
        #BUILDER COMMANDS HERE #
        ########################
        self.AddCommand("water", WaterCmd, 'builder', 'Allows you to place water', '', 0)
        self.AddCommand("lava", LavaCmd, 'builder', 'Allows you to place lava', '', 0)
        self.AddCommand("appear", AppearCmd, 'builder', 'Teleports you to a players location', 'Incorrect syntax! Usage: /appear <username>', 1)
        self.AddCommand("tp", AppearCmd, 'builder', 'Teleports you to a players location', 'Incorrect syntax! Usage: /appear <username>', 1, Alias=True)
        #########################
        #OPERATOR COMMANDS HERE #
        #########################
        self.AddCommand("solid", SolidCmd, 'operator', 'Allows you to place adminium', '', 0)
        self.AddCommand("ban", BanCmd, 'operator', 'Bans a player from the server', 'Incorrect syntax! Usage: /ban <username>', 1)
        self.AddCommand("unban", UnbanCmd, 'operator', 'Unbans a player from the server', 'Incorrect syntax! Usage: /unban <username>', 1)
        self.AddCommand("kick", KickCmd, 'operator', 'Kicks a player from the server', 'Incorrect syntax! Usage: /kick <username> [reason]', 1)
        self.AddCommand("playerinfo", PlayerInfoCmd, 'operator', 'Returns information on a player', 'Incorrect syntax! Usage: /playerinfo <username>',1,Alias=True)
        self.AddCommand("summon", SummonCmd, 'operator', 'Teleports a player to your location', 'Incorrect syntax! Usage: /summon <username>', 1)
        self.AddCommand("undoactions", UndoActionsCmd, 'operator', 'Undoes all of a a players actions in the last X seconds', 'Incorrect Syntax! Usage: /undoactions <username> <seconds>',2)
        self.AddCommand("invisible", InvisibleCmd, 'operator', "Makes you invisible to other players", "", 0)
        self.AddCommand("destroytower",DestroyTowerCmd,'operator', 'Destroys a vertical tower of shit','',0,Alias=True) #Hidden command
        self.AddCommand("ModifyRank", ModifyRankCmd, 'operator', 'Modify\'s a players rank.', 'Incorrect syntax. Usage: /addrank <username> <rank>', 2)
        ######################
        #ADMIN COMMANDS HERE #
        ######################
        self.AddCommand("addipban", AddIPBanCmd, 'admin', 'Ip bans a player from the server.', 'Incorrect syntax! Usage: /addipban <ip/username>', 1)
        self.AddCommand("ipban", AddIPBanCmd, 'admin', 'Ip bans a player from the server.', 'Incorrect syntax! Usage: /addipban <ip/username>', 1,Alias=True)
        self.AddCommand("delipban", DelIPBanCmd, 'admin', 'Removes an IP ban', 'Incorrect syntax! Usage: /delipban <ip/username>', 1)
        self.AddCommand("save", SaveCmd, 'admin', 'Saves all actively running worlds', '', 0)
        self.AddCommand("backup", BackupCmd, 'admin', 'Backs up all actively running worlds', '', 0)
        self.AddCommand("setspawn", SetSpawnCmd, 'admin', 'Changes the worlds default spawn location to where you are standing', '', 0)
        self.AddCommand("tempop", TempOpCmd, 'admin', 'Grants a user operator privledges until they log off', 'Incorrect syntax! Usage: /tempop <username>', 1)
        self.AddCommand("worldsetrank", WorldSetRankCmd, 'admin', 'Sets the minimum rank to build on a world', 'Incorrect syntax. Usage: /worldsetrank <world> <rank>', 2)
        self.AddCommand("zCreate", ZCreateCmd, 'admin', 'Creates a restricted zone', 'Incorrect syntax. Usage: /zCreate <name> <owner> <height>', 3)
        self.AddCommand("zDelete", ZDeleteCmd, 'admin', 'Deletes a restricted zone', 'Incorrect syntax. Usage: /zDelete <name>', 1)
        self.AddCommand("createworld", CreateWorldCmd, 'admin', 'Creates a new world.', 'Incorrect syntax. Usage: /createworld <name> <length> <width> <height>', 4)
        self.AddCommand("setdefaultworld", SetDefaultWorldCmd, 'admin', 'Sets the world you specify to be the default one', 'Incorrect syntax. Usage: /setdefaultworld <name>', 1)
        self.AddCommand("renameworld", RenameWorldCmd, 'admin', 'Renames a world', 'Incorrect syntax! Usage: /renameworld <oldname> <newname>', 2)
        self.AddCommand("hideworld", HideWorldCmd, 'admin', 'Hides a world from the /worlds list', 'Incorrect syntax! Usage: /hideworld <worldname>', 1)
        self.AddCommand("unhideworld", UnHideWorldCmd, 'admin', 'Unhides a world from the /worlds list', 'Incorrect syntax! Usage: /unhideworld <worldname>', 1)
        self.AddCommand("loadworld", LoadWorldCmd, 'admin', 'Loads a world which has been added to the Worlds folder', 'Incorrect syntax! Usage: /loadworld <name>', 1)
        self.AddCommand("loadtemplate", LoadTemplateCmd, 'admin', 'Loads a template world from the Templates directory', 'Incorrect syntax! Usage: /loadtemplate <templatename> <worldname>', 2)
        self.AddCommand("showtemplates", ShowTemplatesCmd, 'admin', 'Lists all the available world templates', '', 0)
        ######################
        #OWNER COMMANDS HERE #
        ######################
        self.AddCommand("flushblocklog",FlushBlockLogCmd,'owner', 'Flushes the worlds blocklog to disk','',0)
        self.AddCommand("removeworld",DeleteWorldCmd,'owner', 'Deletes a world from the server','Incorrect syntax! Usage: /removeworld <worldname>',1)

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
        self.CommandTable[Command.lower()] = CmdObj(self,Permissions,HelpMsg,ErrorMsg,MinArgs,Command,Alias)

    def OverrideCommandPermissions(self,Command,NewPermission):
        CmdObj = self.CommandTable.get(Command.lower(),None)
        if CmdObj != None:
            CmdObj.Permissions = NewPermission.lower()
            CmdObj.PermissionLevel = self.ServerControl.GetRankLevel(NewPermission.lower())
            return True
        return False