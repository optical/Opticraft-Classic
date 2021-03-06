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
SMSG_BLOCKSET = 6
SMSG_SPAWNPOINT = 7
SMSG_PLAYERPOS = 8
SMSG_POSITION_UDPDATE = 10
SMSG_ORIENTATION_UPDATE = 11
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
BlockNamesToID["admincrete"] = BLOCK_HARDROCK
BlockNamesToID["solid"] = BLOCK_HARDROCK
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
BlockNamesToID["redcloth"] = BLOCK_RED_CLOTH
BlockNamesToID["redwool"] = BLOCK_RED_CLOTH
BlockNamesToID["orange"] = BLOCK_ORANGE
BlockNamesToID["orangecloth"] = BLOCK_ORANGE
BlockNamesToID["orangewool"] = BLOCK_ORANGE
BlockNamesToID["yellow"] = BLOCK_YELLOW
BlockNamesToID["yeollowcloth"] = BLOCK_YELLOW
BlockNamesToID["yellowwool"] = BLOCK_YELLOW
BlockNamesToID["lightgreen"] = BLOCK_LIME
BlockNamesToID["lightgreenwool"] = BLOCK_LIME
BlockNamesToID["lightgreencloth"] = BLOCK_LIME
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
BlockNamesToID["bluewool"] = BLOCK_BLUE
BlockNamesToID["bluecloth"] = BLOCK_BLUE
BlockNamesToID["purple"] = BLOCK_PURPLE
BlockNamesToID["purplewool"] = BLOCK_PURPLE
BlockNamesToID["purplecloth"] = BLOCK_PURPLE
BlockNamesToID["indigo"] = BLOCK_INDIGO
BlockNamesToID["indigocloth"] = BLOCK_INDIGO
BlockNamesToID["indigowool"] = BLOCK_INDIGO
BlockNamesToID["violet"] = BLOCK_VIOLET
BlockNamesToID["violetwool"] = BLOCK_VIOLET
BlockNamesToID["violetcloth"] = BLOCK_VIOLET
BlockNamesToID["magenta"] = BLOCK_MAGENTA
BlockNamesToID["magentawool"] = BLOCK_MAGENTA
BlockNamesToID["magentacloth"] = BLOCK_MAGENTA
BlockNamesToID["pink"] = BLOCK_PINK
BlockNamesToID["pinkwool"] = BLOCK_PINK
BlockNamesToID["pinkcloth"] = BLOCK_PINK
BlockNamesToID["black"] = BLOCK_BLACK
BlockNamesToID["blackwool"] = BLOCK_BLACK
BlockNamesToID["blackcloth"] = BLOCK_BLACK
BlockNamesToID["grey"] = BLOCK_GREY
BlockNamesToID["greywool"] = BLOCK_GREY
BlockNamesToID["greycloth"] = BLOCK_GREY
BlockNamesToID["white"] = BLOCK_WHITE
BlockNamesToID["whitecloth"] = BLOCK_WHITE
BlockNamesToID["whitewool"] = BLOCK_WHITE
BlockNamesToID["yellowflower"] = BLOCK_YELLOWFLOWER
BlockNamesToID["rose"] = BLOCK_REDFLOWER
BlockNamesToID["redflower"] = BLOCK_REDFLOWER
BlockNamesToID["redrose"] = BLOCK_REDFLOWER
BlockNamesToID["redmushroom"] = BLOCK_RED_MUSHROOM
BlockNamesToID["brownmushroom"] = BLOCK_MUSHROOM
BlockNamesToID["goldblock"] = BLOCK_GOLD
BlockNamesToID["ironblock"] = BLOCK_IRON
BlockNamesToID["step"] = BLOCK_STEP
BlockNamesToID["doublestep"] = BLOCK_DOUBLESTEP
BlockNamesToID["stair"] = BLOCK_STEP
BlockNamesToID["brick"] = BLOCK_BRICK
BlockNamesToID["tnt"] = BLOCK_TNT
BlockNamesToID["bookcase"] = BLOCK_BOOKCASE
BlockNamesToID["book"] = BLOCK_BOOKCASE
BlockNamesToID["books"] = BLOCK_BOOKCASE
BlockNamesToID["mossycobblestone"] = BLOCK_MOSSYROCK
BlockNamesToID["mossyrock"] = BLOCK_MOSSYROCK
BlockNamesToID["mossyrock"] = BLOCK_MOSSYROCK
BlockNamesToID["greencobblestone"] = BLOCK_MOSSYROCK
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

import string
WaterBlocks = frozenset([BLOCK_WATER, BLOCK_STILLWATER])
LavaBlocks = frozenset([BLOCK_LAVA, BLOCK_STILLLAVA])
DisabledChars = ''.join([c for c in map(chr, range(256)) if c not in string.ascii_letters + string.digits + string.punctuation + string.whitespace]) + '&\r\n'
ColourChars = frozenset('1234567890abcedfABCEDF')

def ParseWordAsTime(Word):
    '''Returns the number of seconds in a given time span.
    eg: "1m2w3d5h" returns 4078800 (1 month, 2 weeks, 3 days, 5hours)'''
    HourMultiplier = 3600
    DayMultiplier = HourMultiplier * 24
    WeekMultiplier = DayMultiplier * 7
    MonthMultiplier = DayMultiplier * 30
    YearMultiplier = WeekMultiplier * 52
    Duration = 0
    i = 0
    while i < len(Word):
        if Word[i].isdigit() == False:
            raise Exception;
        NumberString = ''
        
        while i < len(Word)and Word[i].isdigit():
            NumberString += Word[i]
            i += 1
            
        if i >= len(Word):
            return - 1
        
        Num = int(NumberString)
        Char = Word[i].lower()
        Multi = 0
        if Char == "h":
            Multi = HourMultiplier
        elif Char == "d":
            Multi = DayMultiplier
        elif Char == "w":
            Multi = WeekMultiplier
        elif Char == "m":
            Multi = MonthMultiplier
        elif Char == "y":
            Multi = YearMultiplier
        else:
            return - 1
        
        Duration += Multi * Num
        i += 1
        while i < len(Word) and Word[i].isdigit() == False:
            i += 1
    
    return Duration

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
