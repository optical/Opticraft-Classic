from core.pluginmanager import PluginBase, Hooks
from core.commandhandler import CommandObject
from core.constants import *
from core.console import *
from core.jsondict import JsonSerializeableObject

class ZonePlugin(PluginBase):
    ZoneKey = "Zones"
    ZoneCreationKey = "ZoneCreation"
    def OnLoad(self):
        self.PluginMgr.RegisterHook(self, self.OnAttemptPlaceBlockZoneCheck, Hooks.ON_ATTEMPT_PLACE_BLOCK)
        self.PluginMgr.RegisterHook(self, self.ZoneCreationCheck, Hooks.ON_ATTEMPT_PLACE_BLOCK)
        self.PluginMgr.RegisterHook(self, self.OnWorldLoad, Hooks.ON_WORLD_LOAD)
        self.PluginMgr.RegisterHook(self, self.OnPlayerChangeWorld, Hooks.ON_PLAYER_CHANGE_WORLD)

        #Zone commands
        self.AddCommand("zinfo", ZoneInfoCmd, 'guest', 'Returns information on a zone.', 'Incorrect syntax! Usage: /zinfo <zone>', 1)
        self.AddCommand("zlist", ZoneListCmd, 'guest', 'Lists all zones on the map', '', 0)

        self.AddCommand("ztest", ZoneTestCmd, 'guest', 'Checks to see if you are in a zone.', '', 0)
        self.AddCommand("zaddbuilder", AddZoneBuilderCmd, 'guest', 'Adds a builder to a zone', 'Incorrect syntax! Usage: /zaddbuilder <zone> <username>', 2)
        self.AddCommand("zdelbuilder", DelZoneBuilderCmd, 'guest', 'Deletes a builder from a zone', 'Incorrect syntax! Usage: /zdelbuilder <zone> <username>', 2)
        self.AddCommand("zsetrank", zSetMinRankCmd, 'guest', 'Changes the minimum non zone-builder rank required to build on this zone', 'Incorrect syntax! Usage: /zsetrank <zone> <rank>', 2)
        self.AddCommand("zsetowner", zChangeOwnerCmd, 'guest', 'Changes the owner of a zone', 'Incorrect syntax! Usage: /zsetowner <zone> <username>', 2)
        self.AddCommand("zRename", zRenameCmd, 'admin', 'Renames a restricted zone', 'Incorrect syntax. Usage: /zRename <name> <newname>', 2)
        self.AddCommand("zCreate", ZCreateCmd, 'admin', 'Creates a restricted zone', 'Incorrect syntax. Usage: /zCreate <name> <owner>', 2)
        self.AddCommand("zDelete", ZDeleteCmd, 'admin', 'Deletes a restricted zone', 'Incorrect syntax. Usage: /zDelete <name>', 1)

    def OnAttemptPlaceBlockZoneCheck(self, pWorld, pPlayer, BlockValue, x, y, z):
        Zones = self.GetWorldZones(pWorld)
        if Zones is None:
            return True
        
        for pZone in Zones:
            if pZone.Check(pPlayer, x, y, z) == False:
                pPlayer.SendMessage("&RYou cannot build in zone \"%s\"" % pZone.Name)
                return False
        return True
    
    def OnPlayerChangeWorld(self, pPlayer, OldWorld, NewWorld):
        ZoneData = pPlayer.GetPluginData(ZonePlugin.ZoneCreationKey)
        if ZoneData is not None:
            pPlayer.SendMessage("&SZone creation cancelled due to world change")
            pPlayer.SetPluginData(ZonePlugin.ZoneCreationKey, None)
    
    def OnWorldLoad(self, pWorld):
        '''Deserialize the Zones'''
        EncodedZones = self.GetWorldZones(pWorld)
        Zones = list()
        if EncodedZones is not None:
            for eZone in EncodedZones:
                pZone = Zone(pWorld)
                pZone.FromJson(eZone)
                Zones.append(pZone)
        pWorld.SetDataStoreEntry(ZonePlugin.ZoneKey, Zones)
                
    def GetWorldZones(self, pWorld):
        return None if not pWorld.HasDataStoreEntry(ZonePlugin.ZoneKey) else pWorld.GetDataStoreEntry(ZonePlugin.ZoneKey)

    def ZoneCreationCheck(self, pWorld, pPlayer, BlockValue, x, y, z):
        if BlockValue == BLOCK_AIR:
            return
        ZoneData = pPlayer.GetPluginData(ZonePlugin.ZoneCreationKey)
        if ZoneData is None:
            return True
        if ZoneData.FirstPlacement:
            ZoneData.X1 = x
            ZoneData.Y1 = y
            ZoneData.Z1 = z
            ZoneData.FirstPlacement = False
            pPlayer.SendMessage("&SNow place the second and final corner of the zone")
            return False
        else:
            ZoneData.X2 = x
            ZoneData.Y2 = y
            ZoneData.Z2 = z
            ZoneData.SortCoords()
            pZone = Zone(pPlayer.GetWorld(), ZoneData.Name, ZoneData.X1, ZoneData.Y1, ZoneData.Z1, ZoneData.X2, ZoneData.Y2, ZoneData.Z2, 'builder', ZoneData.Owner)
            
            Zones = self.GetWorldZones(pWorld)
            if Zones is None:
                Zones = list()
                pWorld.SetDataStoreEntry(ZonePlugin.ZoneKey, Zones)
            Zones.append(pZone)
            pPlayer.SetPluginData(ZonePlugin.ZoneCreationKey, None)
            pPlayer.SendMessage("&SSuccessfully created zone \"&V%s&S\"" % ZoneData.Name)
            return False
                
        
class Zone(JsonSerializeableObject):
    def __init__(self, pWorld, Name = '', X1 = 0, Y1 = 0, Z1 = 0, X2 = 0, Y2 = 0, Z2 = 0, MinimumRank = '', Owner = ''):
        self.pWorld = pWorld
        self.Name = Name
        self.X1 = X1
        self.X2 = X2
        self.Y1 = Y1
        self.Y2 = Y2
        self.Z1 = Z1
        self.Z2 = Z2
        self.Builders = set()
        self.Excluded = set()
        self.Owner = Owner
        self.MinimumRank = MinimumRank
        
    def OnJsonLoad(self):
        '''Called when we are deserialized'''
        if self.pWorld.ServerControl.IsValidRank(self.MinimumRank) == False:
            Console.Warning("Zones", "Zone %s had invalid rank %s. Rank changed to builder" % (self.Name, self.MinimumRank))
            self.MinimumRank = 'builder'
        self.Builders = set(self.Builders)
        self.Excluded = set(self.Excluded)
    
    def Check(self, pPlayer, X, Y, Z):
        if self.IsInZone(X, Y, Z):
            return self.CanBuild(pPlayer)
        return True
    
    def IsInZone(self, X, Y, Z):
        return X >= self.X1 and X <= self.X2 and Y >= self.Y1 and Y <= self.Y2 and Z >= self.Z1 and Z <= self.Z2
        
    def CanBuild(self, pPlayer):
        if pPlayer.HasPermission(self.MinimumRank) == False:
            if pPlayer.GetName().lower() not in self.Builders:
                if self.Owner.lower() != pPlayer.GetName().lower():
                    return False
        return True

class ZoneCreationData(object):
    def __init__(self, ZoneName, Owner):
        self.Name = ZoneName
        self.X1, self.X2, self.Y1, self.Y2, self.Z1, self.Z2 = -1, -1, -1, -1, -1, -1
        self.FirstPlacement = True
        self.Owner = Owner
    
    def SortCoords(self):
        self.X1, self.Y1, self.Z1, self.X2, self.Y2, self.Z2 = self.ArrangeCoordinates(self.X1, self.Y1, self.Z1, self.X2, self.Y2, self.Z2)    
        
    def ArrangeCoordinates(self, X1, Y1, Z1, X2, Y2, Z2):
        return min(X1, X2), min(Y1, Y2), min(Z1, Z2), max(X1, X2), max(Y1, Y2), max(Z1, Z2)   
         
##########################
#        Commands        #
##########################
class ZoneCommand(CommandObject):
    def GetZone(self, pWorld, Name):
        Name = Name.lower()
        if pWorld.HasDataStoreEntry(ZonePlugin.ZoneKey):
            Zones = pWorld.GetDataStoreEntry(ZonePlugin.ZoneKey)
            for pZone in Zones:
                if pZone.Name.lower() == Name:
                    return pZone
        return None
    
    def GetZones(self, pWorld):
        return None if not pWorld.HasDataStoreEntry(ZonePlugin.ZoneKey) else pWorld.GetDataStoreEntry(ZonePlugin.ZoneKey)

class ZoneInfoCmd(ZoneCommand):
    '''Zone info command handler. Returns information on a zone'''
    def Run(self, pPlayer, Args, Message):
        Name = Args[0]
        pZone = self.GetZone(pPlayer.GetWorld(), Name)
        if pZone is None:
            pPlayer.SendMessage("&RNo such zone exists on this map")
            return
        pPlayer.SendMessage("&SName: &V%s" % pZone.Name)
        pPlayer.SendMessage("&SOwner: &V%s" % pZone.Owner)
        pPlayer.SendMessage("&SMinimum rank: &V%s" % pZone.MinimumRank.capitalize())
        pPlayer.SendMessage("&S---Builders---")
        Num = 0
        for Builder in pZone.Builders:
            pPlayer.SendMessage('&V%s' % Builder)
            Num += 1
        if Num == 0:
            pPlayer.SendMessage("This zone has no builders")
            
class ZoneListCmd(ZoneCommand):
    '''Zone list command handler. Lists all zones on a map'''
    def Run(self, pPlayer, Args, Message):
        Zones = self.GetZones(pPlayer.GetWorld())
        ZoneNames = str("&S")
        for pZone in Zones:
            ZoneNames += pZone.Name + ' '
        if len(Zones) > 0:
            pPlayer.SendMessage("&SThe following zones are active on this map:")
            pPlayer.SendMessage(ZoneNames)
        else:
            pPlayer.SendMessage("&SThis map has no zones!")
            
class ZoneTestCmd(ZoneCommand):
    '''Command handler for the /ztest command. Checks to see if you are in a zone'''
    def Run(self, pPlayer, Args, Message):
        x, y, z = pPlayer.GetX(), pPlayer.GetY(), pPlayer.GetZ()
        x /= 32
        y /= 32
        z -= 50
        z /= 32
        x = int(x)
        y = int(y)
        z = int(z)
        Zones = self.GetZones(pPlayer.GetWorld())
        for pZone in Zones:
            if pZone.IsInZone(x, y, z):
                pPlayer.SendMessage("&SIt appears you are in zone \"&V%s&S\"" % pZone.Name)
                return
        pPlayer.SendMessage("&SIt does not seem like you are in any zone.")

class AddZoneBuilderCmd(ZoneCommand):
    '''Add zone builder handler. This adds a builder to a zone'''
    def Run(self, pPlayer, Args, Message):
        ZoneName = Args[0]
        Username = Args[1]
        pZone = self.GetZone(pPlayer.GetWorld(), ZoneName)
        if pZone is None:
            pPlayer.SendMessage("&RNo such zone exists on this map")
            return
        if pPlayer.GetName().lower() != pZone.Owner.lower():
            if pPlayer.HasPermission('admin') == False:
                pPlayer.SendMessage("&RYou are not allowed to delete builders from this zone!")
                return
        Username = Username.lower()
        if Username in pZone.Builders:
            pPlayer.SendMessage("&RThat user is already a builder for this zone!")
            return
        pZone.Builders.add(Username)
        pPlayer.SendMessage("&SSuccessfully added &V%s &Sas a builder for zone \"&V%s&S\"" % (Username, pZone.Name))
        if pPlayer.ServerControl.GetPlayerFromName(Username) is not None:
            pPlayer.ServerControl.GetPlayerFromName(Username).SendMessage("&SYou have been added as a builder to zone &V%s" % pZone.Name)

class DelZoneBuilderCmd(ZoneCommand):
    '''Del zone builder handler. This deletes a builder from a zone'''
    def Run(self, pPlayer, Args, Message):
        ZoneName = Args[0]
        Username = Args[1]
        pZone = self.GetZone(pPlayer.GetWorld(), ZoneName)
        if pZone is None:
            pPlayer.SendMessage("&RNo such zone exists on this map")
            return
        if pPlayer.GetName().lower() != pZone.Owner.lower():
            if pPlayer.HasPermission('admin') == False:
                pPlayer.SendMessage("&RYou are not allowed to delete builders from this zone!")
                return
        Username = Username.lower()
        if Username not in pZone.Builders:
            pPlayer.SendMessage("&RThat user is not a builder for this zone!")
            return
        pZone.Builders.remove(Username)
        pPlayer.SendMessage("&SSuccessfully removed %s as a builder for zone &V\"%s&S\"" % (Username, pZone.Name))
        if pPlayer.ServerControl.GetPlayerFromName(Username) is not None:
            pPlayer.ServerControl.GetPlayerFromName(Username).SendMessage("&SYou have been removed as a builder from zone &V\"%s&S\"" % pZone.Name)

class zSetMinRankCmd(ZoneCommand):
    '''Handler for the zSetMinRank command. Changes the minimum rank to build in a zone'''
    def Run(self, pPlayer, Args, Message):
        ZoneName = Args[0]
        Rank = Args[1]
        if pPlayer.ServerControl.IsValidRank(Rank) != True:
            pPlayer.SendMessage("&RInvalid rank! Valid ranks are: %s" % pPlayer.ServerControl.GetExampleRanks())
            return
        pZone = self.GetZone(pPlayer.GetWorld(), ZoneName)
        if pZone is None:
            pPlayer.SendMessage("&RNo such zone exists on this map")
            return
        if pPlayer.GetName().lower() != pZone.Owner.lower():
            if pPlayer.HasPermission('owner') == False:
                pPlayer.SendMessage("&RYou are not allowed to change the minimum rank required in this zone!")
                return
        pZone.MinimumRank = Rank.lower()
        pPlayer.SendMessage("&SMinimum non-builder ranked required to build in zone \"&V%s&S\" is now &V%s" % (pZone.Name, Rank.capitalize()))

class zChangeOwnerCmd(ZoneCommand):
    '''zChangeOwner command handler. This changes the owner of a zone'''
    def Run(self, pPlayer, Args, Message):
        ZoneName = Args[0]
        Username = Args[1]
        pZone = self.GetZone(pPlayer.GetWorld(), ZoneName)
        if pZone is None:
            pPlayer.SendMessage("&RNo such zone exists on this map")
            return
        if pPlayer.GetName().lower() != pZone.Owner.lower():
            if pPlayer.HasPermission('admin') == False:
                pPlayer.SendMessage("&RYou are not allowed to change this zones owner!")
                return
        Username = Username.lower()
        pZone.Owner = Username
        pPlayer.SendMessage("&SSuccessfully changed the owner of zone &V\"%s&S\" to &V%s" % (pZone.Name, Username))
        if pPlayer.ServerControl.GetPlayerFromName(Username) is not None:
            pPlayer.ServerControl.GetPlayerFromName(Username).SendMessage("&SYou have been set as the owner of zone &V\"%s&S\"" % pZone.Name)

class zRenameCmd(ZoneCommand):
    def Run(self, pPlayer, Args, Message):  
        Name = Args[0]
        NewName = Args[1]
        if NewName.isalnum() == False:
            pPlayer.SendMessage("&RInvalid name!")
            return
        if self.GetZone(pPlayer.GetWorld(), NewName) is not None:
            pPlayer.SendMessage("&RA Zone with that name already exists!")
            return
        pZone = self.GetZone(pPlayer.GetWorld(), Name)
        if pZone is None:
            pPlayer.SendMessage("&RThat zone does not exist!")
            return
        pZone.Name = NewName
        pPlayer.SendMessage("&SZone \"&V%s&S\" renamed to \"&V%s&S\"" % (Name, NewName))
        
class ZCreateCmd(ZoneCommand):
    def Run(self, pPlayer, Args, Message):
        Name = Args[0]
        if Name.isalnum() == False:
            pPlayer.SendMessage("&RInvalid name!")
            return
        Owner = Args[1].lower()
        if self.GetZone(pPlayer.GetWorld(), Name) is not None:
            pPlayer.SendMessage("&RA Zone with that name already exists!")
            return
        pPlayer.SendMessage("&SPlace two blocks to define the cuboid that will be the zone.")
        pPlayer.SendMessage("&SYou can place a block using /place")
        pPlayer.SetPluginData(ZonePlugin.ZoneCreationKey, ZoneCreationData(Name, Owner))

class ZDeleteCmd(ZoneCommand):
    '''Delete zone handler. This deletes a zone from a map'''
    def Run(self, pPlayer, Args, Message):
        ZoneName = Args[0]
        pZone = self.GetZone(pPlayer.GetWorld(), ZoneName)
        if pZone is None:
            pPlayer.SendMessage("&RNo such zone exists on this map")
            return
        Zones = pPlayer.GetWorld().GetDataStoreEntry(ZonePlugin.ZoneKey)
        Zones.remove(pZone)
        pPlayer.SendMessage("&SSuccessfully deleted zone &V\"%s&S\"" % pZone.Name)
        
