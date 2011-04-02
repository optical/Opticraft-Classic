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
from core.console import Console
from core.constants import UnicodeToStr
import sys
import json

sys.path.append("plugins")

class Hooks:
    ON_START = 0
    ON_CONNECT = 1
    ON_DISCONNECT = 2
    ON_PLAYER_DATA_LOADED = 3
    ON_KICK = 4
    ON_ATTEMPT_PLACE_BLOCK = 5
    ON_POST_PLACE_BLOCK = 6
    ON_CHAT = 7
    ON_CHANGE_WORLD = 8
    ON_WORLD_LOAD = 9
    ON_WORLD_UNLOAD = 10

class PluginBase(object):
    #These numbers do not include the "self" argument, though all objects need to have this!
    HookSpecs = {
        Hooks.ON_START: 0,
        Hooks.ON_CONNECT: 1,
        Hooks.ON_DISCONNECT: 1,
        Hooks.ON_PLAYER_DATA_LOADED: 1,
        Hooks.ON_KICK: 4,
        Hooks.ON_ATTEMPT_PLACE_BLOCK: 6,
        Hooks.ON_POST_PLACE_BLOCK: 6,
        Hooks.ON_CHAT: 2,
        Hooks.ON_CHANGE_WORLD: 3,
        Hooks.ON_WORLD_LOAD: 1,
        Hooks.ON_WORLD_UNLOAD: 1,
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

    def AddCommand(self, Command, CmdObj, Permissions, HelpMsg, ErrorMsg, MinArgs, Alias = False):
        self.PluginMgr.RegisterCommand(self, CmdObj(self.ServerControl.CommandHandle, Permissions, HelpMsg, ErrorMsg, MinArgs, Command, Alias))
class Hook(object):
    '''Simple struct to store Hook info'''
    def __init__(self, Plugin, Function):
        self.Plugin = Plugin
        self.Function = Function

class PluginException(Exception):
    pass

class PluginManager(object):
    def __init__(self, ServerControl):
        self.ServerControl = ServerControl
        self.Hooks = dict() #Value is a list, Key is a lower case string
        self.Commands = dict() #Key is string (PluginModule), value is list of commandobjects
        self.Plugins = set() # A set of PluginBase Objects.
        self.PluginModules = list() #List of loaded plugin names
        self._Emptylist = list() #Dummy object. Used so we do not have to create empty lists when searching for hooks that dont exist
        
    def _GetHooks(self, Name):
        return self.Hooks.get(Name, self._Emptylist)

    def LoadPlugins(self):
        Plugins = self.ServerControl.ConfigValues.GetItems("plugins")
        Console.Out("PluginMgr", "Loading plugins...")
        for PluginField in Plugins:
            PluginFile = PluginField[0]
            Enabled = PluginField[1]
            if Enabled != False:
                self.LoadPlugin(PluginFile)
        Console.Out("PluginMgr", "Finished loading plugins...")

    def LoadPlugin(self, PluginFile):
        try:
            PluginModule = __import__("%s" % PluginFile)
            reload(PluginModule) #Ensure the most up to date version from disk is loaded
        except ImportError:
            Console.Warning("PluginMgr", "Plugin file %s could not be imported" % PluginFile)
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
                    if pPlugin in self.Plugins:
                        self.Plugins.remove(pPlugin)
                    Console.Warning("PluginMgr", "Error loading plugin object \"%s\" from file \"%s\"" % (Key, PluginFile))
                    Console.Debug("PluginMgr", "Exception: %s" % str(exc))
                    continue
        return True

    def UnloadPlugin(self, PluginName):
        '''Unloads all pluginbase objects in module pluginname'''
        PluginName = PluginName.lower()
        if PluginName in self.PluginModules:
            self.PluginModules.remove(PluginName)
        #Remove commands
        for Module in self.Commands:
            if Module == PluginName:
                for CommandObj in self.Commands[Module]:
                    self.ServerControl.CommandHandle.RemoveCommand(CommandObj)
                del self.Commands[PluginName]
                break

        ToRemove = list()
        for pPlugin in self.Plugins:
            if pPlugin.ModuleName.lower() == PluginName:
                ToRemove.append(pPlugin)

        while len(ToRemove) > 0:
            pPlugin = ToRemove.pop()
            #Not very effecient code...
            for HookName in self.Hooks:
                DeadHooks = list()
                HookList = self.Hooks[HookName]
                for pHook in HookList:
                    if pHook.Plugin == pPlugin:
                        DeadHooks.append(pHook)
                while len(DeadHooks) > 0:
                    HookList.remove(DeadHooks.pop())
            #All hooks removed, time for commands
            #TODO: Commands! >:)
            pPlugin.OnUnload()
            self.Plugins.remove(pPlugin) #Goodbye, cruel world!
        Console.Out("PluginMgr", "Successfully unloaded plugin \"%s\"" % PluginName)
        return True

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
        for Hook in self._GetHooks(Hooks.ON_START):
            Hook.Function()

    def OnPlayerConnect(self, pPlayer):
        '''Called when a player successfully authenticates with the server.
        ...At this stage they will not be on a world nor have any data loaded'''
        for Hook in self._GetHooks(Hooks.ON_CONNECT):
            Hook.Function(pPlayer)
    def OnPlayerDataLoaded(self, pPlayer):
        '''Called when a players data is loaded from the database'''
        for Hook in self._GetHooks(Hooks.ON_PLAYER_DATA_LOADED):
            Hook.Function(pPlayer)

    def OnDisconnect(self, pPlayer):
        '''Called when a player leaves the server for whatever reason (Kick,Ban,Quit,etc)'''
        for Hook in self._GetHooks(Hooks.ON_DISCONNECT):
            Hook.Function(pPlayer)

    def OnKick(self, pPlayer, Initiator, Reason, Ban):
        '''Called when a player is kicked or banned. Ban is true when it is a Ban (D'oh!)'''
        for Hook in self._GetHooks(Hooks.ON_KICK):
            Hook.Function(pPlayer, Initiator, Reason, Ban)

    def OnAttemptPlaceBlock(self, pWorld, pPlayer, BlockValue, x, y, z):
        '''Plugins may return false to disallow the block placement'''
        Allowed = True
        for Hook in self._GetHooks(Hooks.ON_ATTEMPT_PLACE_BLOCK):
            Result = Hook.Function(pWorld, pPlayer, BlockValue, x, y, z)
            if Result == False:
                Allowed = False
        return Allowed

    def OnPostPlaceBlock(self, pWorld, pPlayer, BlockValue, x, y, z):
        '''Called when a block is changed on the map.
        ...IMPORTANT: The pPlayer reference may be null in the event
        ...of an automated (non-player) block change!'''
        for Hook in self._GetHooks(Hooks.ON_POST_PLACE_BLOCK):
            Hook.Function(pWorld, pPlayer, BlockValue, x, y, z)

    def OnChat(self, pPlayer, ChatMessage):
        '''Called when a player types a message
        ...This fires for any message besides slash "/" commands and PM's'''
        for Hook in self._GetHooks(Hooks.ON_CHAT):
            Hook.Function(pPlayer, ChatMessage)

    def OnChangeWorld(self, pPlayer, OldWorld, NewWorld):
        '''Called when a player changes world, be it via
        .../join, /tp, /summon, or any other means'''
        for Hook in self._GetHooks("on_changeworld"):
            Hook.Function(pPlayer, OldWorld, NewWorld)

    def OnWorldLoad(self, pWorld):
        '''Called when a world object is created'''
        for Hook in self._GetHooks(Hooks.ON_WORLD_LOAD):
            Hook.Function(pWorld)

    def OnWorldUnload(self, pWorld):
        '''Called when a world is unloaded'''
        for Hook in self._GetHooks(Hooks.ON_WORLD_UNLOAD):
            Hook.Function(pWorld)

class JsonSerializeableObject(object):
    '''Object which can more easily be encoded to and from json'''
    _ValidJsonTypes = frozenset([str, int, long, bool, dict, list, None, float])
    def _AsJson(self):
        '''This method returns a dictionary which can be encoded as json
        To do so it scans all attributes of the underlying object, adding
        key,values to a new dictionary if the key and value are valid json types.
        It does not however ensure that those values will succeed at being encoded as JSON.
        Eg: a list with a non-json type will be returned, and an exception will be throwing
        during the encoding process.
        This object is intended to allow you to have reference types in your object,
        while still being easily serialized to json'''
        JsonDict = dict()
        for Key, Value in self.__dict__.iteritems():
            tKey = type(Key)
            tValue = type(Value)
            if tKey in JsonSerializeableObject._ValidJsonTypes and tValue in JsonSerializeableObject._ValidJsonTypes:
                JsonDict[Key] = Value
        return JsonDict
    
    def FromJson(self, JsonDict):
        self.__dict__ = JsonDict
        

class PluginDict(object):
    '''Dictionary wrapper which ensures that key is always of type string
    ...Optionally can also ensure all values can be encoded to a json type'''
    def __init__(self, NonJsonValues = True):
        self._dictionary = dict()
        #Nasty piece of code.
        self.NonJsonValues = NonJsonValues
        self.ValidJsonTypes = frozenset([str, int, long, bool, dict, list, None, float, JsonSerializeableObject])

    def __getitem__(self, Key):
        if type(Key) != str:
            raise ValueError("Plugin Data key must be a string")
        return self._dictionary[Key]

    def __setitem__(self, Key, Value):
        if type(Key) != str:
            raise ValueError("Plugin Data key must be a string")
        if self.NonJsonValues == False:
            Valid = False
            for ValidType in self.ValidJsonTypes:
                if isinstance(Value, ValidType):
                    Valid = True
                    break
            if not Valid:
                raise ValueError("Values must be json encodeable")
        if type(Value) != JsonSerializeableObject:
            self._dictionary[Key] = Value
        else:
            self._dictionary[Key] = Value._AsJson()
            
    def __delitem__(self, Key):
        del self._dictionary[Key]

    def __contains__(self, Value):
        return Value in self._dictionary
    def __iter__(self):
        return self._dictionary.__iter__()
    def __reversed__(self):
        return self._dictionary.__reversed__()
    def __len__(self):
        return self._dictionary.__len__()
    def get(self, Key, Default):
        return self._dictionary.get(Key, Default)

    def AsJSON(self):
        assert(self.NonJsonValues == False)
        return json.dumps(self._dictionary, ensure_ascii = True)

    @staticmethod
    def FromJSON(JSON):
        NewDict = PluginDict()
        NewDict._dictionary = PluginDict.FromJSON(JSON)
        return NewDict

    @staticmethod
    def _FromJSON(JSON):
        '''returns a dictionary, not a plugindict'''
        TempDict = json.loads(JSON)
        return UnicodeToStr(TempDict)


class PluginData(PluginDict):
    def __init__(self):
        PluginDict.__init__(self, NonJsonValues = False)

    @staticmethod
    def FromJSON(JSON):
        NewDict = PluginData()
        NewDict._dictionary = PluginDict._FromJSON(JSON)
        return NewDict
