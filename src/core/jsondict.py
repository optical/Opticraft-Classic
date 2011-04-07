
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
import json

def UnicodeToStr(obj):
    '''Terrible function for helping decode json'''
    if type(obj) == unicode:
        return str(obj)
    elif type(obj) == list:
        return [UnicodeToStr(x) for x in obj]
    elif type(obj) == dict:
        NewDict = {}
        for Key, Value in obj.iteritems():
            Key = UnicodeToStr(Key)
            Value = UnicodeToStr(Value)
            NewDict[Key] = Value
            return NewDict
        else:
            return obj

class JsonSerializeableObject(object):
    '''Object which can more easily be encoded to and from json'''
    _ValidJsonTypes = frozenset([str, int, long, bool, dict, list, None, float])
    def _AsJson(self):
        '''This method returns a dictionary which can be encoded as json
        To do so it scans all attributes of the underlying object, adding
        key,values to a new dictionary if the key and value are valid json types.
        It does not however ensure that those values will succeed at being encoded as JSON.
        Eg: a list with a non-json type will be returned, and an exception will be throwing
        during the encoding process.
        This object is intended to allow you to have reference types in your object,
        while still being easily serialized to json'''
        JsonDict = dict()
        for Key, Value in self.__dict__.iteritems():
            tKey = type(Key)
            tValue = type(Value)
            if tKey in JsonSerializeableObject._ValidJsonTypes and tValue in JsonSerializeableObject._ValidJsonTypes:
                JsonDict[Key] = Value
        return JsonDict
    
    def FromJson(self, JsonDict):
        self.__dict__ = JsonDict
        

class PluginDict(object):
    '''Dictionary wrapper which ensures that key is always of type string
    ...Optionally can also ensure all values can be encoded to a json type'''
    def __init__(self, NonJsonValues = True):
        self._dictionary = dict()
        #Nasty piece of code.
        self.NonJsonValues = NonJsonValues
        self.ValidJsonTypes = frozenset([str, int, long, bool, dict, list, None, float, JsonSerializeableObject])

    def __getitem__(self, Key):
        if type(Key) != str:
            raise ValueError("Data key must be a string")
        return self._dictionary[Key]

    def __setitem__(self, Key, Value):
        if type(Key) != str:
            raise ValueError("Data key must be a string")
        if self.NonJsonValues == False:
            Valid = False
            for ValidType in self.ValidJsonTypes:
                if isinstance(Value, ValidType):
                    Valid = True
                    break
            if not Valid:
                raise ValueError("Values must be json encodeable")
        if type(Value) != JsonSerializeableObject:
            self._dictionary[Key] = Value
        else:
            self._dictionary[Key] = Value._AsJson()
            
    def __delitem__(self, Key):
        del self._dictionary[Key]

    def __contains__(self, Value):
        return Value in self._dictionary
    def __iter__(self):
        return self._dictionary.__iter__()
    def __reversed__(self):
        return self._dictionary.__reversed__()
    def __len__(self):
        return self._dictionary.__len__()
    def get(self, Key, Default):
        return self._dictionary.get(Key, Default)

    def AsJSON(self):
        assert(self.NonJsonValues == False)
        return json.dumps(self._dictionary, ensure_ascii = True)

    @staticmethod
    def FromJSON(JSON):
        NewDict = PluginDict()
        NewDict._dictionary = PluginDict.FromJSON(JSON)
        return NewDict

    @staticmethod
    def _FromJSON(JSON):
        '''returns a dictionary, not a plugindict'''
        TempDict = json.loads(JSON)
        return UnicodeToStr(TempDict)


class JSONDict(PluginDict):
    '''Dictionary in which keys have to be a string, and values of any json
    ...serializeable type, including subclasses of JsonSerializeableObject'''
    def __init__(self):
        PluginDict.__init__(self, NonJsonValues = False)

    @staticmethod
    def FromJSON(JSON):
        NewDict = JSONDict()
        NewDict._dictionary = PluginDict._FromJSON(JSON)
        return NewDict
