import struct
import cStringIO
class OptiCraftPacket(object):
    def __init__(self,OpCode,data = ''):
        self.ReadPos = 1
        self.OpCode = OpCode
        self.data = cStringIO.StringIO()
        self.data.write(chr(OpCode))
        if data != '':
            self.data.write(data)
            self.data.seek(1) #Return to the position just after the opcode
            #This is a packet for reading.

        #Writing functions - Appends data in a format to the buffer.
        #Once again - these are NOT safe. Passing an argument of the incorrect type will mess up the
        #...Write buffer positions, or throwing exceptions.
    def WriteByte(self,data):
        self.data.write(struct.pack("B",data))
    def WriteString(self,data):
        self.data.write((data + ((64 - len(data)) *' ')))
    def WriteInt16(self,data):
       self.data.write(struct.pack("!h", data))
    def WriteInt32(self,data):
        self.data.write(struct.pack("!i", data))
    def WriteKBChunk(self,data):
       self.data.write((data + ((1024 - len(data)) *'\0')))

    #Getter functions for unpacking data.
    #These are NOT safe - Exceptions will be thrown if you read beyond the buffer length.
    def GetByte(self):
        self.ReadPos += 1
        return struct.unpack("!B", self.data.read(1))[0]
    def GetString(self):
        self.ReadPos += 64
        return self.data.read(64).strip()
    def GetInt16(self):
        self.ReadPos += 2
        return struct.unpack("!h", self.data.read(2))[0]
    def GetInt32(self):
        self.ReadPos += 4
        return struct.unpack("!i", self.data.read(4))[0]
    def GetKBChunk(self):
        self.ReadPos += 1024
        return self.data.read(1024)

    def GetOpCode(self):
        return self.OpCode
    def GetOutData(self):
        '''Returns the full packet - Opcode+Data which can be then be sent over a socket'''
        return self.data.getvalue()