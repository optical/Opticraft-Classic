from core.jsondict import JSONDict

class PlayerDbDataEntry(object):
    '''This class represents a row in the player database.'''
    def __init__(self, ServerControl, Row = None):
        self.HasLoaded = False
        self.ServerControl = ServerControl
        self.Username = ""
        self.JoinTime = 0
        self.BlocksErased = 0
        self.BlocksMade = 0
        self.LastIps = ""
        self.LastIP = ""
        self.JoinNotifications = self.ServerControl.JoinNotificationsDefault
        self.ChatMessageCount = 0
        self.KickCount = 0
        self.TimePlayed = 0
        self.LoginCount = 0
        self.LoginTime = 0
        self.BannedBy = ""
        self.RankedBy = ""
        self.PermanentPluginData = JSONDict()        
        
        if Row is not None:
            self.LoadFromRow(Row)

            
    def Save(self):
        '''Saves the values back to the player database asynchronously'''
        QueryString = "REPLACE INTO Players Values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"     
        QueryParams = (self.Username, self.JoinTime, self.LoginTime, self.BlocksMade, self.BlocksErased, self.LastIP, self.LastIps, self.JoinNotifications,
                      self.TimePlayed, self.KickCount, self.ChatMessageCount, self.LoginCount, self.BannedBy, self.RankedBy,
                      self.PermanentPluginData.AsJSON())
        self.ServerControl.PlayerDBThread.Tasks.put(["EXECUTE", QueryString, QueryParams])
    
    def LoadFromRow(self, Row):
        self.HasLoaded = True
        self.Username = Row["Username"]
        self.JoinTime = Row["Joined"]
        self.BlocksMade = Row["BlocksMade"] + self.BlocksMade
        self.BlocksErased = Row["BlocksDeleted"] + self.BlocksErased
        self.LastIps = Row["IpLog"]
        self.JoinNotifications = Row["JoinNotifications"]
        self.ChatMessageCount = Row["ChatLines"] + self.ChatMessageCount
        self.KickCount = Row["KickCount"]
        self.TimePlayed = Row["PlayedTime"]
        self.LoginCount = Row["LoginCount"]
        self.LoginTime = Row["LastLogin"]
        self.LastIP = Row["LastIP"]
        self.BannedBy = Row["BannedBy"]
        self.RankedBy = Row["RankedBy"]
        JSONData = Row["PluginData"]
        if JSONData != "":
            self.PermanentPluginData = JSONDict.FromJSON(Row["PluginData"])    
