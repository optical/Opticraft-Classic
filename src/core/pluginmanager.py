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
from core.console import Console
import sys
sys.path.append("plugins")
class PluginBase(object):
    def __init__(self,PluginMgr,ServerControl,Name):
        self.PluginMgr = PluginMgr
        self.ServerControl = ServerControl
        self.ModuleName = Name

    def __repr__(self):
        return self.ModuleName

    def OnLoad(self):
        '''Called when the plugin is loaded
        ...Register all your commands and hooks at this stage'''
        pass

    def UnLoad(self):
        '''Allows the plguin to tidy up any additional stuff it has
        ...Besides hooks and commands (PluginMgr will handle them)'''
        pass

    def AddCommand(self,Command,CmdObj,Permissions,HelpMsg,ErrorMsg,MinArgs,Alias=False):
         self.PluginMgr.RegisterCommand(self, CmdObj(self,Permissions,HelpMsg,ErrorMsg,MinArgs,Command,Alias))

class Hook(object):
    '''Simple struct to store Hook info'''
    def __init__(self,Plugin,Function):
        self.Plugin = Plugin
        self.Function = Function

class PluginManager(object):
    def __init__(self,ServerControl):
        self.ServerControl = ServerControl
        self.Hooks = dict() #Value is a list, Key is a lower case string
        self.Commands = dict() #Key is string (PluginModule), value is list of commandobjects
        self.Plugins = set() # A set of PluginBase Objects.
        self.PluginModules = list() #List of loaded plugin names

    def _GetHooks(self,Name):
        return self.Hooks.get(Name,list())

    def LoadPlugins(self):
        Plugins = self.ServerControl.ConfigValues.GetItems("plugins")
        Console.Out("PluginMgr","Loading plugins...")
        for PluginField in Plugins:
            PluginFile = PluginField[0]
            Enabled = PluginField[1]
            if Enabled != False:
                self.LoadPlugin(PluginFile)
        Console.Out("PluginMgr","Finished loading plugins...")

    def LoadPlugin(self,PluginFile):
        try:
            PluginModule = __import__("%s" %PluginFile)
        except ImportError:
            Console.Warning("PluginMgr","Plugin file %s could not be imported" %PluginFile)
            return False
        self.PluginModules.append(PluginFile.lower())
        #Search for PluginBase objects to instantiate
        for Key in PluginModule.__dict__:
            Value = PluginModule.__dict__[Key]
            if type(Value) == type and issubclass(Value,PluginBase) and Value is not PluginBase:
                #Make a plugin!
                try:
                    pPlugin = Value(self,self.ServerControl,PluginFile)
                    Console.Out("PluginMgr","Loaded object \"%s\" from plugin \"%s\"" %(Key,PluginFile))
                    self.Plugins.add(pPlugin)
                    pPlugin.OnLoad()
                except:
                    Console.Warning("PluginMgr","Error loading plugin object \"%s\" from file \"%s\"" %(Key,PluginFile))
                    continue
        return True

    def UnloadPlugin(self,PluginName):
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
        Console.Out("PluginMgr","Successfully unloaded plugin \"%s\"" %PluginName)
        return True
    def RegisterHook(self,Plugin,Function,HookName):
        '''Registers the plugin and function for the hook'''
        HookList = self.Hooks.get(HookName.lower(),list())
        HookList.append(Hook(Plugin,Function))
        if HookName.lower() not in self.Hooks:
            self.Hooks[HookName.lower()] = HookList

    def RemoveHook(self,Plugin,HookName):
        HookList = self.Hooks[HookName.lower()]
        FoundHook = False
        for Hook in HookList:
            if Hook.Plugin == Plugin:
                HookList.remove(Hook)
                FoundHook = True
                break
        if FoundHook == False:
            Console.Warning("PluginMgr","Plugin %s tried to remove non-existant hook \"%s\"" %(Plugin,HookName))

    def RegisterCommand(self,Plugin,CommandObj):
        pList = self.Commands.get(Plugin.ModuleName,None)
        if pList == None:
            pList = list()
            self.Commands[Plugin.ModuleName] = pList
        pList.append(CommandObj)
        self.ServerControl.CommandHandle.AddCommandObj(CommandObj)

    #=================================
    #Hook events are all listed below!
    #=================================

    def OnServerStart(self):
        '''Called when the server finishes up its startup routine'''
        for Hook in self._GetHooks("on_start"):
            Hook.Function()

    def OnPlayerConnect(self,pPlayer):
        '''Called when a player successfully authenticates with the server.
        ...At this stage they will not be on a world nor have any data loaded'''
        for Hook in self._GetHooks("on_connect"):
            Hook.Function(pPlayer)

    def OnDisconnect(self,pPlayer):
        '''Called when a player leaves the server for whatever reason (Kick,Ban,Quit,etc)'''
        for Hook in self._GetHooks("on_disconnect"):
            Hook.Function(pPlayer)

    def OnKick(self,pPlayer,Initiator,Reason,Ban):
        '''Called when a player is kicked or banned. Ban is true when it is a Ban (D'oh!)'''
        for Hook in self._GetHooks("on_kick"):
            Hook.Function(pPlayer,Initiator,Reason,Ban)

    def OnAttemptPlaceBlock(self,pPlayer,BlockValue,x,y,z):
        '''Plugins may return false to disallow the block placement'''
        Allowed = True
        for Hook in self._GetHooks("on_attemptplaceblock"):
            Result = Hook.Function(pPlayer,BlockValue,x,y,z)
            if Result == False:
                Allowed = False
        return Allowed

    def OnPostPlaceBlock(self,pPlayer,BlockValue,x,y,z):
        '''Called when a block is changed on the map.
        ...IMPORTANT: The pPlayer reference may be null in the event
        ...of an automated (non-player) block change!'''
        for Hook in self._GetHooks("on_postplaceblock"):
            Hook.Function(pPlayer,BlockValue,x,y,z)

    def OnChat(self,pPlayer,ChatMessage):
        '''Called when a player types a message
        ...This fires for any message besides slash "/" commands and PM's'''
        for Hook in self._GetHooks("on_chat"):
            Hook.Function(pPlayer,ChatMessage)

    def OnChangeWorld(self,pPlayer,OldWorld,NewWorld):
        '''Called when a player changes world, be it via
        .../join, /tp, /summon, or any other means'''
        for Hook in self._GetHooks("on_changeworld"):
            Hook.Function(pPlayer,OldWorld,NewWorld)

    def OnWorldLoad(self,pWorld):
        '''Called when a world object is created'''
        for Hook in self._GetHooks("on_worldload"):
            Hook.Function(pWorld)

    def OnWorldUnload(self,pWorld):
        '''Called when a world is unloaded'''
        for Hook in self._GetHooks("on_worldunload"):
            Hook.Function(pWorld)


class PluginDict(object):
    '''Dictionary wrapper which ensures that key is always of type string
    ...Optionally can alse ensure all values can be encoded to a json type'''
    def __init__(self, NonJsonValues = True):
        self._dictionary = dict()
        #Nasty piece of code.
        self.ValidJsonTypes = set([str,int,long,bool,dict,list,None,float])

    def __getitem__(self,Key):
        if type(Key) != str:
            raise ValueError("Plugin Data key must be a string")
        return self._dictionary[Key]

    def __setitem__(self,Key,Value):
        if type(Key) != str:
            raise ValueError("Plugin Data key must be a string")
        if NonJsonValues == false and type(Value) not in self.ValidJsonTypes:
            raise ValueError("Values must be json encodeable")

        self._dictionary[Key] = Value
    def __delitem__(self,Key):
        del self._dictionary[Key]

    def __contains__(self,Value):
        return Value in self._dictionary
    def __iter__(self):
        return self._dictionary.__iter__()
    def __reversed__(self):
        return self._dictionary.__reversed__()
    def __len__(self):
        return self._dictionary.__len__()
    def get(self,Key,Default):
        return self._dictionary.get(Key,Default)

    def AsJSON(self):
        assert(NonJsonValues == False)
        return json.dumps(self._dictionary,ensure_ascii=True)

    @staticmethod
    def FromJSON(self,JSON):
        NewDict = PluginDict()
        NewDict._dictionary = PluginDict.FromJSON(JSON)
        return NewDict

    @staticmethod
    def _FromJSON(self,JSON):
        '''returns a dictionary, not a plugindict'''
        TempDict = json.loads(JSON)
        NewDict = dict()
        for Key in TempDict:
            Value = TempDict[Key]
            if type(Key) == unicode:
                Key = str(Key)
            if Type(Value) == unicode:
                Value = str(Value)
            NewDict[Key] = Value
        return NewDict


class PluginData(PluginDict):
    def __init__(self):
        PluginDict.__init__(self,NonJsonValues = False)

    def FromJSON(self,JSON):
        NewDict = PluginData()
        NewDict._dictionary = PluginDict.FromJSON(JSON)
        return NewDict