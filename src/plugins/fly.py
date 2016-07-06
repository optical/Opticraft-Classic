from core.pluginmanager import PluginBase, Hooks, PluginManager
from core.commandhandler import CommandObject
from core.packet import PacketWriter
from core.constants import *

class FlyPlugin(PluginBase):
    FLY_KEY = "FlyPlugin"
    def OnLoad(self):
        self.PluginMgr.RegisterHook(self, self.OnPlayerPositionUpdate, Hooks.ON_PLAYER_POSITION_UPDATE)
        self.PluginMgr.RegisterHook(self, self.OnPlayerWorldChange, Hooks.ON_PLAYER_CHANGE_WORLD)
        self.AddCommand("fly", FlyCommand, 'guest', 'Enables flying mode', '', 0)
        
    def OnPlayerPositionUpdate(self, pPlayer, x, y, z, o, p):
        pFlyData = pPlayer.GetPluginData(FlyPlugin.FLY_KEY)
        if pFlyData is not None:
            pWorld = pPlayer.GetWorld()
            if pWorld is None:
                return
            NewGlassBlocks = set()
            for px in xrange(x - 3, x + 4):
                for py in xrange(y - 3, y + 4):
                    for pz in xrange(z - 3, z - 1):
                        if pWorld.WithinBounds(px, py, pz) and pWorld.GetBlock(px, py, pz) == BLOCK_AIR:
                            Packet = PacketWriter.MakeBlockSetPacket(px, pz, py, BLOCK_GLASS)
                            pPlayer.SendPacket(Packet)
                            Offset = pWorld._CalculateOffset(px, py, pz)
                            NewGlassBlocks.add(Offset)
                            if Offset in pFlyData.GlassBlocks:
                                pFlyData.GlassBlocks.remove(Offset)
            pFlyData.RemoveOldBlocks()
            pFlyData.GlassBlocks = NewGlassBlocks
        
    def OnPlayerWorldChange(self, pPlayer, OldWorld, NewWorld):
        pFlyData = pPlayer.GetPluginData(FlyPlugin.FLY_KEY)
        if pFlyData is not None:
            pFlyData.GlassBlocks = set()
            
class FlyData(object):
    def __init__(self, pPlayer):
        self.pPlayer = pPlayer
        self.GlassBlocks = set() #List of blocks which the client was last told were glass
    
    def RemoveOldBlocks(self):
        for Offset in self.GlassBlocks:
            x, y, z = self.pPlayer.GetWorld()._CalculateCoords(Offset)
            self.pPlayer.GetWorld().SendBlock(self.pPlayer, x, y, z)
        
class FlyCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):
        if pPlayer.GetPluginData(FlyPlugin.FLY_KEY) is None:
            pPlayer.SendMessage("&SFly mode enabled")
            pPlayer.SetPluginData(FlyPlugin.FLY_KEY, FlyData(pPlayer))
        else:
            pPlayer.GetPluginData(FlyPlugin.FLY_KEY).RemoveOldBlocks()
            pPlayer.SetPluginData(FlyPlugin.FLY_KEY, None)
            pPlayer.SendMessage("&SFly mode disabled")
