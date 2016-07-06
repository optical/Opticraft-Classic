class AsynchronousQueryResult(object):
    '''Used to store data about the result of the query on the world database'''
    def __init__(self, CallbackFunction, kwArgs, Results, Exception):
        self.CallbackFunction = CallbackFunction
        self.kwArgs = kwArgs
        self.IsException = Exception
        self.Results = Results
    def Callback(self):
        self.CallbackFunction(self.Results, self.kwArgs, self.IsException)

'''CallbackFunction has the header below'''
#def ExampleCallbackFunction(list Results, dict kwArgs, bool isException)
