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
import ordereddict
#Client messages
CMSG_IDENTIFY = 0
CMSG_BLOCKCHANGE = 5
CMSG_POSITIONUPDATE = 8
CMSG_MESSAGE = 13
#End!
#Server Messages
SMSG_INITIAL = 0
SMSG_KEEPALIVE = 1
SMSG_PRECHUNK = 2
SMSG_CHUNK = 3
SMSG_LEVELSIZE = 4
SMSG_BLOCKCHANGE = 5
SMSG_BLOCKSET = 6
SMSG_SPAWNPOINT = 7
SMSG_PLAYERPOS = 8
SMSG_PLAYERDIR = 11
SMSG_PLAYERLEAVE = 12
SMSG_MESSAGE = 13
SMSG_DISCONNECT = 14
SMSG_USERTYPE = 15
#Sizes of CMSG packets.
PacketSizes = {
               CMSG_IDENTIFY: 130,
               CMSG_BLOCKCHANGE: 8,
               CMSG_POSITIONUPDATE: 9,
               CMSG_MESSAGE: 65
}
#Block types
BLOCK_AIR = 0
BLOCK_ROCK = 1
BLOCK_GRASS = 2
BLOCK_DIRT = 3
BLOCK_COBBLESTONE = 4
BLOCK_WOOD = 5
BLOCK_PLANK = 5
BLOCK_PLANT = 6
BLOCK_HARDROCK = 7
BLOCK_WATER = 8
BLOCK_STILLWATER = 9
BLOCK_LAVA = 10
BLOCK_STILLLAVA = 11
BLOCK_SAND = 12
BLOCK_GRAVEL = 13
BLOCK_GOLDORE = 14
BLOCK_COPPERORE = 15
BLOCK_COALORE = 16
BLOCK_LOG = 17
BLOCK_LEAVES = 18
BLOCK_SPONGE = 19
BLOCK_GLASS = 20
BLOCK_RED_CLOTH = 21
BLOCK_ORANGE = 22
BLOCK_YELLOW = 23
BLOCK_LIME = 24
BLOCK_GREEN = 25
BLOCK_TEAL = 26
BLOCK_CYAN = 27
BLOCK_BLUE = 28
BLOCK_PURPLE = 29
BLOCK_INDIGO = 30
BLOCK_VIOLET = 31
BLOCK_MAGENTA = 32
BLOCK_PINK = 33
BLOCK_DARKGREY = 34
BLOCK_BLACK = 34
BLOCK_GREY = 35
BLOCK_WHITE = 36
BLOCK_YELLOWFLOWER = 37
BLOCK_REDFLOWER = 38
BLOCK_MUSHROOM = 39
BLOCK_RED_MUSHROOM = 40
BLOCK_GOLD = 41
BLOCK_STEEL = 42
BLOCK_IRON = 42
BLOCK_DOUBLESTEP = 43
BLOCK_STEP = 44
BLOCK_BRICK = 45
BLOCK_TNT = 46
BLOCK_BOOKCASE = 47
BLOCK_MOSSYROCK = 48
BLOCK_OBSIDIAN = 49
BLOCK_END = 50
BlockNamesToID = ordereddict.OrderedDict()
BlockNamesToID["air"] = BLOCK_AIR
BlockNamesToID["blank"] = BLOCK_AIR
BlockNamesToID["stone"] = BLOCK_ROCK
BlockNamesToID["rock"] = BLOCK_ROCK
BlockNamesToID["grass"] = BLOCK_GRASS
BlockNamesToID["dirt"] = BLOCK_DIRT
BlockNamesToID["cobblestone"] = BLOCK_COBBLESTONE
BlockNamesToID["wood"] = BLOCK_WOOD
BlockNamesToID["plant"] = BLOCK_PLANT
BlockNamesToID["sappling"] = BLOCK_PLANT
BlockNamesToID["tree"] = BLOCK_PLANT
BlockNamesToID["hardrock"] = BLOCK_HARDROCK
BlockNamesToID["adminium"] = BLOCK_HARDROCK
BlockNamesToID["adminite"] = BLOCK_HARDROCK
BlockNamesToID["water"] = BLOCK_STILLWATER
BlockNamesToID["lava"] = BLOCK_STILLLAVA
BlockNamesToID["sand"] = BLOCK_SAND
BlockNamesToID["gravel"] = BLOCK_GRAVEL
BlockNamesToID["gold"] = BLOCK_GOLD
BlockNamesToID["goldore"] = BLOCK_GOLDORE
BlockNamesToID["iron"] = BLOCK_IRON
BlockNamesToID["ironore"] = BLOCK_IRON
BlockNamesToID["coal"] = BLOCK_COALORE
BlockNamesToID["coalore"] = BLOCK_COALORE
BlockNamesToID["copper"] = BLOCK_COPPERORE
BlockNamesToID["copperore"] = BLOCK_COPPERORE
BlockNamesToID["log"] = BLOCK_LOG
BlockNamesToID["leaves"] = BLOCK_LEAVES
BlockNamesToID["sponge"] = BLOCK_SPONGE
BlockNamesToID["glass"] = BLOCK_GLASS
BlockNamesToID["red"] = BLOCK_RED_CLOTH
BlockNamesToID["red cloth"] = BLOCK_RED_CLOTH
BlockNamesToID["red wool"] = BLOCK_RED_CLOTH
BlockNamesToID["orange"] = BLOCK_ORANGE
BlockNamesToID["orange cloth"] = BLOCK_ORANGE
BlockNamesToID["orange wool"] = BLOCK_ORANGE
BlockNamesToID["yellow"] = BLOCK_YELLOW
BlockNamesToID["yeollow cloth"] = BLOCK_YELLOW
BlockNamesToID["yellow wool"] = BLOCK_YELLOW
BlockNamesToID["lightgreen"] = BLOCK_LIME
BlockNamesToID["lightgreen wool"] = BLOCK_LIME
BlockNamesToID["lightgreen cloth"] = BLOCK_LIME
BlockNamesToID["lime"] = BLOCK_LIME
BlockNamesToID["limecloth"] = BLOCK_LIME
BlockNamesToID["limewool"] = BLOCK_LIME
BlockNamesToID["green"] = BLOCK_GREEN
BlockNamesToID["greencloth"] = BLOCK_GREEN
BlockNamesToID["greenwool"] = BLOCK_GREEN
BlockNamesToID["aqua"] = BLOCK_TEAL
BlockNamesToID["aquacloth"] = BLOCK_TEAL
BlockNamesToID["aquawool"] = BLOCK_TEAL
BlockNamesToID["teal"] = BLOCK_TEAL
BlockNamesToID["tealwool"] = BLOCK_TEAL
BlockNamesToID["tealcloth"] = BLOCK_TEAL
BlockNamesToID["cyan"] = BLOCK_CYAN
BlockNamesToID["cyanwool"] = BLOCK_CYAN
BlockNamesToID["cyancloth"] = BLOCK_CYAN
BlockNamesToID["blue"] = BLOCK_BLUE
BlockNamesToID["blue wool"] = BLOCK_BLUE
BlockNamesToID["blue cloth"] = BLOCK_BLUE
BlockNamesToID["purple"] = BLOCK_PURPLE
BlockNamesToID["purple wool"] = BLOCK_PURPLE
BlockNamesToID["purple cloth"] = BLOCK_PURPLE
BlockNamesToID["indigo"] = BLOCK_INDIGO
BlockNamesToID["indigo cloth"] = BLOCK_INDIGO
BlockNamesToID["indigo wool"] = BLOCK_INDIGO
BlockNamesToID["violet"] = BLOCK_VIOLET
BlockNamesToID["violet wool"] = BLOCK_VIOLET
BlockNamesToID["violet cloth"] = BLOCK_VIOLET
BlockNamesToID["magenta"] = BLOCK_MAGENTA
BlockNamesToID["magenta wool"] = BLOCK_MAGENTA
BlockNamesToID["magenta cloth"] = BLOCK_MAGENTA
BlockNamesToID["pink"] = BLOCK_PINK
BlockNamesToID["pink wool"] = BLOCK_PINK
BlockNamesToID["pink cloth"] = BLOCK_PINK
BlockNamesToID["black"] = BLOCK_BLACK
BlockNamesToID["black wool"] = BLOCK_BLACK
BlockNamesToID["black cloth"] = BLOCK_BLACK
BlockNamesToID["grey"] = BLOCK_GREY
BlockNamesToID["grey wool"] = BLOCK_GREY
BlockNamesToID["grey cloth"] = BLOCK_GREY
BlockNamesToID["white"] = BLOCK_WHITE
BlockNamesToID["white cloth"] = BLOCK_WHITE
BlockNamesToID["white wool"] = BLOCK_WHITE
BlockNamesToID["yellow flower"] = BLOCK_YELLOWFLOWER
BlockNamesToID["rose"] = BLOCK_REDFLOWER
BlockNamesToID["red flower"] = BLOCK_REDFLOWER
BlockNamesToID["red rose"] = BLOCK_REDFLOWER
BlockNamesToID["red mushroom"] = BLOCK_RED_MUSHROOM
BlockNamesToID["brown mushroom"] = BLOCK_MUSHROOM
BlockNamesToID["gold block"] = BLOCK_GOLD
BlockNamesToID["iron block"] = BLOCK_IRON
BlockNamesToID["step"] = BLOCK_STEP
BlockNamesToID["doublestep"] = BLOCK_DOUBLESTEP
BlockNamesToID["stair"] = BLOCK_STEP
BlockNamesToID["brick"] = BLOCK_BRICK
BlockNamesToID["tnt"] = BLOCK_TNT
BlockNamesToID["bookcase"] = BLOCK_BOOKCASE
BlockNamesToID["book"] = BLOCK_BOOKCASE
BlockNamesToID["books"] = BLOCK_BOOKCASE
BlockNamesToID["mossy cobblestone"] = BLOCK_MOSSYROCK
BlockNamesToID["mossyrock"] = BLOCK_MOSSYROCK
BlockNamesToID["mossy rock"] = BLOCK_MOSSYROCK
BlockNamesToID["green cobblestone"] = BLOCK_MOSSYROCK
BlockNamesToID["obsidian"] = BLOCK_OBSIDIAN

def GetBlockIDFromName(Name):
    return BlockNamesToID.get(Name.lower(), None)
def InvertDictionary(Dictionary):
    NewDict = dict()
    for key in Dictionary.iterkeys():
        if Dictionary[key] not in NewDict:
            NewDict[Dictionary[key]] = key
    return NewDict
IDFromName = InvertDictionary(BlockNamesToID)
def GetBlockNameFromID(ID):
    return IDFromName.get(ID, None)

def UnicodeToStr(obj):
    '''Terrible function for json decoding'''
    if type(obj) == unicode:
        return str(obj)
    elif type(obj) == list:
        return [UnicodeToStr(x) for x in obj]
    elif type(obj) == dict:
        NewDict = {}
        for Key, Value in obj.iteritems():
            Key = UnicodeToStr(Key)
            Value = UnicodeToStr(Value)
            NewDict[Key] = Value
            return NewDict
        else:
            return obj


import string
DisabledBlocks = set([BLOCK_WATER, BLOCK_STILLWATER, BLOCK_LAVA, BLOCK_STILLLAVA, BLOCK_HARDROCK])
DisabledChars = ''.join([c for c in map(chr, range(256)) if c not in string.ascii_letters + string.digits + string.punctuation + string.whitespace]) + '&\r\n'
ColourChars = frozenset('1234567890abcedfABCEDF')
#Taken from http://snipplr.com/view/5713/python-elapsedtime-human-readable-time-span-given-total-seconds/
def ElapsedTime(seconds, suffixes = [' year', ' week', ' day', ' hour', ' minute', ' second'], add_s = True, separator = ' '):
    """
	Takes an amount of seconds and turns it into a human-readable amount of time.
	"""
    # the formatted time string to be returned
    time = []

    # the pieces of time to iterate over (days, hours, minutes, etc)
    # - the first piece in each tuple is the suffix (d, h, w)
    # - the second piece is the length in seconds (a day is 60s * 60m * 24h)
    parts = [(suffixes[0], 60 * 60 * 24 * 7 * 52),
            (suffixes[1], 60 * 60 * 24 * 7),
            (suffixes[2], 60 * 60 * 24),
            (suffixes[3], 60 * 60),
            (suffixes[4], 60),
            (suffixes[5], 1)]

    # for each time piece, grab the value and remaining seconds, and add it to
    # the time string
    for suffix, length in parts:
        value = seconds / length
        if value > 0:
            seconds = seconds % length
            time.append('%s%s' % (str(value),
                                (suffix, (suffix, suffix + 's')[value > 1])[add_s]))
        if seconds < 1:
            break

    return separator.join(time)
