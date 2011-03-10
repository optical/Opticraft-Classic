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

from core.pluginmanager import PluginBase
from core.commandhandler import CommandObject
from core.constants import *
from core.console import *

DRAW_KEY = "draw_plugin"

class DrawAction(object):
    '''Abstract class which when inherited is in charge of actually doing all of the drawing'''
    def __init__(self, pPlayer):
        self.pPlayer = pPlayer
        self.DisallowMapChanges = True
    def OnAttemptPlaceBlock(self, pWorld, BlockValue, x, y, z):
        pass
    def DoDraw(self):
        pass

class DrawCommandPlugin(PluginBase):
    def OnLoad(self):
        self.PluginMgr.RegisterHook(self, self.OnAttemptPlaceBlock, "on_attemptplaceblock")
        self.PluginMgr.RegisterHook(self, self.OnWorldChange, "on_changeworld")
        self.RegisterCommands()
        
    def OnAttemptPlaceBlock(self, pWorld, pPlayer, BlockValue, x, y, z):
        pDrawAction = pPlayer.GetPluginData(DRAW_KEY)
        if pDrawAction != None:
            return pDrawAction.OnAttemptPlaceBlock(pWorld, BlockValue, x, y, z)
            
    def OnWorldChange(self, pPlayer, OldWorld, NewWorld):
        pDrawAction = pPlayer.GetPluginData(DRAW_KEY)
        if pDrawAction != None and pDrawAction.DisallowMapChanges:
            pPlayer.SetPluginData(DRAW_KEY, None)
    
    def RegisterCommands(self):
        self.AddCommand("cuboid", CuboidCommand, 'operator', 'Used to create large cuboids of blocks', 'Incorrect syntax! Usage: /cuboid <material>', 1)

class CuboidCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):
        Material = ' '.join(Args)
        if GetBlockIDFromName(Material) != None:
            pPlayer.SetPluginData(DRAW_KEY, CuboidDrawAction(pPlayer, Material))
            pPlayer.SendMessage("&SPlace blocks to represent the two corners of the cuboid")
        else:
            pPlayer.SendMessage("&S\"&V%s&S\" is not a valid block!" % Material)
            
class CuboidDrawAction(DrawAction):
    def __init__(self, pPlayer, Material):
        DrawAction.__init__(self, pPlayer)
        self.Material = GetBlockIDFromName(Material)
        self.X1, self.Y1, self.Z1 = -1, -1, -1
        self.X2, self.Y2, self.Z2 = -1, -1, -1
        self.TempX, self.TempY, self.TempZ = -1, -1, -1
        
    def OnAttemptPlaceBlock(self, pWorld, BlockValue, x, y, z):
        if BlockValue == BLOCK_AIR:
            return
        if self.TempX == -1:
            self.TempX = x
            self.TempY = y
            self.TempZ = z
            self.pPlayer.SendMessage("&SNow place the second block for the cuboid to complete drawing.")
            return False
        else:
            self.X1 = min(self.TempX, x)
            self.Y1 = min(self.TempY, y)
            self.Z1 = min(self.TempZ, z)
            self.X2 = max(self.TempX, x)
            self.Y2 = max(self.TempY, y)
            self.Z2 = max(self.TempZ, z)
            self.DoDraw()
            return False
            
    def DoDraw(self):
        self.pPlayer.SendMessage("&SDrawing cuboid!")
        for x in xrange(self.X1, self.X2 + 1):
            for y in xrange(self.Y1, self.Y2 + 1):
                for z in xrange(self.Z1, self.Z2 + 1):
                    self.pPlayer.GetWorld().SetBlock(self.pPlayer, x, y, z, self.Material, ResendToClient = True)
                    #self.pPlayer.Teleport(x * 32, y * 32, z * 32, 0, 0)
        self.pPlayer.SendMessage("&SFinished drawing cuboid")
        self.pPlayer.SetPluginData(DRAW_KEY, None)
