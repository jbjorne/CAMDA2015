import sqlite3
import os, sys
import json

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

def getCancerClassIds(specimenTypeValues):
    classes = {}
    for className in specimenTypeValues:
        classes[className] = 1 if "tumour" in className else -1
    return classes

def addFeatureId(value, featureIds):
    if value not in featureIds:
        featureIds[value] = len(featureIds)
        
def predefineFeatureIds(con, table, columns, featureIds=None):
    con = connect(con)
    if featureIds == None:
        featureIds = {}
    for column in columns:
        for value in enumerateValues(con, table, column):
            addFeatureId((column, value), featureIds)
    return featureIds

def getExamples(dbName, sql, classColumn, featureColumns, classIds, featureIds):
    con = connect(dbName)
    con.row_factory = sqlite3.Row
    classes = []
    features = []
    for row in con.execute(sql):
        classes.append(classIds[row[classColumn]])
        featureVector = {}
        for column in featureColumns:
            value = row[column]
            featureVector[featureIds[(column, value)]] = 1
        features.append(featureVector)
    return classes, features

def expandVectors(features, featureIds):
    maxIndex = max(featureIds.values())
    arrays = []
    for vector in features:
        array = []
        for i in range(maxIndex):
            if i in vector:
                array.append(vector[i])
            else:
                array.append(0)
        arrays.append(array)
    return arrays
        

dbName = dataPath + "BRCA-US.sqlite"
con = sqlite3.connect(dbName)
classIds = getCancerClassIds(enumerateValues(con, "clinicalsample", "analyzed_sample_type"))
featureColumns = ["chromosome", "mutation_type", "consequence_type"]
featureIds = predefineFeatureIds(con, "simple_somatic_mutation_open", featureColumns)
print "Class IDs:", json.dumps({str(k):v for k,v in classIds.items()})
print "Feature IDs:", json.dumps({str(k):v for k,v in featureIds.items()})
X, y = getExamples(dbName, "SELECT * FROM clinicalsample NATURAL JOIN simple_somatic_mutation_open LIMIT 15;", "analyzed_sample_type", featureColumns, classIds, featureIds)
print X
print y
print expandVectors(y, featureIds)