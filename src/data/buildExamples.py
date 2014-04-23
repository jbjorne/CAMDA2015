import csv, sqlite3
import re
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
dataPath = settings.DATA_PATH

def connect(con):
    if isinstance(con, basestring):
        con = sqlite3.connect(con)
    return con

def enumerateValues(con, table, column):
    con = connect(con)
    values = con.execute("SELECT DISTINCT " + column + " FROM " + table)
    return [x[0] for x in values]
    #result = con.execute()
    #print result

def getCancerClasses(specimenTypeValues):
    classes = {}
    for className in specimenTypeValues:
        classes[className] = 1 if "tumour" in className else -1
    return classes

def addFeature(value, features):
    if value not in features:
        features[value] = len(features)
        
def predefineFeatures(con, table, columns, features):
    con = connect(con)
    for column in columns:
        for value in enumerateValues(con, table, column):
            addFeature((column, value), features)
    return features

dbName = dataPath + "BRCA-US.sqlite"
con = sqlite3.connect(dbName)
print getCancerClasses(enumerateValues(con, "clinical", "specimen_type"))
features = predefineFeatures(con, "simple_somatic_mutation_open", 
                        ["chromosome", "mutation_type", "consequence_type", "gene_affected"], {})
print len(features)