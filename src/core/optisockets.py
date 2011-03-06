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

import socket
import errno
from select import select
from core.player import Player
from core.opticraftpacket import OptiCraftPacket
from core.console import *

class ListenSocket(object):
    def __init__(self, Host, Port):
        self.Socket = socket.socket()
        #This allows the server to restart instantly instead of waiting around
        self.Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.port = Port
        #Bind our socket to an interface
        try:
            self.Socket.bind((Host, Port))
            self.Socket.listen(5)
            self.Socket.setblocking(0)
        except:
            Console.Error("ListenSocket", "Critical error - could not bind socket to port %d on interface \"%s\"" % (Port, Host))
            exit(1)

    def Accept(self):
        try:
            return self.Socket.accept()
        except socket.error, (error_no, error_msg):
            if error_no == errno.EWOULDBLOCK:
                return None, None
            else:
                #Critical error
                raise socket.error

    def Terminate(self):
        self.Socket.close()
        del self.Socket

class SocketManager(object):
    def __init__(self, ServerControl):
        self.ListenSock = ListenSocket(ServerControl.Host, ServerControl.Port)
        self.PlayerSockets = list() #Used for reading
        self.ClosingSockets = set() #Sockets which need to be terminated.
        self.ClosingPlayers = dict()
        self.ServerControl = ServerControl

    def Terminate(self, Crash):
        '''Stop the listening socket'''
        self.ListenSock.Terminate()
        
    def Run(self):
        '''Runs a cycle. Accept sockets from our listen socket, and then perform jobs
        ...on our Playersockets, such as reading and writing'''

        #Pop a socket off the stack
        PlayerSock, SockAddress = self.ListenSock.Accept()
        while PlayerSock != None and SockAddress != None:
            PlayerSock.setblocking(0)
            #This enables socket buffering through the nagle algorithmn
            # - http://en.wikipedia.org/wiki/Nagle's_algorithm
            if self.ServerControl.LowLatencyMode == False:
                PlayerSock.setsockopt(0x06, socket.TCP_NODELAY, 0)
            self.PlayerSockets.append(PlayerSock)
            pPlayer = Player(PlayerSock, SockAddress, self.ServerControl)
            Result, Message = self.ServerControl.AttemptAddPlayer(pPlayer)
            if Result == False:
                #Server is full
                try:
                    self.PlayerSockets.remove(PlayerSock)
                    try:
                        Packet = OptiCraftPacket(SMSG_DISCONNECT)
                        Packet.WriteString(Message)
                        PlayerSock.send(Packet.GetOutData())
                    except:
                        pass
                    PlayerSock.close()
                except:
                    pass

            PlayerSock, SockAddress = self.ListenSock.Accept()

        #Shutdown any sockets we need to.
        if len(self.ClosingSockets) > 0:
            #Send any last packets to the client. This allows us to show them the kick message
            WriteableSockets = select([], self.ClosingSockets, [], 0.01)
            WriteableSockets = WriteableSockets[1]
            for wSocket in WriteableSockets:
                pPlayer = self.ClosingPlayers[wSocket]
                try:
                    wSocket.send(pPlayer.GetOutBuffer().getvalue())
                except:
                    pass

            while len(self.ClosingSockets) > 0:
                Socket = self.ClosingSockets.pop()
                self.PlayerSockets.remove(Socket)
                del self.ClosingPlayers[Socket]
                try:
                    Socket.shutdown(socket.SHUT_RDWR)
                    Socket.close()
                except:
                    pass
            
        #Finished that. Now to see what our sockets are up to...
        if len(self.PlayerSockets) == 0:
            return #calling select() on windows with 3 empty lists results in an exception.
        rlist, wlist, xlist = select(self.PlayerSockets, self.PlayerSockets, [], 0.100) #100ms timeout
        for Socket in rlist:
            try:
                data = Socket.recv(4096)
            except socket.error, (error_no, error_msg):
                if error_no != errno.EWOULDBLOCK:
                    if Socket in wlist:
                        wlist.remove(Socket)
                    self._RemoveSocket(Socket)
                continue

            if len(data) > 0:
                pPlayer = self.ServerControl.GetPlayerFromSocket(Socket)
                pPlayer.PushRecvData(data)
            else:
                #a recv call which returns nothing usually means a dead socket
                if Socket in wlist:
                    wlist.remove(Socket)
                self._RemoveSocket(Socket)
                continue

        for Socket in wlist:
            pPlayer = self.ServerControl.GetPlayerFromSocket(Socket)
            #pop data and send.
            ToSend = pPlayer.GetOutBuffer().getvalue()
            if len(ToSend) == 0:
                continue
            #Let us try send some data
            try:
                result = Socket.send(ToSend)
            except socket.error, (error_no, error_msg):
                if error_no != errno.EWOULDBLOCK:
                    self._RemoveSocket(Socket)
                continue
            Buffer = pPlayer.GetOutBuffer()
            Buffer.truncate(0)
            Buffer.write(ToSend[result:])

    def CloseSocket(self, Socket):
        self.ClosingSockets.add(Socket)
        self.ClosingPlayers[Socket] = self.ServerControl.GetPlayerFromSocket(Socket)

    def _RemoveSocket(self, Socket):
        #this function can be called twice in a row.
        #This occurs when the socket is returned in both the rlist and wlist
        #... after the select() is called, and both the read() and write()
        #... functions consequently fail.
        if Socket in self.PlayerSockets:
            self.PlayerSockets.remove(Socket)
            pPlayer = self.ServerControl.GetPlayerFromSocket(Socket)
            self.ServerControl.RemovePlayer(pPlayer)
            try:
                Socket.close()
            except:
                pass
