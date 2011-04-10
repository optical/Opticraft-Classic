
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
class NonJsonType(object):
    pass

def MakeJsonSerializeable(Value):
    '''Helper for _AsJson
        Returns Value without any non json-serializeable types removed'''
    ValueType = type(Value)
    
    if ValueType == dict:
        NewDict = dict()
        for Key, DictValue in Value.iteritems():
            Key = MakeJsonSerializeable(Key)
            DictValue = MakeJsonSerializeable(DictValue)
            if DictValue is NonJsonType or Key is NonJsonType:
                continue
            NewDict[Key] = DictValue
        return NewDict
    
    elif ValueType == list or ValueType == set:
        NewList = list()
        for Item in Value:
            Item = MakeJsonSerializeable(Item)
            if Item is NonJsonType:
                continue
            NewList.append(Item)
        return NewList
    
    elif isinstance(Value, JsonSerializeableObject):
        return MakeJsonSerializeable(Value.__dict__)
    
    elif ValueType in JsonSerializeableObject._ValidJsonTypes:
        return Value
    else:
        return NonJsonType
        
class JsonSerializeableObject(object):
    '''Object which can more easily be encoded to and from json'''
    _ValidJsonTypes = frozenset([str, unicode, int, long, bool, dict, list, None, float])
    def _AsJson(self):
        '''This method returns a dictionary which can be encoded as json
        To do so it scans all attributes of the underlying object, adding
        key,values to a new dictionary if the key and value are valid json types.
        Lists and dictionary will be recursively reconstructed
        This object is intended to allow you to have reference types in your object,
        while still being easily serialized to json'''
        return MakeJsonSerializeable(self.__dict__)

    
    def FromJson(self, JsonDict):
        '''Sets the objects internal dictionary to the value of the JsonDict'''
        self.__dict__.update(JsonDict)
        self.OnJsonLoad()
        
    def OnJsonLoad(self):
        '''Called when the objects internal dictionary is loaded from JSON'''
        pass
        

class PluginDict(object):
    '''Dictionary wrapper which ensures that key is always of type string
    ...Optionally can also ensure all values can be encoded to a json type'''
    def __init__(self, NonJsonValues = True):
        self._dictionary = dict()
        #Nasty piece of code.
        self.NonJsonValues = NonJsonValues
        self.ValidJsonTypes = frozenset([str, int, long, bool, dict, list, float, JsonSerializeableObject])

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
                if isinstance(Value, ValidType) or Value is None:
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
    
    def __getattr__(self, Name):
        '''Try grab from our dictionary'''
        return self._dictionary.__getattribute__(Name)

    def AsJSON(self):
        assert(self.NonJsonValues == False)
        return json.dumps(MakeJsonSerializeable(self._dictionary))

    @staticmethod
    def FromJSON(JSON):
        NewDict = PluginDict()
        NewDict._dictionary = PluginDict.FromJSON(JSON)
        return NewDict

    @staticmethod
    def _FromJSON(JSON):
        '''returns a dictionary, not a plugindict'''
        TempDict = json.loads(JSON)
        y = UnicodeToStr(TempDict)
        return y


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
