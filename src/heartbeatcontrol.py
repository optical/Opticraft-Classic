import urllib2
import urllib
import time
from threading import Thread
from console import *
class HeartBeatController(Thread):
    def __init__(self,ServerControl):
        Thread.__init__(self)
        self.LastFetch = 0
        self.FetchInterval = 30
        self.MaxClients = ServerControl.MaxClients
        self.Name = ServerControl.Name
        self.Public = ServerControl.Public
        self.Salt = ServerControl.Salt
        self.Port = ServerControl.Port
        self.DumpStats = ServerControl.DumpStats
        self.LanMode = ServerControl.LanMode
        self.Peak = 0
        self.Clients = 9
        self.ServerControl = ServerControl
        self.Running = True
        self.FirstHeartbeat = True

    def IncreaseClients(self):
        self.Clients += 1
        if self.Clients > self.Peak:
            self.Peak = self.Clients
    def DecreaseClients(self):
        self.Clients -= 1


    def run(self):
        while self.Running:
            now = time.time()
            if self.LastFetch + self.FetchInterval < now:
                Result = self.FetchUrl()
                if Result:
                    #Sleep for FetchInterval seconds minus the time it took to perform the heartbeat.
                    self.LastFetch = time.time()
                    sleeptime = self.FetchInterval - (self.LastFetch-now)
                    if sleeptime > 0:
                        time.sleep(sleeptime)
                        
    def FetchUrl(self):
        if self.DumpStats:
            try:
                fHandle = open("stats.txt","w")
                fHandle.write("%d\n%d\n%d\n%s\n%s\n%s" %(self.Port,self.Clients,self.MaxClients,self.Name,self.Public,self.Salt))
                fHandle.close()
            except IOError:
                pass
        url = "http://www.minecraft.net/heartbeat.jsp"
        data = {
        "port": self.Port,
        "max": self.MaxClients,
        "name": self.Name,
        "public": self.Public,
        "version": 7,
        "salt": self.Salt,
        "users": self.Clients
        }
        url = '%s?%s' %(url,urllib.urlencode(data))
        try:
            Handle = urllib2.urlopen(url)
            if self.FirstHeartbeat:
                url = Handle.read().strip()
                self.FirstHeartbeat = False
                if self.LanMode == True:
                    url = "http://www.minecraft.net/play.jsp?ip=127.0.0.1&port=%d" %self.Port
                Console.Out("Heartbeat","Your url is: %s" %url)
                Console.Out("Heartbeat","This has been saved to url.txt")
                fHandle = open("url.txt","w")
                fHandle.write(url)
                fHandle.close()
            return True
        except urllib2.URLError:
            Console.Error("Heartbeat","Failed to register heartbeat, trying again...")
            return False