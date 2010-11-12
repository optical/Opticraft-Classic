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
        self.Clients = 9
        self.ServerControl = ServerControl
        self.Running = True
        self.FirstHeartbeat = True

    def IncreaseClients(self):
        self.Clients += 1
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
        try:
            Handle = urllib.urlopen("http://minecraft.net/heartbeat.jsp",urllib.urlencode({
                "port": self.Port,
                "users": self.Clients,
                "max": self.MaxClients,
                "name": self.Name,
                "public": self.Public,
                "version": 7,
                "salt": self.Salt,
            }))
            url = Handle.read().strip()
            if self.FirstHeartbeat:
                self.FirstHeartbeat = False
                Console.Out("Heartbeat","Your url is: %s" %url)
                Console.Out("Heartbeat","This has been saved to url.txt")
            fHandle = open("url.txt","w")
            fHandle.write(url)
            fHandle.close()
            return True
        except:
            Console.Error("Heartbeat","Failed to register heartbeat, trying again...")
            return False