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

from core.pluginmanager import PluginBase, Hooks, PluginManager
from core.commandhandler import CommandObject
from core.packet import PacketWriter
from core.constants import *

class FlyPlugin(PluginBase):
    FLY_KEY = "FlyPlugin"
    def OnLoad(self):
        self.PluginMgr.RegisterHook(self, self.OnPlayerPositionUpdate, Hooks.ON_PLAYER_POSITION_UPDATE)
        self.AddCommand("fly", FlyCommand, 'guest', 'Enables flying mode', '', 0)
        
    def OnPlayerPositionUpdate(self, pPlayer, x, y, z, o, p):
        pFlyData = pPlayer.GetPluginData(FlyPlugin.FLY_KEY)
        if pFlyData is not None:
            NewGlassBlocks = set()
            pWorld = pPlayer.GetWorld()
            for px in xrange(x -3, x + 4):
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