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
import cStringIO
class OptiCraftPacket(object):
    def __init__(self,OpCode,data = ''):
        self.OpCode = OpCode
        self.data = cStringIO.StringIO()
        self.data.write(chr(OpCode))
        if data != '':
            self.data.write(data)
            self.data.seek(1) #Return to the position just after the opcode
            #This is a packet for reading.

        #Writing functions - Appends data in a format to the buffer.
        #Once again - these are NOT safe. Passing an argument of the incorrect type will throw exceptions.
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
        return struct.unpack("!B", self.data.read(1))[0]
    def GetString(self):
        return self.data.read(64).strip()
    def GetInt16(self):
        return struct.unpack("!h", self.data.read(2))[0]
    def GetInt32(self):
        return struct.unpack("!i", self.data.read(4))[0]
    def GetKBChunk(self):
        return self.data.read(1024)

    def GetOpCode(self):
        return self.OpCode
    def GetOutData(self):
        '''Returns the full packet - Opcode+Data which can then be sent over a socket'''
        return self.data.getvalue()