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
from core.pluginmanager import PluginBase, Hooks, PluginManager
from core.commandhandler import CommandObject
from core.jsondict import JsonSerializeableObject
from core.packet import PacketWriter

class PortalPlugin(PluginBase):
    PortalKey = "PortalManager"
    PortalCreationKey = "PortalCreation"
    PortalDisplayKey = "PortalDisplayKey"
    def OnLoad(self):
        '''Register Hooks and commands'''
        self.PluginMgr.RegisterHook(self, self.OnPlayerPositionUpdate, Hooks.ON_PLAYER_POSITION_UPDATE)
        self.PluginMgr.RegisterHook(self, self.OnWorldLoad, Hooks.ON_WORLD_LOAD)
        self.PluginMgr.RegisterHook(self, self.OnAttemptPlaceBlock, Hooks.ON_ATTEMPT_PLACE_BLOCK)
        self.PluginMgr.RegisterHook(self, self.OnPlayerChangeWorld, Hooks.ON_PLAYER_CHANGE_WORLD)
        self.PluginMgr.RegisterHook(self, self.OnPlayerLogout, Hooks.ON_PLAYER_DISCONNECT)
        
        #Commands
        self.AddCommand("portal", PortalCmd, 'admin', 'Displays help on portal commands', '', 0)
        self.AddCommand("portals", PortalListCmd, 'admin', 'Lists and displays all portals on a world.', '', 0)
        self.AddCommand("portalcreate", PortalCreateCmd, 'admin', 'Creates a new portal on a world.', 'Incorrect syntax! Usage: /portalcreate <name>', 1)
        self.AddCommand("portaldelete", PortalDeleteCmd, 'admin', 'Deletes a portal on a world.', 'Incorrect syntax! Usage: /portaldelete <name>', 1)
        
    def OnWorldLoad(self, pWorld):
        '''Deserialize portal information'''
        if pWorld.HasDataStoreEntry(PortalPlugin.PortalKey):
            SerializedManager = pWorld.GetDataStoreEntry(PortalPlugin.PortalKey)
            Manager = PortalManager(pWorld)
            Manager.FromJson(SerializedManager)
            pWorld.SetDataStoreEntry(PortalPlugin.PortalKey, Manager)
    
    def OnPlayerLogout(self, pPlayer):
        '''Allows the world to be unloaded as creation process is over'''
        CreationData = pPlayer.GetPluginData(PortalPlugin.PortalCreationKey)
        if CreationData is not None:
            if CreationData.pWorld.IsMainWorld == False:
                CreationData.pWorld.CanUnload = True
    
    def OnPlayerPositionUpdate(self, pPlayer, x, y, z, o, p):
        '''Lets the worlds PortalManager (if any) that a player has moved'''
        if pPlayer.GetWorld().HasDataStoreEntry(PortalPlugin.PortalKey):
            Manager = pPlayer.GetWorld().GetDataStoreEntry(PortalPlugin.PortalKey)
            Manager.OnPlayerMove(pPlayer, x, y, z)
            
    def OnAttemptPlaceBlock(self, pWorld, pPlayer, BlockValue, x, y, z):
        '''Handles portal entrance/exit placement'''
        CreationData = pPlayer.GetPluginData(PortalPlugin.PortalCreationKey)
        if CreationData is not None:
            if BlockValue != BLOCK_RED_CLOTH:
                if CreationData.AllowedPlaceEntry == False:
                    pPlayer.SendMessage("&SEntry points cannot span multiple worlds.")
                    return False
                pPlayer.SendMessage("&SEntry point placed. Place a &cRed block for the exit")
                CreationData.Points.add(Point(x, y, z))
                return True
                
            else:
                if len(CreationData.Points) == 0:
                    pPlayer.SendMessage("&RYou must place an entry point first!")
                    return
                pPortal = Portal(CreationData.Name, x, y, z + 1, pWorld.Name)
                pPortal.Points = CreationData.Points
                
                Manager = None
                PortalWorld = CreationData.pWorld
                if PortalWorld.HasDataStoreEntry(PortalPlugin.PortalKey) == False:
                    Manager = PortalManager(PortalWorld)
                    PortalWorld.SetDataStoreEntry(PortalPlugin.PortalKey, Manager)
                else:
                    Manager = PortalWorld.GetDataStoreEntry(PortalPlugin.PortalKey)
                
                Manager.AddPortal(pPortal)
                if PortalWorld.IsMainWorld == False:
                    PortalWorld.CanUnload = True
                pPlayer.SetPluginData(PortalPlugin.PortalCreationKey, None)
                pPlayer.SendMessage("&SSuccessfully created portal\"&V%s&S\"" % pPortal.Name)
                return False
                
    def OnPlayerChangeWorld(self, pPlayer, OldWorld, NewWorld):
        '''Disable entries on multiple worlds'''
        CreationData = pPlayer.GetPluginData(PortalPlugin.PortalCreationKey)
        if CreationData is not None:
            CreationData.AllowedPlaceEntry = False
            pPlayer.SendMessage("&SYou must now place an exit point for the portal. Use /portalexit")
            
        ListData = pPlayer.GetPluginData(PortalPlugin.PortalDisplayKey)
        if ListData is not None:
            pPlayer.SetPluginData(PortalPlugin.PortalDisplayKey, None)
    
class PortalManager(JsonSerializeableObject):
    '''Manages all portals, and portal blocks on a world'''
    def __init__(self, pWorld):
        self.pWorld = pWorld
        self.PortalBlocks = dict() #Key is X,Y,Z offset of a world. Value is a Portal object
        self.Portals = set() #Set of all Portal objects.
        
    def OnJsonLoad(self):
        '''Create the hashmap of Offset -> PortalBlock'''
        EncodedPortals = self.Portals
        self.Portals = set()
        for EncodedPortal in EncodedPortals:
            pPortal = Portal()
            pPortal.FromJson(EncodedPortal)
            self.AddPortal(pPortal)
            
        self.Portals = set(self.Portals)
        for pPortal in self.Portals:
            self.LoadPortalBlocks(pPortal)
                                  
    def AddPortal(self, pPortal):
        '''Loads a portal object and creates PortalBlock entries'''
        self.Portals.add(pPortal)
        self.LoadPortalBlocks(pPortal)
        
    def LoadPortalBlocks(self, pPortal):
        '''Adds portalsblocks to the hashmap'''
        for pPoint in pPortal.Points:
            self.PortalBlocks[self.pWorld._CalculateOffset(pPoint.X, pPoint.Y, pPoint.Z)] = PortalBlock(pPortal)
        
    def RemovePortal(self, pPortal):
        '''Removes a portal and its portalblocks'''
        self.Portals.remove(pPortal)
        for pPoint in pPortal.Points:
            Offset = self.pWorld._CalculateOffset(pPoint.X, pPoint.Y, pPoint.Z)
            del self.PortalBlocks[Offset]
    
    def OnPlayerMove(self, pPlayer, x, y, z):
        '''Teleports player if they are standing in a portal'''
        pPortal = self.PortalBlocks.get(pPlayer.GetWorld()._CalculateOffset(x, y, z), None)
        if pPortal is not None:
            pPortal.Trigger(pPlayer)
        
   
   
class Point(JsonSerializeableObject):
    '''Represents a 3 dimensional point'''
    def __init__(self, x = 0, y = 0, z = 0):
        self.X = x
        self.Y = y
        self.Z = z
        
class Portal(JsonSerializeableObject):
    '''Portal object. Stores information about the Portal. Does no work'''
    def __init__(self, Name = "", DestinationX = 0, DestinationY = 0, DestinationZ = 0, DestinationWorldName = ""):
        self.Points = set()
        self.Name = Name
        #Coordinates are stored in block value, not pixel
        self.DestinationX = DestinationX
        self.DestinationY = DestinationY
        self.DestinationZ = DestinationZ
        self.DestinationWorldName = DestinationWorldName
        
    def OnJsonLoad(self):
        EncodedPoints = self.Points
        self.Points = set()
        for EncodedPoint in EncodedPoints:
            pPoint = Point()
            pPoint.FromJson(EncodedPoint)
            self.Points.add(pPoint)
        
class PortalBlock(object):
    '''PortalBlock object. Responsible for teleporting players'''
    def __init__(self, Parent):
        self.Parent = Parent
    
    def Trigger(self, pPlayer):
        '''Teleport player to destination'''
        ServerControl = pPlayer.ServerControl
        if pPlayer.GetWorld().Name.lower() == self.Parent.DestinationWorldName.lower():
            pPlayer.Teleport(self.Parent.DestinationX * 32, self.Parent.DestinationY * 32, self.Parent.DestinationZ * 32,
                            pPlayer.GetOrientation(), pPlayer.GetPitch())
        else:
            if ServerControl.WorldExists(self.Parent.DestinationWorldName) == False:
                if pPlayer.HasPermission('admin'):
                    pPlayer.SendMessage("&RPortal %s has an invalid target world. Use /portaldelete" % self.Parent.Name)
           
            else:
                if pPlayer.HasPermission(ServerControl.GetWorldJoinRank(self.Parent.DestinationWorldName)):
                    pPlayer.SetSpawnPosition(self.Parent.DestinationX * 32, self.Parent.DestinationY * 32, self.Parent.DestinationZ * 32,
                                            pPlayer.GetOrientation(), pPlayer.GetPitch())
                    pPlayer.ChangeWorld(self.Parent.DestinationWorldName)
                else:
                    pPlayer.SendMessage("&RYou do not have the required rank to use this portal!")
        
class PortalCreationData(object):
    '''Object used to store information about a portal while it is being created'''
    def __init__(self, pPlayer, PortalName):
        self.pPlayer = pPlayer
        self.pWorld = pPlayer.GetWorld()
        self.pWorld.CanUnload = False
        self.Name = PortalName
        self.DestinationWorldName = ""
        self.Points = set()
        self.AllowedPlaceEntry = True



#################################
#       Portal commands         #
#################################

class PortalCmd(CommandObject):
    '''Lists all portal commands. Here to help new users figure out portals'''
    def Run(self, pPlayer, Args, Message):
        pPlayer.SendMessage("&STo create a portal, use &V/portalcreate")
        pPlayer.SendMessage("&STo delete a portal, use &V/portaldelete")
        pPlayer.SendMessage("&STo view all portals, use &V/portals")

class PortalCreateCmd(CommandObject):
    '''Starts the portal creation process.'''
    def Run(self, pPlayer, Args, Message):
        PortalName = Args[0]
        if pPlayer.GetWorld().HasDataStoreEntry(PortalPlugin.PortalKey):
            Manager = pPlayer.GetWorld().GetDataStoreEntry(PortalPlugin.PortalKey)
            for pPortal in Manager.Portals:
                if pPortal.Name.lower() == PortalName.lower():
                    pPlayer.SendMessage("&RA portal with that name already exists on this world.")
                    return
        
        pPlayer.SetPluginData(PortalPlugin.PortalCreationKey, PortalCreationData(pPlayer, PortalName))
        pPlayer.SendMessage("&SPlace blocks to define the entry point.")
        pPlayer.SendMessage("&SWater is the recommended block type. Use: /water")
        pPlayer.SendMessage("&SPlace a &cRed &Sblock to define the exit")
        
class PortalDeleteCmd(CommandObject):
    '''Erases a portal from a world.'''
    def Run(self, pPlayer, Args, Message):    
        PortalName = Args[0]
        if pPlayer.GetWorld().HasDataStoreEntry(PortalPlugin.PortalKey):
            Manager = pPlayer.GetWorld().GetDataStoreEntry(PortalPlugin.PortalKey)
            for pPortal in Manager.Portals:
                if pPortal.Name.lower() == PortalName.lower():
                    Manager.RemovePortal(pPortal)
                    pPlayer.SendMessage("&SSuccessfully deleted portal \"&V%s&S\"" % pPortal.Name)
                    return
                
        pPlayer.SendMessage("&RThat portal does not exist!")
    
class PortalListCmd(CommandObject):
    '''Lists all portals on the world, as well as displaying them.'''
    def Run(self, pPlayer, Args, Message):
        if pPlayer.GetWorld().HasDataStoreEntry(PortalPlugin.PortalKey):
            Manager = pPlayer.GetWorld().GetDataStoreEntry(PortalPlugin.PortalKey)
            
            #List all portals, as well as how their entrances and exits on the world
            if pPlayer.GetPluginData(PortalPlugin.PortalDisplayKey) is None:
                OutStr = '&S'
                for pPortal in Manager.Portals:
                    OutStr += pPortal.Name + ' '
                    for pPoint in pPortal.Points:
                        pPlayer.SendPacket(PacketWriter.MakeBlockSetPacket(pPoint.X, pPoint.Z, pPoint.Y, BLOCK_BLUE))
                    if pPortal.DestinationWorldName.lower() == pPlayer.GetWorld().Name.lower():
                        pPlayer.SendPacket(PacketWriter.MakeBlockSetPacket(pPortal.DestinationX, pPortal.DestinationZ, pPortal.DestinationY, BLOCK_ORANGE))
                
                if len(OutStr) != 2:
                    pPlayer.SendMessage("&SThe following portals are active on this world:")
                    pPlayer.SendMessage(OutStr)
                    pPlayer.SendMessage("&SEntrances are marked as blue blocks. Exits in orange")
                    pPlayer.SetPluginData(PortalPlugin.PortalDisplayKey, True)
                    return
            
                pPlayer.SendMessage("&SThis world has no portals")
        
            else:
                pPlayer.SendMessage("&SNow hiding portal entrances and exits")
                for pPortal in Manager.Portals:
                    for pPoint in pPortal.Points:
                        pPlayer.SendPacket(PacketWriter.MakeBlockSetPacket(pPoint.X, pPoint.Z, pPoint.Y,
                            pPlayer.GetWorld().GetBlock(pPoint.X, pPoint.Y, pPoint.Z)))
                    if pPortal.DestinationWorldName.lower() == pPlayer.GetWorld().Name.lower():    
                        pPlayer.SendPacket(PacketWriter.MakeBlockSetPacket(pPortal.DestinationX, pPortal.DestinationZ, pPortal.DestinationY,
                                                                           pPlayer.GetWorld().GetBlock(pPortal.DestinationX, pPortal.DestinationY, pPortal.DestinationZ)))
                pPlayer.SetPluginData(PortalPlugin.PortalDisplayKey, None)
        else:
            pPlayer.SendMessage("&SThis world has no portals")
        
