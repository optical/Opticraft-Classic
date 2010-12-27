# Copyright (c) 2010, Jared Klopper
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

import urllib2
import urllib
import socket
import time
from threading import Thread
from console import *
class HeartBeatController(Thread):
    def __init__(self,ServerControl):
        Thread.__init__(self)
        self.daemon = True
        self.LastFetch = 0
        self.FetchInterval = 45
        self.MaxClients = ServerControl.MaxClients
        self.Name = ServerControl.Name
        self.Public = ServerControl.Public
        self.Salt = ServerControl.Salt
        self.Port = ServerControl.Port
        self.DumpStats = ServerControl.DumpStats
        self.LanMode = ServerControl.LanMode
        self.Peak = 0
        self.Clients = 0
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

    def _RegisterHeartbeat(self,Data):
        Connection = socket.socket()
        Connection.connect(("www.minecraft.net",80))
        Connection.send("GET /heartbeat.jsp?%s HTTP/1.1\r\n" %urllib.urlencode(Data))
        Connection.send("Host: minecraft.net\r\n\r\n")
    def _InitialHeartbeat(self,Url):
        Handle = urllib2.urlopen(Url)
        Url = Handle.read().strip()
        self.FirstHeartbeat = False
        if self.LanMode == True:
            Url = "http://www.minecraft.net/play.jsp?ip=127.0.0.1&port=%d" %self.Port
        Console.Out("Heartbeat","Your url is: %s" %Url)
        Console.Out("Heartbeat","This has been saved to url.txt")
        fHandle = open("url.txt","w")
        fHandle.write(Url)
        fHandle.close()
        return True

    def FetchUrl(self):
        if self.DumpStats:
            try:
                fHandle = open("stats.txt","w")
                fHandle.write("%d\n%d\n%d\n%s\n%s\n%s" %(self.Port,self.Clients,self.MaxClients,self.Name,self.Public,self.Salt))
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
            url = 'http://www.minecraft.net/heartbeat.jsp?%s' %urllib.urlencode(data)
            try:
                self._InitialHeartbeat(url)
            except urllib2.URLError:
                Console.Error("Heartbeat","Failed to register heartbeat, trying again...")
                return False
        else:
            try:
                self._RegisterHeartbeat(data)
            except socket.error:
                return False
            else:
                return True