import csv, sqlite3
import re
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
dataPath = settings.DATA_PATH

def enumerateValues(dbName, table, column):
    con = sqlite3.connect(dbName)
    values = con.execute("SELECT DISTINCT " + column + " FROM " + table)
    return [x[0] for x in values]
    #result = con.execute()
    #print result

enumerateValues(dataPath + "BRCA-US.sqlite", "clinical", "specimen_type")
