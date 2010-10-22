import urllib
import time
from threading import Thread

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

    def IncreaseClients(self):
        self.Clients += 1
    def DecreaseClients(self):
        self.Clients -= 1


    def run(self):
        while self.Running:
            if self.LastFetch + self.FetchInterval < time.time():
                start = time.time()
                Result = self.FetchUrl()
                if Result:
                    #Sleep for FetchInterval seconds minus the time it took to perform the heartbeat.
                    self.LastFetch = time.time()
                    print "Sleeping for %f ms" %(self.FetchInterval - (self.LastFetch-start))
                    time.sleep(self.FetchInterval - (time.time()-start) * 1000)
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
            return True
        except:
            print "Error in heartbeat!"
            return False