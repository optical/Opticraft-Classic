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
from console import Console


class PluginBase(object):
    def __init__(self,PluginMgr,Name):
        self.PluginMgr = PluginMgr
        self.Name = Name

    def __repr__(self):
        return self.Name

    def OnLoad(self):
        '''Called when the plugin is loaded
        ...Register all your commands and hooks at this stage'''
        pass

    def UnLoad(self):
        '''Called when the plugin is unloaded
        ...Remove all hooks and commands here. Tidy up!'''
        pass

class Hook(object):
    '''Simple struct to store Hook info'''
    def __init__(self,Plugin,Function):
        self.Plugin = Plugin
        self.Function = Function

class PluginManager(object):
    def __init__(self,ServerControl):
        self.ServerControl = ServerControl
        self.Hooks = dict() #Value is a list, key is a lower case string
        self.Plugins = set()

    def _GetHooks(self,Name):
        return self.Hooks.get(Name,list())

    def LoadPlugins(self):
        Plugins = self.ServerControl.ConfigValues.GetItems("plugins")
        for PluginName in Plugins:
            try:
                PluginModule = __import__("plugins.%s" %PluginName, globals(), locals(), -1)
            except ImportError:
                Console.Warning("PluginMgr","Plugin %s could not be imported" %PluginName)
                continue
            #Search for PluginBase objects to instantiate
            for Key,Value in PluginModule.__dict__:
                if issubclass(type(Value),PluginBase):
                    #Make a plugin!
                    pPlugin = Value(self,Key)
                    pPlugin.OnLoad()
                    self.Plugins.Add(pPlugin)

    def RegisterHook(self,Plugin,Function,Hook):
        '''Registers the plugin and function for the hook'''
        HookList = self.Hooks.get(Hook.lower(),list())
        HookList.append(Hook(Plugin,Function))

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
        pass

    #Hook events are all listed below!
    def OnPlayerConnect(self,pPlayer):
        for Hook in self._GetHooks("on_connect"):
            Hook.Function(pPlayer)

    def OnDisconnect(self,pPlayer,Reason):
        '''Called when a player leaves the server for whatever reason (Kick,Ban,Quit,etc)'''
        for Hook in self._GetHooks("on_disconnect"):
            Hook.Function(pPlayer,Reason)

    def OnKick(self,pPlayer,Reason,Ban):
        '''Called when a player is kicked or banned. Ban is true when it is a Ban (D'oh!)'''
        for Hook in self._GetHooks("on_kick"):
            Hook.Function(pPlayer,Reason,Ban)

    def OnAttemptPlaceBlock(self,pPlayer,BlockValue):
        '''Plugins may return false to disallow the block placement'''
        Allowed = True
        for Hook in self._GetHooks("on_attemptplaceblock"):
            Result = Hook.Function(pPlayer,BlockValue)
            if Result == False:
                Allowed = False
        return Allowed

    def OnChat(self,pPlayer,ChatMessage):
        '''Called when a player types a message
        ...This fires for any message besides slash "/" commands
        ...Includes pm's!
        '''
        for Hook in self._GetHooks("on_chat"):
            Hook.Function(pPlayer,ChatMessage)

    def OnChangeWorld(self,pPlayer,OldWorld,NewWorld):
        '''Called when a player changes world, be it via
        .../join, /tp, /summon, or any other means'''
        for Hook in self._GetHooks("on_changeworld"):
            Hook.Function(pPlayer,OldWorld,NewWorld)
            
