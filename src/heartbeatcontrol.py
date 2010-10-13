import urllib
import time
class HeartBeatController(object):
    def __init__(self,ServerControl):
        self.LastFetch = 0
        self.FetchInterval = 60
        self.MaxClients = ServerControl.MaxClients
        self.Name = ServerControl.Name
        self.Public = ServerControl.Public
        self.Salt = ServerControl.Salt
        self.Port = ServerControl.Port
        self.Clients = 0
        self.ServerControl = ServerControl

    def IncreaseClients(self):
        self.Clients += 1
    def DecreaseClients(self):
        self.Clients -= 1


    def run(self):
        if self.LastFetch + self.FetchInterval < time.time():
            self.FetchUrl()
            self.LastFetch = time.time()
    def FetchUrl(self):
        try:
            Handle = urllib.urlopen("http://www.minecraft.net/heartbeat.jsp",urllib.urlencode({
                "port": self.Port,
                "users": self.Clients,
                "max": self.MaxClients,
                "name": self.Name,
                "public": self.Public,
                "version": 7,
                "salt": self.Salt,
            }))
            url = Handle.read().strip()
            print "Got URL:", url
            fHandle = open("url.txt","w")
            fHandle.write(url)
            fHandle.close()
        except:
            print "Error in heartbeat!"