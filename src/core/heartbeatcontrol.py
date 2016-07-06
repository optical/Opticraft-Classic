import urllib2
import httplib
import urllib
import socket
import time
from threading import Thread
from core.console import *
class HeartBeatController(Thread):
    def __init__(self, ServerControl):
        Thread.__init__(self, name = "HeartBeat Thread")
        self.daemon = True
        self.LastFetch = 0
        self.FetchInterval = 45
        self.MaxClients = ServerControl.MaxClients
        self.Name = ServerControl.Name
        self.Public = ServerControl.Public
        if self.Public.isdigit():
            self.Public = "True" if self.Public == "1" else "False"
        if self.Public.lower() not in ["true", "false"]:
            self.Public = "true" 
        self.Salt = ServerControl.Salt
        self.Port = int(ServerControl.Port.split(",")[0])
        self.DumpStats = ServerControl.DumpStats
        self.LanMode = ServerControl.LanMode
        self.Peak = 0
        self.Clients = 0
        self.ServerControl = ServerControl
        self.Running = True
        self.FirstHeartbeat = True
        self.Connection = None

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
                    sleeptime = self.FetchInterval - (self.LastFetch - now)
                    if sleeptime > 0:
                        time.sleep(sleeptime)

    def _RegisterHeartbeat(self, Data):
        if self.Connection:
            self.Connection.close()
        self.Connection = socket.socket()
        self.Connection.connect(("www.minecraft.net", 80))
        self.Connection.send("GET /heartbeat.jsp?%s HTTP/1.1\r\nHost: minecraft.net\r\n\r\n" % urllib.urlencode(Data))

    def _InitialHeartbeat(self, Url):
        Handle = urllib2.urlopen(Url)
        Url = Handle.read().strip()
        self.FirstHeartbeat = False
        if self.LanMode == True:
            Url = "http://www.minecraft.net/play.jsp?ip=127.0.0.1&port=%d" % self.Port
        Console.Out("Heartbeat", "Your url is: %s" % Url)
        Console.Out("Heartbeat", "This has been saved to url.txt")
        with open("url.txt", "w") as fHandle:
            fHandle.write(Url)
        return True

    def FetchUrl(self):
        if self.DumpStats:
            try:
                fHandle = open("stats.txt", "w")
                fHandle.write("%d\n%d\n%d\n%s\n%s\n%s" % (self.Port, self.Clients, self.MaxClients, self.Name, self.Public, self.Salt))
                fHandle.close()
            except IOError:
                pass

        data = {
        "port": self.Port,
        "max": self.MaxClients,
        "name": self.Name,
        "public": self.Public,
        "version": 7,
        "salt": self.Salt,
        "users": self.Clients
        }
        if self.FirstHeartbeat:
            url = 'http://www.minecraft.net/heartbeat.jsp?%s' % urllib.urlencode(data)
            try:
                self._InitialHeartbeat(url)
            except httplib.BadStatusLine:
                return False
            except urllib2.URLError:
                return False
        else:
            try:
                self._RegisterHeartbeat(data)
            except socket.error, (error_no, error_msg):
                Console.Error("Heartbeat", "Failed to register heartbeat, trying again... (%s)" % (error_msg))
                return False
            else:
                return True
