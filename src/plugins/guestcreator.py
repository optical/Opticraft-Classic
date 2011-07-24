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
#       the documentation and/or other materials sprovided with the distribution.
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

##########################
#        SETTINGS        #
##########################
GUEST_NAME = "Guest" #Name of the main guest building world
TEMPLATE_NAME = "Guest" #Name of the template to be used to create a fresh guest world.
CREATION_PERIOD = 86400 #How often is a new guest world created?
HIDE_OLD_GUESTS = True #Should old guest worlds be set to hidden?
DELETE_OLD_GUESTS = True #Should old guests be deleted?
NO_OF_GUESTS_BEFORE_DELETION = 5 #How many guests should be kept before being deleted?
VERBOSE = True #Announce new worlds to ingame users?
###############################################
#        DO NOT EDIT BEYOND THIS LINE!        #
###############################################
from core.pluginmanager import PluginBase, Hooks
from core.commandhandler import CommandObject
from core.constants import *
from core.console import *
from core.world import MetaDataKey
import time
import shutil

class GuestCreator(PluginBase):
    def __init__(self, PluginMgr, ServerControl, Name):
        PluginBase.__init__(self, PluginMgr, ServerControl, Name)
        self.LastCreation = None
        
    def OnLoad(self):
        self.PluginMgr.RegisterHook(self, self.OnTick, Hooks.ON_SERVER_TICK)
        if self.ServerControl.HasStarted == False:
            self.PluginMgr.RegisterHook(self, self.OnServerStart, Hooks.ON_SERVER_START)
        else:
            self.Initialize()

    def OnServerStart(self):
        self.Initialize()
    
    def Initialize(self):
        GuestMetaData = self.ServerControl.GetWorldMetaData(GUEST_NAME)
        if GuestMetaData is None:
            self.CreateNewGuestWorld()
        else:
            self.LastCreation = GuestMetaData[MetaDataKey.CreationDate]    
    
    def OnTick(self):
        if self.LastCreation + CREATION_PERIOD < time.time():
            self.CreateNewGuestWorld()
    
    def GetId(self, Word, Prefix):
        if Word.startswith(Prefix):
            Index = Word.find(Prefix) + len(Prefix)
            if Index == len(Word):
                return None
            else:
                try:
                    return int(Word[Index:])
                except:
                    return None
        else:
            return None
        
    
    def FindLastGuestID(self):
        ActiveWorlds, InactiveWorlds = self.ServerControl.GetWorlds()
        LargestInactiveId = max([self.GetId(Word, GUEST_NAME) for Word in InactiveWorlds])
        LargestActiveId = max([self.GetId(World.Name, GUEST_NAME) for World in ActiveWorlds])
        LargestId = max((LargestInactiveId, LargestActiveId))
        if LargestId is None:
            LargestId = 0
        return LargestId
    
    def CreateNewGuestWorld(self):
        NewID = self.FindLastGuestID() + 1
        OldGuestName = GUEST_NAME + str(NewID)
        self.ServerControl.RenameWorld(GUEST_NAME, OldGuestName)
        shutil.copy("Templates/%s.save" % TEMPLATE_NAME, "Worlds/%s.save" % GUEST_NAME)
        self.ServerControl.AddWorld(GUEST_NAME)
        self.ServerControl.WorldMetaDataCache[GUEST_NAME.lower()][MetaDataKey.CreationDate] = int(time.time())
        self.LastCreation = int(time.time())
        Console.Out("GuestCreator", "New guest world created. Old one is %s" % OldGuestName)
        if VERBOSE:
            self.ServerControl.SendMessageToAll("&c[Notice]&e A new guest world has been created.")
                
        if HIDE_OLD_GUESTS:
            OldGuestMetaData = self.ServerControl.GetWorldMetaData(OldGuestName)
            if OldGuestMetaData is not None:
                OldGuestMetaData[MetaDataKey.IsHidden] = True
        
        if DELETE_OLD_GUESTS:
            GuestToDeleteId = NewID - NO_OF_GUESTS_BEFORE_DELETION
            if GuestToDeleteId > 0:
                GuestToDelete = GUEST_NAME + str(GuestToDeleteId)
                if self.ServerControl.WorldExists(GuestToDelete):
                    self.ServerControl.DeleteWorld(GuestToDelete)
                    Console.Out("GuestCreator", "Deleted world %s" % GuestToDelete)
                    

        
        
            
     


