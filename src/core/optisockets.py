import socket
import errno
from select import select
from core.player import Player
from core.packet import PacketWriter
from core.console import *

class SocketBindFailException(Exception):
    pass
class ListenSocket(object):
    def __init__(self, Host, Port, BackLog = 120):
        self.Socket = socket.socket()
        #This allows the server to restart instantly instead of waiting around
        self.Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.port = Port
        #Bind our socket to an interface
        try:
            self.Socket.bind((Host, Port))
            self.Socket.listen(BackLog)
            self.Socket.setblocking(0)
        except:
            raise SocketBindFailException("Could not bind to host '%s' on port %d" % (Host, Port))

    def Accept(self):
        try:
            return self.Socket.accept()
        except socket.error, (error_no, error_msg):
            if error_no == errno.EWOULDBLOCK:
                return None, None
            else:
                #Critical error
                raise socket.error(error_no, error_msg)

    def Terminate(self):
        self.Socket.close()
        del self.Socket

class SocketManager(object):
    def __init__(self, ServerControl):
        self.ListenSockets = []
        assert(len(ServerControl.Port.split(',')) > 0)
        for Port in ServerControl.Port.split(','):
            #Undocumented feature: Opticraft supports listening on multiple ports
            try:
                ListenSock = ListenSocket(ServerControl.Host, int(Port))
                self.ListenSockets.append(ListenSock)
            except SocketBindFailException, e:
                Console.Error("ListenSocket", str(e))
                raise e
        self.PlayerSockets = list() #Used for reading
        self.ClosingSockets = set() #Sockets which need to be terminated.
        self.ClosingPlayers = dict()
        self.ServerControl = ServerControl
        self.RecievedBytes = 0
        self.SentBytes = 0

    def Terminate(self, Crash):
        '''Stop the listening sockets'''
        for ListenSock in self.ListenSockets:
            ListenSock.Terminate()
        
    def AcceptConnection(self):
        '''None blocking call. Returns Tuple of Socket, IP or None,None if would block'''
        for ListenSock in self.ListenSockets:
            PlayerSock, PlayerIP = ListenSock.Accept()
            if PlayerSock is not None:
                return PlayerSock, PlayerIP
            else:
                continue
        return None, None
        
    def Run(self):
        '''Runs a cycle. Accept sockets from our listen socket, and then perform jobs
        ...on our Playersockets, such as reading and writing'''

        #Pop a socket off the stack
        PlayerSock, SockAddress = self.AcceptConnection()
        while PlayerSock is not None and SockAddress is not None:
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
                        Packet = PacketWriter.MakeDisconnectPacket(Message)
                        PlayerSock.send(Packet.GetOutData())
                    except:
                        pass
                    PlayerSock.close()
                except:
                    pass

            PlayerSock, SockAddress = self.AcceptConnection()

        #Shutdown any sockets we need to.
        if len(self.ClosingSockets) > 0:
            #Send any last packets to the client. This allows us to show them the kick message
            WriteableSockets = select([], self.ClosingSockets, [], 0.01)
            WriteableSockets = WriteableSockets[1]
            for wSocket in WriteableSockets:
                pPlayer = self.ClosingPlayers[wSocket]
                try:
                    wSocket.send(''.join(pPlayer.OutBuffer))
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
                self.RecievedBytes += len(data)
            else:
                #a recv call which returns nothing usually means a dead socket
                if Socket in wlist:
                    wlist.remove(Socket)
                self._RemoveSocket(Socket)
                continue

        for Socket in wlist:
            pPlayer = self.ServerControl.GetPlayerFromSocket(Socket)
            #pop data and send.
            ToSend = ''.join(pPlayer.OutBuffer)
            if len(ToSend) == 0:
                continue
            #Let us try send some data
            try:
                result = Socket.send(ToSend)
            except socket.error, (error_no, error_msg):
                if error_no != errno.EWOULDBLOCK:
                    self._RemoveSocket(Socket)
                continue
            self.SentBytes += result
            pPlayer.OutBuffer = [ToSend[result:]]

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
