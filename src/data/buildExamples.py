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

def getCancerClasses(specimenTypeValues):
    classes = {}
    for className in specimenTypeValues:
        classes[className] = 1 if "tumour" in className else -1
    return classes

dbName = dataPath + "BRCA-US.sqlite"
print getCancerClasses(enumerateValues(dbName, "clinical", "specimen_type"))
