# To change this template, choose Tools | Templates
# and open the template in the editor.
import time
import socket
from select import select
from player import Player



class ListenSocket(object):
    def __init__(self,Host,Port):
        self.Socket = socket.socket()
        self.port = Port
        #Temporary hack - REWRITE ME
        self.NewPlayers = list()
        #Bind our socket to an interface
        try:
            self.Socket.bind((Host,Port))
            self.Socket.listen(5)
            self.Socket.setblocking(0)
        except:
            print "Critical error - could not bind socket to port %d on interface \"%s\"" %(Port,Host)
            exit(1)

    def Accept(self):
        try:
            return self.Socket.accept()
        except:
            return None, None


class SocketManager(object):
    def __init__(self,ServerControl):
        self.ListenSock = ListenSocket(ServerControl.Host,ServerControl.Port)
        self.PlayerSockets = list() #Used for reading
        self.ClosingSockets = list() #Sockets which need to be terminated.
        self.WriteJobs = set() #a set of player pointers who have packets ready to be sent.
        self.ServerControl = ServerControl

    def run(self):
        '''Runs a cycle. Accept sockets from our listen socket, and then perform jobs
        ...on our Playersockets, such as reading and writing'''

        #Pop a socket off the stack
        PlayerSock, SockAddress = self.ListenSock.Accept()
        while PlayerSock != None and SockAddress != None:
            self.PlayerSockets.append(PlayerSock)
            pPlayer = Player(PlayerSock,SockAddress,self.ServerControl)
            result = self.ServerControl.AttemptAddPlayer(pPlayer)
            if result == False:
                #Server is full - Remove him next cycle.
                pPlayer.Disconnect()

            PlayerSock, SockAddress = self.ListenSock.Accept()

        #Shutdown any sockets we need to.
        while len(self.ClosingSockets) > 0:
            Socket = self.ClosingSockets.pop()
            self.PlayerSockets.remove(Socket)
            #TODO: Wrap this in try blocks - Once i know what errors can occur
            Socket.shutdown(socket.SHUT_RDWR)
            Socket.close()
            
        #Finished that. Now to see what our sockets are up to...
        if len(self.PlayerSockets) == 0:
            return #calling select() on windows with 3 empty lists results in an exception.
        rlist, wlist,xlist = select(self.PlayerSockets,self.PlayerSockets,[],0.05) #50ms timeout

        for Socket in rlist:
            try:
                data = Socket.recv(4096)
            except socket.error, (error_no, error_msg):
                if error_no == 10054 or error_no == 10053: #They closed the connection...
                    self._RemoveSocket(Socket)
                    continue
                else: #An error i haven't accounted for occured - o shit.
                    print "Critical Error! id:", error_no, "Message:", error_msg
                    exit(1)
            if len(data) > 0:
                #print "Recieved some data:", data
                pPlayer = self.ServerControl.GetPlayerFromSocket(Socket)
                pPlayer.Push_Recv_Data(data)

        ToRemove = []
        for Socket in wlist:
            pPlayer = self.ServerControl.GetPlayerFromSocket(Socket)
            if pPlayer in self.WriteJobs:
                #pop data and send. ERGH!
                ToSend = pPlayer.GetOutBuffer()
                size = len(ToSend)
                #Let us try send some data :XX
                try:
                    result = Socket.send(ToSend)
                except:
                    ToRemove.append(pPlayer)
                    self._RemoveSocket(Socket)
                    continue
                Remaining = size-result
                if Remaining > 0:
                    pPlayer.SetOutBuffer(ToSend[result:])
                else:
                    pPlayer.SetOutBuffer('')
                    ToRemove.append(pPlayer)
        
        for pPlayer in ToRemove:
            self.WriteJobs.remove(pPlayer)

    def AddWriteablePlayer(self,pPlayer):
        self.WriteJobs.add(pPlayer)

    def CloseSocket(self,Socket):
        self.ClosingSockets.append(Socket)

    def _RemoveSocket(self,Socket):
        #this function can be called twice in a row.
        #This occurs when the socket is returned in both the rlist and wlist
        #... after the select() is called, and both the read() and write()
        #... functions consequently fail.
        if Socket in self.PlayerSockets:
            self.PlayerSockets.remove(Socket)
            pPlayer = self.ServerControl.GetPlayerFromSocket(Socket)
            self.ServerControl.RemovePlayer(pPlayer)