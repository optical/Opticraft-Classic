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
import time

from core.console import *
class CommandObject(object):
    '''Parents class for all commands'''
    '''Abstract'''
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Alias = False):
        self.Permissions = Permissions
        self.PermissionLevel = CmdHandler.ServerControl.GetRankLevel(Permissions)
        self.Name = Name
        self.HelpMsg = HelpMsg
        self.ErrorMsg = ErrorMsg
        self.MinArgs = MinArgs
        self.CmdHandler = CmdHandler
        self.IsAlias = Alias

    def Execute(self, pPlayer, Message):
        '''Checks player has correct permissions and number of arguments'''
        if self.Permissions != '':
            if pPlayer.HasPermission(self.Permissions) == False:
                pPlayer.SendMessage("&RThat command requires %s+ rank" % self.Permissions)
                return
        Tokens = Message.split()[1:]
        Args = len(Tokens)
        if Args < self.MinArgs:
            pPlayer.SendMessage('%s%s' % ('&R', self.ErrorMsg))
            return
        else:
            self.Run(pPlayer, Tokens, Message)
            if self.CmdHandler.LogFile is not None and self.PermissionLevel >= self.CmdHandler.ServerControl.GetRankLevel('operator'):
                #Log all operator+ commands
                self.LogCommand(pPlayer, self.Name, Tokens)
    def LogCommand(self, pPlayer, Command, Args):
        TimeFormat = time.strftime("%d %b %Y [%H:%M:%S]", time.localtime())
        OutStr = "%s User %s (%s) used command %s with args: %s\n" % (TimeFormat, pPlayer.GetName(), pPlayer.GetIP(), Command, ' '.join(Args))
        self.CmdHandler.LogFile.write(OutStr)
    def Run(self, pPlayer, Args, Message):
        '''Subclasses will perform their work here'''
        pass

class CommandHandler(object):
    '''Stores all the commands avaliable on opticraft and processes any command messages'''
    def __init__(self, ServerControl):
        self.CommandTable = OrderedDict()
        self.ServerControl = ServerControl
        self.LogFile = None
        if ServerControl.LogCommands:
            try:
                self.LogFile = open("Logs/commands.log", "a")
            except IOError:
                Console.Warning("Logging", "Unable to open file \"Logs/commands.log\" - logging disabled")

    def HandleCommand(self, pPlayer, Message):
        '''Called when a player types a slash command'''
        if Message == '':
            pPlayer.SendMessage("&RPlease enter in a command!")
            return
        Tokens = Message.split()
        Command = Tokens[0].lower()
        if self.CommandTable.has_key(Command) == False:
            pPlayer.SendMessage("&RNo such command. Type /cmdlist for a list of commands")
            return
        else:
            CommandObj = self.CommandTable[Command]
            CommandObj.Execute(pPlayer, Message)

    def AddCommandObj(self, CmdObj):
        self.CommandTable[CmdObj.Name.lower()] = CmdObj
        Permission = self.ServerControl.ConfigValues.GetValue("commandoverrides", CmdObj.Name, '')
        if Permission != '':
            if self.ServerControl.IsValidRank(Permission):
                Console.Out("CommandOverride", "Overrode command %s to rank %s" % (CmdObj.Name, Permission))
                self.OverrideCommandPermissions(CmdObj, Permission)
            else:
                Console.Warning("CommandOverride", "Failed to override command %s, rank %s does not exist" % (CmdObj.Name, Permission))
        self._SortCommands()
    
    def _SortCommands(self):
        self.CommandTable = OrderedDict(sorted(self.CommandTable.items(), key = lambda i: i[0]))

    def RemoveCommand(self, CmdObj):
        del self.CommandTable[CmdObj.Name.lower()]

    def OverrideCommandPermissions(self, CmdObj, NewPermission):
        CmdObj.Permissions = NewPermission.lower()
        CmdObj.PermissionLevel = self.ServerControl.GetRankLevel(NewPermission.lower())
        return True
