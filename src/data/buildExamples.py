import sqlite3
import os, sys
import json
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
dataPath = settings.DATA_PATH

def connect(con):
    if isinstance(con, basestring):
        con = sqlite3.connect(con)
        con.row_factory = sqlite3.Row
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

# def getExamples(dbName, sql, classColumn, featureColumns, classIds, featureIds):
#     con = connect(dbName)
#     con.row_factory = sqlite3.Row
#     classes = []
#     features = []
#     for row in con.execute(sql):
#         if classColumn != None:
#             classes.append(classIds[row[classColumn]])
#         featureVector = {}
#         for column in featureColumns:
#             value = row[column]
#             featureVector[featureIds[(column, value)]] = 1
#         features.append(featureVector)
#     return classes, features

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

def getExperiment(experiment):
    if isinstance(experiment, basestring):
        return getattr(settings, experiment)
    else:
        return experiment

def getId(name, dictionary):
    if name not in dictionary:
        dictionary[name] = len(dictionary)
    return dictionary[name]

def writeSVMLight(f, example, cls, features):
    f.write(str(cls) + " " + " ".join([str(key) + ":" + '{0:f}'.format(features[key]) for key in sorted(features.keys())]) + "\n")

def compileTemplate(template):
    if template[0] == "{" and template[-1] == "}":
        return eval("lambda con, example: \"" + template.replace("{","\" + ").replace("}"," + \"") + "\"")
    else:
        return eval("lambda con, example: con.execute(\"" + template.replace("{","\" + ").replace("}"," + \"") + "\")")

def getExamples(con, experiment, callback, callbackArgs):
    experiment = getExperiment(experiment).copy()
    for key in experiment:
        if isinstance(experiment[key], basestring):
            experiment[key] = compileTemplate(experiment[key])
        elif isinstance(experiment[key], list):
            experiment[key] = [compileTemplate(x) for x in experiment[key]]
    print "Compiled experiment"
    examples = [x for x in experiment["example"](con, None)]
    numExamples = len(examples)
    print "Examples", numExamples
    count = 1
    clsIds = {True:1, False:-1}
    featureIds = {}
#     clsRules = {}
#     for rule in re.search(r"\[(\w+)\]", experiment["class"]):
#         clsRules[rule] = 
    for example in examples:
        cls = getId(experiment["class"](con, example), clsIds)
        #print experiment["class"](con, example)
        if count % 10 == 0:
            print "Processing example", example, cls, str(count) + "/" + str(numExamples)
        features = {}
        for featureGroup in experiment.get("features", []):
            for feature in featureGroup(con, example):
                features[getId(feature[0], featureIds)] = feature[1]
        if callback != None:
            callback(example=example, cls=cls, features=features, **callbackArgs)
        count += 1

# def getExamples2(con, experiment):
#     experiment = getExperiment("TEST_EXPERIMENT_COMPLETE")
#     example = None
#     cls = None
#     clsIds = {}
#     featureIds = {}
#     count = 1
#     for row in con.execute(experiment["all"]):
#         if row[0] != example:
#             example = row[0]
#             cls = clsIds.setdefault(row[1], len(clsIds))
#             features = {}
#             if count % 10 == 0:
#                 print "Processing example", example, str(count)
#             count += 1
#         #features[featureIds.setdefault(row[2], len(featureIds))] = row[3]
        

#dbPath = os.path.join(settings.DATA_PATH, settings.DB_NAME)        

# dbName = dataPath + "BRCA-US.sqlite"
# con = sqlite3.connect(dbName)
# classIds = getCancerClassIds(enumerateValues(con, "clinicalsample", "analyzed_sample_type"))
# featureColumns = ["chromosome", "mutation_type", "consequence_type"]
# featureIds = predefineFeatureIds(con, "simple_somatic_mutation_open", featureColumns)
# print "Class IDs:", json.dumps({str(k):v for k,v in classIds.items()})
# print "Feature IDs:", json.dumps({str(k):v for k,v in featureIds.items()})
# X, y = getExamples(dbName, "SELECT * FROM clinicalsample NATURAL JOIN simple_somatic_mutation_open LIMIT 15;", "analyzed_sample_type", featureColumns, classIds, featureIds)
# print X
# print y
# print expandVectors(y, featureIds)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Import ICGC data')
    parser.add_argument('-d','--directory', default=settings.DATA_PATH)
    parser.add_argument('-o','--output', default=None)
    parser.add_argument('-e','--experiment', help='', default=None)
    parser.add_argument('-b','--database', help='Database location', default=None)
    options = parser.parse_args()
    
#     outFile = None
    writer = None
    writerArgs = None
    if options.output != None:
        if not os.path.exists(os.path.dirname(options.output)):
            os.makedirs(os.path.dirname(options.output))
        outFile = open(options.output, "wt")
        writer = writeSVMLight
        writerArgs = {"f":outFile}
    
    con = connect(options.database)
    getExamples(con, options.experiment, writer, writerArgs)
    #getExamples2(con, options.experiment)
    
    if outFile != None:
        outFile.close()