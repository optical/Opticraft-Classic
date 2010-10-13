import struct
class OptiCraftPacket(object):
    def __init__(self,OpCode,data = ''):
        self.ReadPos = 0
        self.WritePos = 0
        self.OpCode = OpCode
        self.data = data #TODO: Replace this with an effecient mutable data type (Such as an array)

        #Writing functions - Appends data in a format to the buffer.
        #Once again - these are NOT safe. Passing an argument of the incorrect type will mess up the
        #...Write buffer positions, or throwing exceptions.
    def WriteByte(self,data):
        self.data += struct.pack("B",data)
        self.WritePos += 1
    def WriteString(self,data):
        self.data += (data + ((64 - len(data)) *' '))
        self.WritePos += 64
    def WriteInt16(self,data):
        self.data += struct.pack("!h", data)
        self.WritePos += 2
    def WriteInt32(self,data):
        self.data += struct.pack("!i", data)
        self.WritePos += 4
    def WriteKBChunk(self,data):
        self.data += (data + ((1024 - len(data)) *'\0'))
        self.WritePos += 1024

    #Getter functions for unpacking data.
    #These are NOT safe - Exceptions will be thrown if you read beyond the buffer length.
    def GetByte(self):
        Result = struct.unpack("!B", self.data[self.ReadPos])[0]
        self.ReadPos += 1
        return Result
    def GetString(self):
        Result = self.data[self.ReadPos:self.ReadPos+64].strip()
        self.ReadPos += 64
        return Result
    def GetInt16(self):
        Result = struct.unpack("!h", self.data[self.ReadPos:self.ReadPos+2])
        self.ReadPos += 2
        return Result[0]
    def GetInt32(self):
        Result = struct.unpack("!i", self.data[self.ReadPos:self.ReadPos+4])
        self.ReadPos += 4
        return Result[0]
    def GetKBChunk(self):
        Result = self.data[self.ReadPos:self.ReadPos+1024]
        self.ReadPos += 1024
        return Result
    def GetOpCode(self):
        return self.OpCode
    def GetOutData(self):
        '''Returns the full packet - Opcode+Data which can be then be sent over a socket'''
        return chr(self.OpCode) + self.data