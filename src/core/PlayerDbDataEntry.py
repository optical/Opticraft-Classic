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
        QueryParams = (self.Username, self.JoinTime, self.LoginTime, self.BlocksMade, self.BlocksErased, '', self.LastIps, self.JoinNotifications,
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
