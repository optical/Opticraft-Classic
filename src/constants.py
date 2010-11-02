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
BLOCK_STONE = 4
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

DisabledBlocks = set([BLOCK_WATER,BLOCK_STILLWATER,BLOCK_LAVA,BLOCK_STILLLAVA,BLOCK_HARDROCK])

#Permission ranks
#These are subject to change as more ranks are added over time.
# 0 = Spectator
# 1 = Trusted
# 2 = Builder
# 3 = Operator
# 4 = Admin
# 5 = Owner

RankToName = {
    "g" : "Guest",
    "s" : "Spectator",
    "t": "Recruit",
    "b": "Builder",
    "o": "Operator",
    "a": "Admin",
    "z": "Owner"
}
RankToColour = {
    "g" : "&f",
    "s": "&f",
    "a": "&9", #Blue
    "b": "&a", #Light green
    "o": "&b", #Teal
    "t": "&7", #Grey
    "z": "&c" #Red
}
RankToLevel = {
    "s": 3,
    "g" : 5,
    "t": 7,
    "b": 10,
    "o": 20,
    "a": 30,
    "z": 0xFF,
}
RankToDescription = {
    "s": "Griefers are set to this rank. They may not build",
    "g" : "Everyone starts out at this rank",
    "t": "Users who show potential get promoted to this rank. They may use lava and water",
    "b": "Users who have proved themself and played for several days get this rank. They may build on builder only maps",
    "o": "Mature, responsible users get promoted to this. Do not ask to be promoted to this rank",
    "a": "These users are the server administrators",
    "z": "This is the owner of the server",
}
ValidRanks = ''
for Rank in RankToName.keys():
    if Rank != '':
        ValidRanks = "%s %s " %(ValidRanks,Rank)
#Taken from http://snipplr.com/view/5713/python-elapsedtime-human-readable-time-span-given-total-seconds/
def ElapsedTime(seconds, suffixes=[' year',' week',' day',' hour',' minute',' second'], add_s=True, separator=' '):
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