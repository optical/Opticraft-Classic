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

from core.pluginmanager import PluginBase, Hooks
from core.commandhandler import CommandObject
import time
import array
import math
from core.constants import *
from core.console import *

DRAW_KEY = "draw_plugin"
COPY_KEY = "draw_plugin_copy_data"
LOCK_LEVEL = 35000 #35,000 block changes results in the map being resent to prevent lag

class DrawCommandPlugin(PluginBase):
    def OnLoad(self):
        self.PluginMgr.RegisterHook(self, self.OnAttemptPlaceBlock, Hooks.ON_ATTEMPT_PLACE_BLOCK)
        self.PluginMgr.RegisterHook(self, self.OnWorldChange, Hooks.ON_CHANGE_WORLD)
        self.RegisterCommands()
        
    def OnAttemptPlaceBlock(self, pWorld, pPlayer, BlockValue, x, y, z):
        pDrawAction = pPlayer.GetPluginData(DRAW_KEY)
        if pDrawAction is not None:
            return pDrawAction.OnAttemptPlaceBlock(pWorld, BlockValue, x, y, z)
            
    def OnWorldChange(self, pPlayer, OldWorld, NewWorld):
        pDrawAction = pPlayer.GetPluginData(DRAW_KEY)
        if pDrawAction is not None and pDrawAction.DisallowMapChanges:
            pPlayer.SetPluginData(DRAW_KEY, None)
    
    def RegisterCommands(self):
        self.AddCommand("place", PlaceCommand, 'builder', 'Use instead of placing a block during a draw command', '', 0)
        self.AddCommand("cancel", CancelCommand, 'builder', 'Cancels your current draw command', '', 0)
        self.AddCommand("measure", MeasureCommand, 'guest', 'Measures the distance between two points', '', 0)
        self.AddCommand("cuboid", CuboidCommand, 'builder', 'Used to create large cuboids of blocks', 'Incorrect syntax! Usage: /cuboid <material>', 1)
        self.AddCommand("cuboidh", CuboidHCommand, 'builder', 'Used to create large hollow cuboids of blocks', 'Incorrect syntax! Usage: /cuboidh <material>', 1)
        self.AddCommand("cuboidw", CuboidWCommand, 'builder', 'Used to create large wireframes cuboids', 'Incorrect syntax! Usage: /cuboidw <material>', 1)
        self.AddCommand("cuboidr", CuboidRCommand, 'builder', 'Replaces all the "Material1" with "Material2 in a given cuboid', 'Incorrect syntax! Usage: /cuboidr <replacewhat> <replacewith>', 2)
        self.AddCommand("copy", CopyCommand, 'builder', 'Used to copy and then paste an area of blocks', '', 0)
        self.AddCommand("paste", PasteCommand, 'builder', 'Used to paste blocks after you have copied them with /copy', '', 0)
        self.AddCommand("destroytower", DestroyTowerCommand, 'operator', 'Destroys tower of the same block. Useful for cleaning', '', 0)

class CancelCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):
        if pPlayer.GetPluginData(DRAW_KEY) is not None:
            pPlayer.SetPluginData(DRAW_KEY, None)
            pPlayer.SendMessage("&SDraw command cancelled")
            return
        else:
            pPlayer.SendMessage("&RYou are not currently using a draw command!")

class PlaceCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):
        DrawObject = pPlayer.GetPluginData(DRAW_KEY)
        if DrawObject is None:
            pPlayer.SendMessage("&RYou are not currently using a draw command!")
        else:
            DrawObject.OnAttemptPlaceBlock(pPlayer.GetWorld(), BLOCK_ROCK, pPlayer.GetX() / 32, pPlayer.GetY() / 32, pPlayer.GetZ() / 32)
   
class CuboidCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):
        Material = ' '.join(Args)
        if GetBlockIDFromName(Material) is not None:
            pPlayer.SetPluginData(DRAW_KEY, Cuboid(pPlayer, Material))
            pPlayer.SendMessage("&SPlace two blocks or use /place to represent the cuboid's corners")
        else:
            pPlayer.SendMessage("&R%s is not a valid block!" % Material)

class CuboidWCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):
        Material = ' '.join(Args)
        if GetBlockIDFromName(Material) is not None:
            pPlayer.SetPluginData(DRAW_KEY, WireFrameCuboid(pPlayer, Material))
            pPlayer.SendMessage("&SPlace two blocks or use /place to represent the cuboid corners")
        else:
            pPlayer.SendMessage("&R%s is not a valid block!" % Material)

            
class CuboidHCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):
        Material = ' '.join(Args)
        if GetBlockIDFromName(Material) is not None:
            pPlayer.SetPluginData(DRAW_KEY, HollowCuboid(pPlayer, Material))
            pPlayer.SendMessage("&SPlace two blocks or use /place to represent the cuboid's corners")
        else:
            pPlayer.SendMessage("&R%s is not a valid block!" % Material)  

class CuboidRCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):    
        Material1 = Args[0]
        Material2 = Args[1]
        if GetBlockIDFromName(Material1) is None:
            pPlayer.SendMessage("&R%s is not a valid block!" % Material1)
            return
        elif GetBlockIDFromName(Material2) is None:
            pPlayer.SendMessage("&R%s is not a valid block!" % Material2)
            return
        else:
            pPlayer.SetPluginData(DRAW_KEY, ReplaceCuboid(pPlayer, Material1, Material2))
            pPlayer.SendMessage("&SPlace two blocks or use /place to represent the cuboid's corners")
         
class CopyCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):
        pPlayer.SetPluginData(DRAW_KEY, CopyAction(pPlayer))
        pPlayer.SendMessage("&SPlace two blocks or use /place around the area you wish to copy")
                                                   
class PasteCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):
        if pPlayer.GetPluginData(COPY_KEY) is None:
            pPlayer.SendMessage("&RYou have not copied anything! Use /copy first")
            return
        else:
            pPlayer.SendMessage("&SPlace a block, or use /place where you want to paste")
            pPlayer.SetPluginData(DRAW_KEY, PasteAction(pPlayer))

class MeasureCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):
        pPlayer.SetPluginData(DRAW_KEY, Measure(pPlayer))
        pPlayer.SendMessage("&SPlace two blocks to measure the distance between")
        
class DestroyTowerCommand(CommandObject):
    def Run(self, pPlayer, Args, Message):
        DrawData = pPlayer.GetPluginData(DRAW_KEY)
        if type(DrawData) == DestroyTowerAction:
            pPlayer.SetPluginData(DRAW_KEY, None)
            pPlayer.SendMessage("&SDestroy tower disabled")
        else:
            pPlayer.SetPluginData(DRAW_KEY, DestroyTowerAction(pPlayer))
            pPlayer.SendMessage("&SDestroy tower enabled")

#######################################
#        Draw actions go below        #
#######################################    
class DrawAction(object):
    '''Abstract class which when inherited is in charge of actually doing all of the drawing'''
    def __init__(self, pPlayer):
        self.pPlayer = pPlayer
        self.DisallowMapChanges = True
        self.IsLogged = True
        self.IsOneUse = True
        self.EnableWorldLocking = True
        
    def OnAttemptPlaceBlock(self, pWorld, BlockValue, x, y, z):
        pass
    def DrawBlock(self, x, y, z, Value):
        self.pPlayer.GetWorld().AttemptSetBlock(self.pPlayer, x, y, z, Value, AutomatedChange = True, ResendToClient = True)
    def PreDraw(self):
        pass #Calculate blocks here
    def TryDraw(self, NumBlocks):
        if self.IsOneUse:
            self.pPlayer.SetPluginData(DRAW_KEY, None)
        Limit = int(self.pPlayer.ServerControl.ConfigValues.GetValue("drawcommands", self.pPlayer.GetRank(), "2147483647"))
        if NumBlocks > Limit:
            self.pPlayer.SendMessage("&RYou are only allowed to draw %d blocks. Proposed action would affect %d blocks" % (Limit, NumBlocks))
        else:
            if NumBlocks > LOCK_LEVEL and self.EnableWorldLocking:
                self.pPlayer.GetWorld().Lock()
            TimeFormat = time.strftime("%d %b %Y [%H:%M:%S]", time.localtime())
            LogLine = "%s User %s (%s) used draw command (%s) on map %s, changed %d blocks\n" % (TimeFormat,
                    self.pPlayer.GetName(), self.pPlayer.GetIP(), self.__class__.__name__,
                    self.pPlayer.GetWorld().Name, NumBlocks)
            LogFile = self.pPlayer.ServerControl.CommandHandle.LogFile
            if LogFile is not None:
                LogFile.write(LogLine)
            self.DoDraw()
            if NumBlocks > LOCK_LEVEL and self.EnableWorldLocking:
                self.pPlayer.GetWorld().UnLock()
    def DoDraw(self):
        pass        
        
class TwoStepDrawAction(DrawAction):
    '''Useful base for DrawAction classes which require
    ...Two blocks to be placed before actually drawing'''
    def __init__(self, pPlayer):
        DrawAction.__init__(self, pPlayer)
        self.X1, self.Y1, self.Z1 = -1, -1, -1
        self.X2, self.Y2, self.Z2 = -1, -1, -1
        self.Pos1 = (-1, -1, 1)
        self.Pos2 = (-1, -1, -1)
        self.TempX, self.TempY, self.TempZ = -1, -1, -1    
        self.AllowAir = False
            
    def ArrangeCoordinates(self, X1, Y1, Z1, X2, Y2, Z2):
        return min(X1, X2), min(Y1, Y2), min(Z1, Z2), max(X1, X2), max(Y1, Y2), max(Z1, Z2)

    def OnFirstBlockPlaced(self, pWorld, BlockValue, x, y, z):
        pass
                                
    def OnAttemptPlaceBlock(self, pWorld, BlockValue, x, y, z):
        if BlockValue == BLOCK_AIR and not self.AllowAir:
            return
        if pWorld.WithinBounds(x, y, z) == False:
            self.pPlayer.SendMessage("&RCoordinate is outside map bounds.")
            return
        if self.TempX == -1:
            self.TempX = x
            self.TempY = y
            self.TempZ = z
            self.Pos1 = (x, y, z)
            self.OnFirstBlockPlaced(pWorld, BlockValue, x, y, z)
            return False
        else:
            self.Pos2 = (x, y, z)
            self.X1, self.Y1, self.Z1, self.X2, self.Y2, self.Z2 = self.ArrangeCoordinates(self.TempX, self.TempY, self.TempZ, x, y, z)    
            self.PreDraw()
            return False
       
class Measure(TwoStepDrawAction):
    def __init__(self, pPlayer):
        TwoStepDrawAction.__init__(self, pPlayer)
        self.IsLogged = False
        
    def OnFirstBlockPlaced(self, pWorld, BlockValue, x, y, z):
        self.pPlayer.SendMessage("&SNow place the final block to measure the distance")
    def PreDraw(self):
        self.TryDraw(0)
    def DoDraw(self):
        dx = self.X2 + 1 - self.X1
        dy = self.Y2 + 1 - self.Y1
        dz = self.Z2 + 1 - self.Z1
        Distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        self.pPlayer.SendMessage("&SThe distance from &V%s &Sto &V%s &Sis: &V%d" % (self.Pos1, self.Pos2, Distance))
        
class Cuboid(TwoStepDrawAction):
    def __init__(self, pPlayer, Material):
        TwoStepDrawAction.__init__(self, pPlayer)
        self.Material = GetBlockIDFromName(Material)
        
    def OnFirstBlockPlaced(self, pWorld, BlockValue, x, y, z):
        self.pPlayer.SendMessage("&SNow place the second block for the cuboid to complete drawing.")
    def PreDraw(self):
        NumBlocks = (self.X2 + 1 - self.X1) * (self.Y2 + 1 - self.Y1) * (self.Z2 + 1 - self.Z1)
        self.TryDraw(NumBlocks)     
    
    def DoDraw(self):
        self.pPlayer.SendMessage("&SDrawing cuboid!")
        for x in xrange(self.X1, self.X2 + 1):
            for y in xrange(self.Y1, self.Y2 + 1):
                for z in xrange(self.Z1, self.Z2 + 1):
                    self.DrawBlock(x, y, z, self.Material)
        self.pPlayer.SendMessage("&SFinished drawing cuboid")
        
class ReplaceCuboid(TwoStepDrawAction):
    '''Material 1 is replaced with Material 2'''
    def __init__(self, pPlayer, Material1, Material2):
        TwoStepDrawAction.__init__(self, pPlayer)
        self.Material1 = GetBlockIDFromName(Material1)
        self.Material2 = GetBlockIDFromName(Material2)
        self.CoordArray = list()
        
    def OnFirstBlockPlaced(self, pWorld, BlockValue, x, y, z):
        self.pPlayer.SendMessage("&SNow place the second block for the cuboids to be replaced.")
        
    def PreDraw(self):
        Count = 0
        for x in xrange(self.X1, self.X2 + 1):
            for y in xrange(self.Y1, self.Y2 + 1):
                for z in xrange(self.Z1, self.Z2 + 1):
                    if self.pPlayer.GetWorld().GetBlock(x, y, z) == self.Material1:
                        Count += 1
                        self.CoordArray.append((x, y, z))
                        
        self.TryDraw(Count)  
    
    def DoDraw(self):
        self.pPlayer.SendMessage("&SReplacing blocks!")
        for x, y, z in self.CoordArray:
            self.DrawBlock(x, y, z, self.Material2)
        self.pPlayer.SendMessage("&SFinished replacing blocks!")
        
        

class HollowCuboid(Cuboid):
    def PreDraw(self):
        dx = self.X2 - self.X1
        dy = self.Y2 - self.Y1
        dz = self.Z2 - self.Z1
        NumBlocks = (dx * dy) + (dx * dz) + (dy * dz)
        NumBlocks += 1
        NumBlocks *= 2
        self.TryDraw(NumBlocks)     
            
    def DoDraw(self):
        self.pPlayer.SendMessage("&SDrawing hollow cuboid!")
        for x in xrange(self.X1, self.X2 + 1):
            for y in xrange(self.Y1, self.Y2 + 1):
                for z in xrange(self.Z1, self.Z2 + 1):
                    if x == self.X1 or x == self.X2 or y == self.Y1 or y == self.Y2 or z == self.Z1 or z == self.Z2:
                        self.DrawBlock(x, y, z, self.Material)
        self.pPlayer.SendMessage("&SFinished drawing hollow cuboid")
 
class WireFrameCuboid(Cuboid):
    def PreDraw(self):
        dx = self.X2 + 1 - self.X1
        dy = self.Y2 + 1 - self.Y1
        dz = self.Z2 + 1 - self.Z1
        NumBlocks = dx * 4 + dy * 4 + dz * 4
        self.TryDraw(NumBlocks)
        
    def DoDraw(self):
        for x in xrange(self.X1, self.X2 + 1):
            self.DrawBlock(x, self.Y1, self.Z1, self.Material)
            self.DrawBlock(x, self.Y2, self.Z1, self.Material)
            self.DrawBlock(x, self.Y1, self.Z2, self.Material)
            self.DrawBlock(x, self.Y2, self.Z2, self.Material)
        for y in xrange(self.Y1, self.Y2 + 1):
            self.DrawBlock(self.X1, y, self.Z1, self.Material)
            self.DrawBlock(self.X2, y, self.Z1, self.Material)
            self.DrawBlock(self.X1, y, self.Z2, self.Material)
            self.DrawBlock(self.X2, y, self.Z2, self.Material)

        for z in xrange(self.Z1, self.Z2 + 1):
            self.DrawBlock(self.X1, self.Y1, z, self.Material)
            self.DrawBlock(self.X2, self.Y1, z, self.Material)
            self.DrawBlock(self.X1, self.Y2, z, self.Material)
            self.DrawBlock(self.X2, self.Y2, z, self.Material)

        self.pPlayer.SendMessage("&SFinished drawing the wireframe cuboid")
        
class CopyInformation(object):
    '''Used for storing block data in /copy /paste commands'''
    def __init__(self, X, Y, Z):
        self.X = X
        self.Y = Y
        self.Z = Z
        self.Blocks = array.array('B')
        
class CopyAction(TwoStepDrawAction):
    def __init__(self, pPlayer):
        TwoStepDrawAction.__init__(self, pPlayer)
        self.EnableWorldLocking = False
        
    def OnFirstBlockPlaced(self, pWorld, BlockValue, x, y, z):
        self.pPlayer.SendMessage("&SNow place the second block to define the area")
        
    def PreDraw(self):
        NumBlocks = (self.X2 + 1 - self.X1) * (self.Y2 + 1 - self.Y1) * (self.Z2 + 1 - self.Z1)
        self.TryDraw(NumBlocks)
            
    def DoDraw(self):
        CopyData = CopyInformation(self.X2 + 1 - self.X1, self.Y2 + 1 - self.Y1, self.Z2 + 1 - self.Z1)
        for x in xrange(self.X1, self.X2 + 1):
            for y in xrange(self.Y1, self.Y2 + 1):
                for z in xrange(self.Z1, self.Z2 + 1):
                    try:
                        CopyData.Blocks.append(self.pPlayer.GetWorld().GetBlock(x, y, z))
                    except IndexError:
                        self.pPlayer.SendMessage("&RCannot copy that area as it extends outside of map bounds")
                        return
                    
        self.pPlayer.SetPluginData(COPY_KEY, CopyData)
        self.pPlayer.SendMessage("&SData has been copied. Use /paste to paste")
                    
class PasteAction(DrawAction):
    def __init__(self, pPlayer):
        DrawAction.__init__(self, pPlayer)
        self.X, self.Y, self.Z = -1, -1, -1
        self.CopyData = self.pPlayer.GetPluginData(COPY_KEY)
        
    def OnAttemptPlaceBlock(self, pWorld, BlockValue, x, y, z):
        self.X = x
        self.Y = y
        self.Z = z
        self.PreDraw()
    
    def PreDraw(self):
        self.TryDraw(self.CopyData.X * self.CopyData.Y * self.CopyData.Z)
        
    def DoDraw(self):
        Index = 0
        for x in xrange(self.CopyData.X):
            for y in xrange(self.CopyData.Y):
                for z in xrange(self.CopyData.Z):
                    self.DrawBlock(self.X + x, self.Y + y, self.Z + z, self.CopyData.Blocks[Index])
                    Index += 1
        self.pPlayer.SendMessage("&SPasting complete.")
        
class DestroyTowerAction(DrawAction):
    def __init__(self, pPlayer):
        DrawAction.__init__(self, pPlayer)
        self.IsLogged = False
        self.IsOneUse = False
        self.DisallowMapChanges = False
        self.BusyDrawing = False
        self.X, self.Y, self.Z = -1, -1, -1
        
    def OnAttemptPlaceBlock(self, pWorld, BlockValue, x, y, z):
        if self.BusyDrawing:
            return
        self.X = x
        self.Y = y
        self.Z = z
        self.PreDraw()
        
    def PreDraw(self):
        self.TryDraw(0)
        
    def DoDraw(self):
        self.BusyDrawing = True
        BadBlock = self.pPlayer.GetWorld().GetBlock(self.X, self.Y, self.Z)
        for z in xrange(self.Z, -1, -1):
            if self.pPlayer.GetWorld().GetBlock(self.X, self.Y, z) == BadBlock:
                self.DrawBlock(self.X, self.Y, z, BLOCK_AIR)
            else:
                break
        self.BusyDrawing = False
        
