from core.constants import *
from core.pluginmanager import PluginBase, Hooks, PluginManager
from core.commandhandler import CommandObject
from core.jsondict import JsonSerializeableObject
from core.packet import PacketWriter

class PortalPlugin(PluginBase):
    PortalKey = "PortalManager"
    PortalCreationKey = "PortalCreation"
    PortalDisplayKey = "PortalDisplayKey"
    PortalModificationKey = "PortalModificationKey"
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
        self.AddCommand("portalmodify", PortalModifyCmd, 'admin', 'Allows you to change entry and exit points of a portal', 'Incorrect syntax! Usage: /portalmodify <name>', 1)
        
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
            return self.HandleCreationBlockChange(CreationData, pWorld, pPlayer, BlockValue, x, y, z)
        
        ModifyData = pPlayer.GetPluginData(PortalPlugin.PortalModificationKey)
        if ModifyData is not None:
            return self.HandleModificationBlockChange(ModifyData, pWorld, pPlayer, BlockValue, x, y, z)
            
        
    def HandleCreationBlockChange(self, CreationData, pWorld, pPlayer, BlockValue, x, y, z):
        '''Called when a player places or deletes a block and is creation a portal'''
        if BlockValue == BLOCK_AIR:
            return
        
        if BlockValue != BLOCK_RED_CLOTH:
            if CreationData.AllowedPlaceEntry == False:
                pPlayer.SendMessage("&SEntry points cannot span multiple worlds.")
                return False
            pPlayer.SendMessage("&SEntry point placed. Place a &cRed &Sblock for the exit")
            CreationData.Points.add(Point(x, y, z))
            pPlayer.SendPacket(PacketWriter.MakeBlockSetPacket(x, z, y, BLOCK_BLUE))
            return PluginManager.FailSilently
            
        else:
            if len(CreationData.Points) == 0:
                pPlayer.SendMessage("&RYou must place an entry point first!")
                return
            pPortal = Portal(CreationData.Name, x, y, z, pWorld.Name)
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
            
            for pPoint in pPortal.Points:
                PortalWorld.SetBlock(None, pPoint.X, pPoint.Y, pPoint.Z, BLOCK_STILLWATER)
            
            pPlayer.SetPluginData(PortalPlugin.PortalCreationKey, None)
            pPlayer.SendMessage("&SSuccessfully created portal\"&V%s&S\"" % pPortal.Name)
            return False
                
    def HandleModificationBlockChange(self, ModifyData, pWorld, pPlayer, BlockValue, x, y, z):
        '''Called when a player places or deletes a block and has the portal modification command active'''
        if pWorld.Name.lower() != ModifyData.WorldName.lower():
            if BlockValue != BLOCK_RED_CLOTH:
                pPlayer.SendMessage("&RCannot erase or place entry points on another world")
                return False
        
        
        if BlockValue == BLOCK_AIR:
            for pPoint in ModifyData.pPortal.Points:
                if pPoint.X == x and pPoint.Y == y and pPoint.Z == z:
                    ModifyData.pPortalManager.RemovePortal(ModifyData.pPortal)
                    ModifyData.pPortal.Points.remove(pPoint)
                    ModifyData.pPortalManager.AddPortal(ModifyData.pPortal)
                    pPlayer.SendMessage("&SDeleted entry point.")
                    return
                
        elif BlockValue == BLOCK_RED_CLOTH:
            pPlayer.SendMessage("&SChanged portal exit")
            ModifyData.pPortal.Hide(pPlayer)
            ModifyData.pPortal.DestinationX = x
            ModifyData.pPortal.DestinationY = y
            ModifyData.pPortal.DestinationZ = z
            ModifyData.pPortal.DestinationWorldName = pWorld.Name
            ModifyData.pPortal.Display(pPlayer)
            return PluginManager.FailSilently
        
        else:
            ModifyData.pPortalManager.RemovePortal(ModifyData.pPortal)
            ModifyData.pPortal.Points.add(Point(x, y, z))
            ModifyData.pPortalManager.AddPortal(ModifyData.pPortal)
            pPlayer.SendMessage("&SSuccessfully added entry point")
            pWorld.SetBlock(None, x, y, z, BLOCK_WATER)
            ModifyData.pPortal.Display(pPlayer)
            return PluginManager.FailSilently

            
                                               
    def OnPlayerChangeWorld(self, pPlayer, OldWorld, NewWorld):
        '''Disable entries on multiple worlds'''
        CreationData = pPlayer.GetPluginData(PortalPlugin.PortalCreationKey)
        if CreationData is not None:
            CreationData.AllowedPlaceEntry = False
            pPlayer.SendMessage("&SYou must now place an exit point for the portal. Use /portalexit")
            
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
        
    def __eq__(self, other):
        return isinstance(other, Point) and other.X == self.X and other.Y == self.Y and other.Z == self.Z
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return self.X | self.Y | self.Z
        
class Portal(JsonSerializeableObject):
    '''Portal object. Stores information about the Portal.'''
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
            
    def Display(self, pPlayer):
        '''Display the portals entrances and exits'''
        for pPoint in self.Points:
            pPlayer.SendPacket(PacketWriter.MakeBlockSetPacket(pPoint.X, pPoint.Z, pPoint.Y, BLOCK_BLUE))
        if self.DestinationWorldName.lower() == pPlayer.GetWorld().Name.lower():
            pPlayer.SendPacket(PacketWriter.MakeBlockSetPacket(self.DestinationX, self.DestinationZ, self.DestinationY, BLOCK_ORANGE))
        
    def Hide(self, pPlayer):
        '''Hide the portal from a player'''
        for pPoint in self.Points:
            try:   
                BlockVal = pPlayer.GetWorld().GetBlock(pPoint.X, pPoint.Y, pPoint.Z)
                pPlayer.SendPacket(PacketWriter.MakeBlockSetPacket(pPoint.X, pPoint.Z, pPoint.Y, BlockVal))
            except IndexError:
                break
        if self.DestinationWorldName.lower() == pPlayer.GetWorld().Name.lower():    
            pPlayer.SendPacket(PacketWriter.MakeBlockSetPacket(self.DestinationX, self.DestinationZ, self.DestinationY,
                                pPlayer.GetWorld().GetBlock(self.DestinationX, self.DestinationY, self.DestinationZ)))        

class PortalBlock(object):
    '''PortalBlock object. Responsible for teleporting players'''
    def __init__(self, Parent):
        self.Parent = Parent
    
    def Trigger(self, pPlayer):
        '''Teleport player to destination'''
        ServerControl = pPlayer.ServerControl
        if pPlayer.GetWorld().Name.lower() == self.Parent.DestinationWorldName.lower():
            pPlayer.Teleport(self.Parent.DestinationX * 32, self.Parent.DestinationY * 32, (self.Parent.DestinationZ + 1) * 32,
                            pPlayer.GetOrientation(), pPlayer.GetPitch())
        else:
            if ServerControl.WorldExists(self.Parent.DestinationWorldName) == False:
                if pPlayer.HasPermission('admin'):
                    pPlayer.SendMessage("&RPortal %s has an invalid target world. Use /portalmodify" % self.Parent.Name)
           
            else:
                if pPlayer.HasPermission(ServerControl.GetWorldJoinRank(self.Parent.DestinationWorldName)):
                    pPlayer.SetSpawnPosition(self.Parent.DestinationX * 32, self.Parent.DestinationY * 32, (self.Parent.DestinationZ + 1) * 32,
                                            pPlayer.GetOrientation(), pPlayer.GetPitch())
                    pWorld = ServerControl.GetActiveWorld(self.Parent.DestinationWorldName)
                    if pWorld is not None:
                        if pWorld.IsFull():
                            if pPlayer.HasPermission('admin'):
                                pPlayer.SendMessage("&RCould not teleport you to world %s, it is full" % self.Parent.DestinationWorldName)
                            return
                        
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

class PortalModificationData(object):
    '''Object used to store information about the modification of a portal'''
    def __init__(self, pPlayer, pPortal):
        self.pPortal = pPortal
        self.pPlayer = pPlayer
        self.WorldName = pPlayer.GetWorld().Name
        self.pPortalManager = pPlayer.GetWorld().GetDataStoreEntry(PortalPlugin.PortalKey)

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
    
class PortalModifyCmd(CommandObject):
    '''Allows you to place new entry points and change the exit of a portal'''
    def Run(self, pPlayer, Args, Message):   
        PortalName = Args[0]
        ModifyData = pPlayer.GetPluginData(PortalPlugin.PortalModificationKey)
        if ModifyData is None:
            if pPlayer.GetWorld().HasDataStoreEntry(PortalPlugin.PortalKey):
                Manager = pPlayer.GetWorld().GetDataStoreEntry(PortalPlugin.PortalKey)
                for pPortal in Manager.Portals:
                    if pPortal.Name.lower() == PortalName.lower():
                        pPortal.Display(pPlayer)
                        pPlayer.SendMessage("&SYou may now place additional entry points for the portal.")
                        pPlayer.SendMessage("&SCurrent portal entrances are blue, the exit is orange")
                        pPlayer.SendMessage("&SThe exit may be changed by placing a &cred &Sblock")
                        pPlayer.SendMessage("&SEntry points can be removed by deleting the blocks")
                        pPlayer.SendMessage("&STo disable modification, use /portalmodify again")
                        pPlayer.SetPluginData(PortalPlugin.PortalModificationKey, PortalModificationData(pPlayer, pPortal))
                        return
                        
            pPlayer.SendMessage("&RThat portal does not exist!")
        else:
            pPlayer.SetPluginData(PortalPlugin.PortalModificationKey, None)
            pPlayer.SendMessage("&SYou are no longer modifying portal &V%s" % ModifyData.pPortal.Name)
            ModifyData.pPortal.Hide(pPlayer)

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
                    pPortal.Display(pPlayer)

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
                    pPortal.Hide(pPlayer)
                    
                pPlayer.SetPluginData(PortalPlugin.PortalDisplayKey, None)
        else:
            pPlayer.SendMessage("&SThis world has no portals")
        
