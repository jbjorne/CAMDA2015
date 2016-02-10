import os
import math
import sqlite3

class Database():
    def __init__(self, filePath=None):
        self._databasePath = filePath
        self._connection = None
        
    def getConnection(self):
        if self._connection == None:
            if not os.path.exists(self.databasePath):
                raise Exception("No database at " + str(self._databasePath))
            print "Using database at", self._databasePath
            self._connection = sqlite3.connect(self._databasePath) # @UndefinedVariable
            self._connection.row_factory = sqlite3.Row # @UndefinedVariable
            self._connection.create_function("log", 1, math.log)
        return self._connection
    
    def getPath(self):
        return self._databasePath