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

'''Plugin support'''
import inspect
from core.console import Console, LOG_LEVEL_DEBUG
import sys
import json
import traceback

sys.path.append("plugins")

class Hooks:
    ON_SERVER_START = 0
    ON_PLAYER_CONNECT = 1
    ON_PLAYER_DISCONNECT = 2
    ON_PLAYER_DATA_LOADED = 3
    ON_PLAYER_KICK = 4
    ON_ATTEMPT_PLACE_BLOCK = 5
    ON_POST_PLACE_BLOCK = 6
    ON_PLAYER_CHAT = 7
    ON_PLAYER_CHANGE_WORLD = 8
    ON_WORLD_LOAD = 9
    ON_WORLD_UNLOAD = 10
    ON_WORLD_METADATA_LOAD = 11
    ON_PLAYER_POSITION_UPDATE = 12
    ON_WORLD_RENAME = 13
    ON_WORLD_DELETE = 14
    ON_SERVER_TICK = 15
    ON_SERVER_SHUTDOWN = 16
    ON_PLAYER_EMOTE = 17

class PluginBase(object):
    #These numbers do not include the "self" argument, though all objects need to have this!
    HookSpecs = {
        Hooks.ON_SERVER_START: 0,
        Hooks.ON_PLAYER_CONNECT: 1,
        Hooks.ON_PLAYER_DISCONNECT: 1,
        Hooks.ON_PLAYER_DATA_LOADED: 1,
        Hooks.ON_PLAYER_KICK: 4,
        Hooks.ON_ATTEMPT_PLACE_BLOCK: 6,
        Hooks.ON_POST_PLACE_BLOCK: 7,
        Hooks.ON_PLAYER_CHAT: 2,
        Hooks.ON_PLAYER_CHANGE_WORLD: 3,
        Hooks.ON_WORLD_LOAD: 1,
        Hooks.ON_WORLD_UNLOAD: 1,
        Hooks.ON_WORLD_METADATA_LOAD: 1,
        Hooks.ON_PLAYER_POSITION_UPDATE: 6,
        Hooks.ON_WORLD_RENAME: 2,
        Hooks.ON_WORLD_DELETE: 1,
        Hooks.ON_SERVER_TICK: 0,
        Hooks.ON_SERVER_SHUTDOWN: 0,
        Hooks.ON_PLAYER_EMOTE: 2,
    }

    def __init__(self, PluginMgr, ServerControl, Name):
        self.PluginMgr = PluginMgr
        self.ServerControl = ServerControl
        self.ModuleName = Name

    def __repr__(self):
        return self.ModuleName

    def OnLoad(self):
        '''Called when the plugin is loaded
        ...Register all your commands and hooks at this stage'''
        pass

    def OnUnload(self):
        '''Allows the plguin to tidy up any additional stuff it has
        ...Besides hooks and commands (PluginMgr will handle them)'''
        pass

    def AddCommand(self, Command, CmdObj, Permissions, HelpMsg, ErrorMsg, MinArgs, Hidden = False):
        self.PluginMgr.RegisterCommand(self, CmdObj(self.ServerControl.CommandHandle, Permissions, HelpMsg, ErrorMsg, MinArgs, Command, Hidden))
class Hook(object):
    '''Simple struct to store Hook info'''
    __slots__ = ['Plugin', 'Function']
    def __init__(self, Plugin, Function):
        self.Plugin = Plugin
        self.Function = Function

class PluginException(Exception):
    pass

class PluginManager(object):
    def __init__(self, ServerControl):
        self.ServerControl = ServerControl
        self.Hooks = dict() #Value is a list, Key is an integer from Hooks.
        self.Commands = dict() #Key is string (PluginModule), value is list of commandobjects
        self.Plugins = set() # A set of PluginBase Objects.
        self.PluginModules = list() #List of loaded plugin names
        self.SetupHookList()
        
    def SetupHookList(self):
        for Key in PluginBase.HookSpecs.iterkeys():
            self.Hooks[Key] = list()

    def LoadPlugins(self):
        Plugins = self.ServerControl.ConfigValues.GetItems("plugins")
        Console.Out("PluginMgr", "Loading plugins...")
        for PluginField in Plugins:
            PluginFile = PluginField[0]
            Enabled = PluginField[1]
            if Enabled != "0":
                self.LoadPlugin(PluginFile)
        Console.Out("PluginMgr", "Finished loading plugins...")

    def LoadPlugin(self, PluginFile):
        try:
            PluginModule = __import__("%s" % PluginFile)
            reload(PluginModule) #Ensure the most up to date version from disk is loaded
        except Exception, e:
            Console.Warning("PluginMgr", "Plugin file %s could not be imported (%s)" % (PluginFile, e))
            return False
        self.PluginModules.append(PluginFile.lower())
        #Search for PluginBase objects to instantiate
        for Key in PluginModule.__dict__:
            Value = PluginModule.__dict__[Key]
            if type(Value) == type and issubclass(Value, PluginBase) and Value is not PluginBase:
                #Make a plugin!
                pPlugin = None
                try:
                    pPlugin = Value(self, self.ServerControl, PluginFile)
                    Console.Out("PluginMgr", "Loaded object \"%s\" from plugin \"%s\"" % (Key, PluginFile))
                    self.Plugins.add(pPlugin)
                    pPlugin.OnLoad()
                except Exception as exc:
                    if pPlugin in self.Plugins: #The plugin may of added some hooks or commands before it exploded.
                        self.RemovePluginHooks(pPlugin)
                        self.RemovePluginCommands(pPlugin.ModuleName)
                        self.Plugins.remove(pPlugin)
                    Console.Warning("PluginMgr", "Error loading plugin object \"%s\" from file \"%s\"" % (Key, PluginFile))
                    if Console.LogLevel == LOG_LEVEL_DEBUG:
                        Console.Debug("PluginMgr", "Exception: %s" % str(exc))
                        Console.Debug("PluginMgr", "Callstack:")
                        traceback.print_exc()
                    continue
        return True

    def UnloadPlugin(self, PluginName):
        '''Unloads all pluginbase objects in module pluginname'''
        PluginName = PluginName.lower()
        if PluginName in self.PluginModules:
            self.PluginModules.remove(PluginName)
        #Remove commands
        self.RemovePluginCommands(PluginName)

        ToRemove = list()
        for pPlugin in self.Plugins:
            if pPlugin.ModuleName.lower() == PluginName:
                ToRemove.append(pPlugin)

        while len(ToRemove) > 0:
            pPlugin = ToRemove.pop()
            self.RemovePluginHooks(pPlugin)
            #All hooks removed, time for commands
            #TODO: Commands! >:)
            pPlugin.OnUnload()
            self.Plugins.remove(pPlugin) #Goodbye, cruel world!
        Console.Out("PluginMgr", "Successfully unloaded plugin \"%s\"" % PluginName)
        return True
    
    def RemovePluginHooks(self, pPlugin):
        for HookName in self.Hooks:
            DeadHooks = list()
            HookList = self.Hooks[HookName]
            for pHook in HookList:
                if pHook.Plugin == pPlugin:
                    DeadHooks.append(pHook)
            while len(DeadHooks) > 0:
                HookList.remove(DeadHooks.pop())        
    
    def RemovePluginCommands(self, PluginName):
        for Module in self.Commands:
            if Module == PluginName:
                for CommandObj in self.Commands[Module]:
                    self.ServerControl.CommandHandle.RemoveCommand(CommandObj)
                del self.Commands[PluginName]
                break        
    
    def RegisterHook(self, Plugin, Function, HookName):
        '''Registers the plugin and function for the hook'''
        NumArgs = PluginBase.HookSpecs.get(HookName, None)
        if NumArgs is None:
            raise PluginException("Hook %s does not exist!" % HookName)
        NumArgs += 1 #Include the 'self' argument
        FuncArgs = len(inspect.getargspec(Function)[0])
        if FuncArgs != NumArgs:
            raise PluginException("Hook %s requires %d arguments. Function %s provides %d" 
                % (HookName, NumArgs, Function.func_name, FuncArgs))

        HookList = self.Hooks.get(HookName, list())
        HookList.append(Hook(Plugin, Function))
        if HookName not in self.Hooks:
            self.Hooks[HookName] = HookList

    def RemoveHook(self, Plugin, HookName):
        HookList = self.Hooks[HookName]
        FoundHook = False
        for Hook in HookList:
            if Hook.Plugin == Plugin:
                HookList.remove(Hook)
                FoundHook = True
                break
        if FoundHook == False:
            Console.Warning("PluginMgr", "Plugin %s tried to remove non-existant hook \"%s\"" % (Plugin, HookName))

    def RegisterCommand(self, Plugin, CommandObj):
        if self.ServerControl.CommandHandle.CommandTable.has_key(CommandObj.Name.lower()):
            return
        pList = self.Commands.get(Plugin.ModuleName, None)
        if pList is None:
            pList = list()
            self.Commands[Plugin.ModuleName] = pList
        pList.append(CommandObj)
        self.ServerControl.CommandHandle.AddCommandObj(CommandObj)

    #=================================
    #Hook events are all listed below!
    #=================================

    def OnServerStart(self):
        '''Called when the server finishes up its startup routine'''
        for Hook in self.Hooks[Hooks.ON_SERVER_START]:
            Hook.Function()

    def OnPlayerConnect(self, pPlayer):
        '''Called when a player successfully authenticates with the server.
        ...At this stage they will not be on a world nor have any data loaded'''
        for Hook in self.Hooks[Hooks.ON_PLAYER_CONNECT]:
            Hook.Function(pPlayer)
    def OnPlayerDataLoaded(self, pPlayer):
        '''Called when a players data is loaded from the database'''
        for Hook in self.Hooks[Hooks.ON_PLAYER_DATA_LOADED]:
            Hook.Function(pPlayer)

    def OnDisconnect(self, pPlayer):
        '''Called when a player leaves the server for whatever reason (Kick,Ban,Quit,etc)'''
        for Hook in self.Hooks[Hooks.ON_PLAYER_DISCONNECT]:
            Hook.Function(pPlayer)

    def OnKick(self, pPlayer, Initiator, Reason, Ban):
        '''Called when a player is kicked or banned. Ban is true when it is a Ban (D'oh!)'''
        for Hook in self.Hooks[Hooks.ON_PLAYER_KICK]:
            Hook.Function(pPlayer, Initiator, Reason, Ban)

    #FailSilently is a special return type that will disallow placement, but does not let the client know it failed
    FailSilently = -1
    def OnAttemptPlaceBlock(self, pWorld, pPlayer, BlockValue, x, y, z):
        '''Plugins may return false to disallow the block placement'''
        Allowed = True
        for Hook in self.Hooks[Hooks.ON_ATTEMPT_PLACE_BLOCK]:
            Result = Hook.Function(pWorld, pPlayer, BlockValue, x, y, z)
            if Result == False:
                Allowed = Result
            if Result == PluginManager.FailSilently and Allowed != PluginManager.FailSilently:
                Allowed = Result
        return Allowed

    def OnPostPlaceBlock(self, pWorld, pPlayer, OldValue, BlockValue, x, y, z):
        '''Called when a block is changed on the map.
        ...IMPORTANT: The pPlayer reference may be null in the event
        ...of an automated (non-player) block change!'''
        for Hook in self.Hooks[Hooks.ON_POST_PLACE_BLOCK]:
            Hook.Function(pWorld, pPlayer, OldValue, BlockValue, x, y, z)

    def OnChat(self, pPlayer, ChatMessage):
        '''Called when a player types a message
        ...This fires for any message besides slash "/" commands and PM's'''
        Result = True
        for Hook in self.Hooks[Hooks.ON_PLAYER_CHAT]:
            if Hook.Function(pPlayer, ChatMessage) == False:
                Result = False
        return Result

    def OnChangeWorld(self, pPlayer, OldWorld, NewWorld):
        '''Called when a player changes world, be it via
        .../join, /tp, /summon, or any other means'''
        for Hook in self.Hooks[Hooks.ON_PLAYER_CHANGE_WORLD]:
            Hook.Function(pPlayer, OldWorld, NewWorld)

    def OnWorldLoad(self, pWorld):
        '''Called when a world object is created'''
        for Hook in self.Hooks[Hooks.ON_WORLD_LOAD]:
            Hook.Function(pWorld)

    def OnWorldUnload(self, pWorld):
        '''Called when a world is unloaded'''
        for Hook in self.Hooks[Hooks.ON_WORLD_UNLOAD]:
            Hook.Function(pWorld)
            
    def OnWorldMetaDataLoad(self, WorldName):
        '''Called when the worlds meta data is loaded and deserialized'''
        for Hook in self.Hooks[Hooks.ON_WORLD_METADATA_LOAD]:
            Hook.Function(WorldName)
    
    def OnPlayerPositionUpdate(self, pPlayer, x, y, z, o, p):
        '''Called when a player's position changes.
        ...the X, Y, Z values are in map coordinates.'''
        for Hook in self.Hooks[Hooks.ON_PLAYER_POSITION_UPDATE]:
            Hook.Function(pPlayer, x, y, z, o, p)
            
    def OnWorldRename(self, OldName, NewName):
        '''Called prior to a world being named. World still has OldName'''
        for Hook in self.Hooks[Hooks.ON_WORLD_RENAME]:
            Hook.Function(OldName, NewName)
    
    def OnWorldDelete(self, WorldName):
        '''Called prior to a world being erased. World still exists.'''
        for Hook in self.Hooks[Hooks.ON_WORLD_DELETE]:
            Hook.Function(WorldName)
        
    def OnServerTick(self):
        '''Called every "tick" of the server, approximately every 5ms, depending on server load'''
        for Hook in self.Hooks[Hooks.ON_SERVER_TICK]:
            Hook.Function()
            
    def OnServerShutdown(self):
        '''Called when the server is shut down'''
        for Hook in self.Hooks[Hooks.ON_SERVER_SHUTDOWN]:
            Hook.Function()           

    def OnEmote(self, pPlayer, Message):
        '''Called when a player uses the /me command or any other form of emoting'''
        for Hook in self.Hooks[Hooks.ON_PLAYER_EMOTE]:
            Hook.Function(pPlayer, Message)
