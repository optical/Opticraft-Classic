'''Command system for opticraft'''

from core.constants import *
from core.ordereddict import OrderedDict
from core.console import *
import time

class CommandObject(object):
    '''Parents class for all commands'''
    '''Abstract / Interface'''
    def __init__(self, CmdHandler, Permissions, HelpMsg, ErrorMsg, MinArgs, Name, Hidden = False):
        self.Permissions = Permissions
        self.PermissionLevel = CmdHandler.ServerControl.GetRankLevel(Permissions)
        self.Name = Name
        self.HelpMsg = HelpMsg
        self.ErrorMsg = ErrorMsg
        self.MinArgs = MinArgs
        self.CmdHandler = CmdHandler
        self.Aliases = set()
        self.Hidden = Hidden

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
    '''Stores all the commands available on opticraft and processes any command messages'''
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
        self._AddCommandObj(CmdObj, CmdObj.Name)
        for Alias in CmdObj.Aliases:
            self._AddCommandObj(CmdObj, Alias)
            
    def _AddCommandObj(self, CmdObj, Name):
        if self.CommandTable.has_key(Name.lower()):
            Console.Warning("Commands", "Command %s has been defined twice. Posible plugin conflict" % Name)
        self.CommandTable[Name.lower()] = CmdObj
        
        Permission = self.ServerControl.ConfigValues.GetValue("commandoverrides", Name, '')
        if Permission != '':
            if self.ServerControl.IsValidRank(Permission):
                Console.Out("CommandOverride", "Overrode command %s to rank %s" % (Name, Permission))
                self.OverrideCommandPermissions(CmdObj, Permission)
            else:
                Console.Warning("CommandOverride", "Failed to override command %s, rank %s does not exist" % (Name, Permission))
        self._SortCommands()
            
    def _SortCommands(self):
        self.CommandTable = OrderedDict(sorted(self.CommandTable.items(), key = lambda i: i[0]))

    def RemoveCommand(self, CmdObj):
        ToRemove = []
        for CommandName in self.CommandTable:
            if self.CommandTable[CommandName] == CmdObj:
                ToRemove.append(CommandName)
                
        while len(ToRemove) > 0:
            del self.CommandTable[ToRemove.pop()]

    def OverrideCommandPermissions(self, CmdObj, NewPermission):
        CmdObj.Permissions = NewPermission.lower()
        CmdObj.PermissionLevel = self.ServerControl.GetRankLevel(NewPermission.lower())
        return True
