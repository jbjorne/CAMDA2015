import sqlite3
import os, sys
from collections import OrderedDict
import json
import time
from template import *
from example import *

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
dataPath = settings.DATA_PATH

def connect(con):
    if isinstance(con, basestring):
        con = sqlite3.connect(con)
        con.row_factory = sqlite3.Row
    return con

def getExperiment(experiment):
    if isinstance(experiment, basestring):
        return getattr(settings, experiment)
    else:
        return experiment

def getId(name, dictionary):
    if name not in dictionary:
        dictionary[name] = len(dictionary)
    return dictionary[name]

def getExamples(con, experimentName, callback, callbackArgs, metaDataFileName=None, options=None):
    con = connect(con)
    template = getExperiment(experimentName).copy()
    options = updateTemplateOptions(template, options)
    print "Template:", experimentName
    print json.dumps(template, indent=4)
    compiled = template.copy()
    compiled["example"] = compileTemplate(compiled["example"], ["con", "options"], "example")
    compiled["class"] = compileTemplate(compiled["class"], ["con", "example", "options"], "class")
    compiled["features"] = compileTemplate(compiled["features"], ["con", "example", "options"], "features")
    compiled["meta"] = compileTemplate(compiled["meta"], ["con", "example", "options", "cls", "features"], "meta")
    print "Compiled experiment"
    examples = [x for x in compiled["example"](con, options)]
    numExamples = len(examples)
    print "Examples", numExamples
    count = 1
    clsIds = compiled.get("classIds", {})
    featureIds = {}
#     clsRules = {}
#     for rule in re.search(r"\[(\w+)\]", experiment["class"]):
#         clsRules[rule] = 
    meta = []
    featureGroups = compiled.get("features", [])
    for example in examples:
        cls = getId(compiled["class"](con, example, options), clsIds)
        #print experiment["class"](con, example)
        #if count % 10 == 0:
        print "Processing example", example, cls, str(count) + "/" + str(numExamples)
        features = {}
        for featureGroup in featureGroups:
            for feature in featureGroup(con, example, options):
                #print example, options, feature
                features[getId(feature[0], featureIds)] = feature[1]
        if len(features) == 0:
            print "WARNING: example has no features"
        if callback != None:
            callback(example=example, cls=cls, features=features, **callbackArgs)
        if "meta" in compiled:
            meta.append(compiled["meta"](con, example, options, cls, features))
        count += 1
    saveMetaData(metaDataFileName, template, experimentName, clsIds, featureIds, meta)
    return featureIds

def saveMetaData(metaDataFileName, template, experimentName, clsIds, featureIds, meta):
    if (metaDataFileName != None):
        f = open(metaDataFileName, "wt")
        #template = getExperiment(experimentName).copy()
        experimentMeta = {}
        experimentMeta["name"] = experimentName
        experimentMeta["time"] = time.strftime("%c")
        experimentMeta["dbFile"] = [x["file"] for x in con.execute("PRAGMA database_list;")][0]
        experimentMeta["dbModified"] = time.strftime("%c", time.localtime(os.path.getmtime(experimentMeta["dbFile"])))
        output = OrderedDict((("experiment",experimentMeta), ("template",template), ("class",clsIds), ("feature",featureIds)))
        if len(meta) > 0:
            output["meta"] = meta
        json.dump(output, f, indent=4)#, separators=(',\n', ':'))
        f.close()

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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Build examples from ICGC data')
    parser.add_argument('-x','--features', help='Output file for feature vectors (X)', default=None)
    parser.add_argument('-y','--labels', help='Output file for class labels (Y)', default=None)
    parser.add_argument('-w','--writer', help='Output writer function (optional)', default='writeNumpyText')
    parser.add_argument('-m','--meta', help='Metadata output file name (optional)', default=None)
    parser.add_argument('-e','--experiment', help='Experiment template', default=None)
    parser.add_argument('-p','--options', help='Experiment template options', default=None)
    parser.add_argument('-b','--database', help='Database location', default=None)
    options = parser.parse_args()
    
    print options.database
    if not os.path.exists(options.database):
        raise Exception("No database at " + str(options.database))
    
#     outFile = None
    writer = None
    writerArgs = None
    opened = {}
    if options.features != None or options.labels != None:
        writer = eval(options.writer)
        writerArgs = {}
        for argName, filename in [("fX", options.features), ("fY", options.labels)]:
            if filename != None:
                parentDir = os.path.dirname(filename)
                if parentDir != None and not os.path.exists(parentDir):
                    os.makedirs(parentDir)
                filename = os.path.abspath(os.path.expanduser(filename))
                if filename not in opened:
                    opened[filename] = open(filename, "wt")
                writerArgs[argName] = opened[filename]
    
    if options.meta != None and not os.path.exists(os.path.dirname(options.meta)):
        os.makedirs(os.path.dirname(options.meta))
    
    con = connect(options.database)
    featureIds = getExamples(con, options.experiment, writer, writerArgs, options.meta, parseTemplateOptions(options.options))
    #getExamples2(con, options.experiment)
    
    for outFile in opened.values():
        outFile.close()
    if options.writer == "writeNumpyText" and options.features != None:
        padNumpyFeatureFile(options.features, len(featureIds))