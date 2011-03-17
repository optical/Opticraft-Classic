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

import struct
class OptiCraftPacket(object):
    __slots__ = ['OpCode', 'data', 'ReadPos']
    def __init__(self, OpCode, data = ''):
        self.OpCode = OpCode
        self.data = chr(OpCode) + data
        self.ReadPos = 0
        if data != '':
            self.ReadPos = 1 #Return to the position just after the opcode
            #This is a packet for reading.

        #Writing functions - Appends data in a format to the buffer.
        #Once again - these are NOT safe. Passing an argument of the incorrect type will throw exceptions.
    def WriteByte(self, data):
        self.data += struct.pack("B", data)
    def WriteString(self, data):
        self.data += (data + ((64 - len(data)) * ' '))
    def WriteInt16(self, data):
        self.data += struct.pack("!h", data)
    def WriteInt32(self, data):
        self.data += struct.pack("!i", data)
    def WriteKBChunk(self, data):
        self.data += (data + ((1024 - len(data)) * '\0'))

    #Getter functions for unpacking data.
    #These are NOT safe - Exceptions will be thrown if you read beyond the buffer length.
    def GetByte(self):
        Result = struct.unpack("!B", self.data[self.ReadPos:self.ReadPos + 1])[0]
        self.ReadPos += 1
        return Result
    def GetString(self):
        Result = self.data[self.ReadPos:self.ReadPos + 64].strip()
        self.ReadPos += 64
        return Result
    def GetInt16(self):
        Result = struct.unpack("!h", self.data[self.ReadPos:self.ReadPos + 2])[0]
        self.ReadPos += 2
        return Result
    def GetInt32(self):
        Result = struct.unpack("!i", self.data[self.ReadPos:self.ReadPos + 4])[0]
        self.ReadPos += 4
        return Result
    def GetKBChunk(self):
        Result = self.data[self.ReadPos:self.ReadPos + 1024]
        self.ReadPos += 1024
        return Result

    def GetOpCode(self):
        return self.OpCode
    def GetOutData(self):
        '''Returns the full packet - Opcode+Data which can then be sent over a socket'''
        return self.data
