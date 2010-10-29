'''Zone system for opticraft maps'''
from configreader import ConfigReader
from constants import *
import os.path
import random
class Zone(object):
    '''Zones are cuboid sections of the map with a height value tacked on'''
    def __init__(self,FileName):
        self.Name = ''
        self.Map = ''
        self.FileName = FileName #This is usually in format: Name-Randomnumber.ini
        self.MinRank = ''
        self.MinRankNumeric = 0
        self.Owner = ''
        self.X1 = 0 #Lower of the two X values
        self.X2 = 0
        self.Y1 = 0 #Lower of the two Y values
        self.Y2 = 0
        self.Z1 = 0 #Lower of the two Z values
        self.Z2 = 0
        self.Builders = set()
        self.ConfigValues = None
        self.Load()

    def IsInZone(self,X,Y,Z):
        if X >= self.X1 and X <= self.X2 and Y >= self.Y1 and Y <= self.Y2 and Z >= self.Z1 and Z <= self.Z2:
            return True
        else:
            return False
    def CanBuild(self,pPlayer):
        Name = pPlayer.GetName().lower()
        if Name == self.Owner or Name in self.Builders:
            return True
        elif RankToLevel[pPlayer.GetRank()] >= self.MinRankNumeric:
            return True
        else:
            return False
        
    def Load(self):
        self.ConfigValues = ConfigReader()
        self.ConfigValues.read("Zones/%s" %self.FileName)
        self.Name = self.ConfigValues.get("Info","Name")
        self.Map = self.ConfigValues.get("Info","Map")
        self.X1 = int(self.ConfigValues.get("Info","X1"))
        self.X2 = int(self.ConfigValues.get("Info","X2"))
        self.Y1 = int(self.ConfigValues.get("Info","Y1"))
        self.Y2 = int(self.ConfigValues.get("Info","Y2"))
        self.Z1 = int(self.ConfigValues.get("Info","Z1"))
        self.Z2 = int(self.ConfigValues.get("Info","Z2"))
        self.Owner = self.ConfigValues.get("Info","Owner")
        self.MinRank = self.ConfigValues.get("Info","Minrank")
        self.MinRankNumeric = RankToLevel[self.MinRank]
        for Name,junk in self.ConfigValues.items("Builders"):
            self.Builders.add(Name)
        

    @staticmethod
    def Create(Name,X1,X2,Y1,Y2,Z1,Z2,Height,Owner,Map):
        while True:
            FileName = "%s-%d.ini" %(Name, random.randint(100,999))
            if os.path.isfile("Zones/%s" %FileName) == False:
                break #File doesn't exist. Make it
        fHandle = open("Zones/%s" %FileName,"w")
        fHandle.close()
        ConfigValues = ConfigReader()
        ConfigValues.read("Zones/%s.ini" %FileName)
        ConfigValues.add_section("Info")
        ConfigValues.set("Info","Name",Name)
        ConfigValues.set("Info","Map",Map)
        ConfigValues.set("Info","X1",min(X1,X2))
        ConfigValues.set("Info","X2",max(X1,X2))
        ConfigValues.set("Info","Y1",min(Y1,Y2))
        ConfigValues.set("Info","Y2",max(Y1,Y2))
        ConfigValues.set("Info","Z1",min(Z1,Z2))
        ConfigValues.set("Info","Z2",min(Z1,Z2)+Height)
        ConfigValues.set("Info","Owner",Owner.lower())
        ConfigValues.set("Info","Minrank",'b')
        ConfigValues.add_section("Builders")
        fHandle = open("Zones/%s" %FileName,"w")
        ConfigValues.write(fHandle)
        fHandle.close()
        return FileName

    def AddBuilder(self,Username):
        self.Builders.add(Username.lower())
        self.ConfigValues.set("Builders",Username.lower(),"1")
        self.Save()

    def Save(self):
        fHandle = open("Zones/%s" %self.FileName,"w")
        self.ConfigValues.write(fHandle)
        fHandle.close()

    def Delete(self):
        '''Deletes the zone from disk'''
        os.remove("Zones/%s" %self.FileName)
    def DelBuilder(self,Username):
        if Username.lower() in self.Builders:
            self.Builders.remove(Username.lower())
            self.ConfigValues.remove_option("Builders",Username.lower())
            self.Save()
    def ChangeOwner(self,Owner):
        self.Owner = Owner.lower()
        self.ConfigValues.set("Info","Owner",Owner.lower())
        self.Save()

    def SetMinRank(self,Rank):
        self.MinRank = Rank
        self.MinRankNumeric = RankToLevel[self.MinRank]
        self.ConfigValues.set("Info","Minrank",Rank)
        self.Save()