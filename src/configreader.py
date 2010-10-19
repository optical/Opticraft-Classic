from ConfigParser import RawConfigParser

class ConfigReader(RawConfigParser):
    def __init__(self):
        RawConfigParser.__init__(self)

    def GetValue(self,Section,Option,Default=''):
        if self.has_option(Section,Option):
            return self.get(Section,Option)
        else:
            return Default