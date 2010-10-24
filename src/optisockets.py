import socket
from select import select
from player import Player



class ListenSocket(object):
    def __init__(self,Host,Port):
        self.Socket = socket.socket()
        #This allows the server to restart instantly instead of waiting around
        self.Socket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
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

    def Terminate(self):
        self.Socket.close()
        del self.Socket

class SocketManager(object):
    def __init__(self,ServerControl):
        self.ListenSock = ListenSocket(ServerControl.Host,ServerControl.Port)
        self.PlayerSockets = list() #Used for reading
        self.ClosingSockets = list() #Sockets which need to be terminated.
        self.WriteList = [] #a list of player pointers who have packets ready to be sent.
        self.ServerControl = ServerControl

    def Terminate(self,Crash):
        '''Stop the listening socket'''
        self.ListenSock.Terminate()
        
    def run(self):
        '''Runs a cycle. Accept sockets from our listen socket, and then perform jobs
        ...on our Playersockets, such as reading and writing'''

        #Pop a socket off the stack
        PlayerSock, SockAddress = self.ListenSock.Accept()
        while PlayerSock != None and SockAddress != None:
            PlayerSock.setblocking(0)
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
            pPlayer = self.ServerControl.GetPlayerFromSocket(Socket)
            if pPlayer.IsWriteFlagged() == True:
                self.WriteList.remove(pPlayer)
            try:
                Socket.shutdown(socket.SHUT_RDWR)
                Socket.close()
            except:
                pass
            
        #Finished that. Now to see what our sockets are up to...
        if len(self.PlayerSockets) == 0:
            return #calling select() on windows with 3 empty lists results in an exception.
        rlist, wlist,xlist = select(self.PlayerSockets,self.WriteList,[],0.100) #100ms timeout
        for Socket in rlist:
            try:
                data = Socket.recv(4096)
            except socket.error, (error_no, error_msg):
                self._RemoveSocket(Socket)
                continue

            if len(data) > 0:
                #print "Recieved some data:", data
                pPlayer = self.ServerControl.GetPlayerFromSocket(Socket)
                pPlayer.PushRecvData(data)

        ToRemove = []
        for Socket in wlist:
            pPlayer = self.ServerControl.GetPlayerFromSocket(Socket)
            #pop data and send.
            ToSend = pPlayer.GetOutBuffer().getvalue()
            #Let us try send some data :XX
            try:
                result = Socket.send(ToSend)
            except:
                self._RemoveSocket(Socket)
                continue
            Buffer = pPlayer.GetOutBuffer()
            Buffer.truncate(0)
            NewData = ToSend[result:]
            if len(NewData) == 0:
                ToRemove.append(Socket)
            Buffer.write(NewData)

        
        while len(ToRemove) > 0:
            Socket = ToRemove.pop()
            self.WriteList.remove(Socket)
            pPlayer = self.ServerControl.GetPlayerFromSocket(Socket)
            pPlayer.SetWriteFlagged(False)

    def AddWriteablePlayer(self,pPlayer):
        self.WriteList.append(pPlayer.GetSocket())

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
            if pPlayer.GetWriteFlagged() == True:
                self.WriteList.remove(pPlayer.GetSocket())
                pPlayer.SetWriteFlagged(False)