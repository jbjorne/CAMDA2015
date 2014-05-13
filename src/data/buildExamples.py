"""
For building examples from the ICGC database.
"""
import sqlite3
import os, sys
from collections import OrderedDict
import json
import time
from template import *
from example import *
import itertools
import hidden
import math
import inspect
from numbers import Number

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
dataPath = settings.DATA_PATH

def connect(con):
    if isinstance(con, basestring):
        con = sqlite3.connect(con)
        con.row_factory = sqlite3.Row
        con.create_function("log", 1, math.log)
    for func in settings.SQLITE_FUNCTIONS: #functions:
        con.create_function(func.func_name,func.func_code.co_argcount,func)
    return con

def parseExperiment(experiment):
    if isinstance(experiment, basestring):
        return getattr(settings, experiment)
    else:
        return experiment

def getId(value, dictionary):
    if value not in dictionary:
        dictionary[value] = len(dictionary)
    return dictionary[value]

def getIdOrValue(value, dictionary=None):
    if dictionary != None:
        value = str(value)
        if value not in dictionary:
            dictionary[value] = len(dictionary)
        return dictionary[value]
    else:
        return value

def getExamples(con, experimentName, callback, callbackArgs, metaDataFileName=None, options=None, experimentMeta=None, hiddenRule="skip"):
    con = connect(con)
    template = parseExperiment(experimentName).copy()
    template = parseTemplateOptions(options, template)
    #con = connect(con, template.get("functions", None))
    #options = updateTemplateOptions(template, options)
    print "Template:", experimentName
    print json.dumps(template, indent=4)
    compiled, lambdaArgs = compileTemplate(template)
    print "Compiled experiment"
    examples = [dict(x) for x in compiled["example"](con=con, **lambdaArgs)]
    numHidden = hidden.setHiddenValues(examples, compiled)
    numExamples = len(examples)
    print "Examples " +  str(numExamples) + ", hidden " + str(numHidden)
    count = 0
    clsIds = compiled.get("classes", None)
    featureIds = {}
    meta = []
    featureGroups = compiled.get("features", [])
    for example in examples:
        count += 1
        if not hidden.getInclude(example, compiled.get("hidden", None), hiddenRule):
            continue
        #print experiment["class"](con, example)
        #if count % 10 == 0:
        print "Processing example", example,
        cls = getIdOrValue(compiled["label"](con=con, example=example, **lambdaArgs), clsIds)
        print cls, str(count) + "/" + str(numExamples)
        features = {}
        for featureGroup in featureGroups:
            for row in featureGroup(con=con, example=example, **lambdaArgs):
                for key, value in itertools.izip(*[iter(row)] * 2): # iterate over each consecutive key,value columns pair
                    if not isinstance(key, basestring):
                        raise Exception("Non-string feature key '" + str(key) + "' in feature group " + str(featureGroups.index(featureGroup)))
                    if not isinstance(value, Number):
                        raise Exception("Non-number feature value '" + str(value) + "' in feature group " + str(featureGroups.index(featureGroup)))
                    features[getId(key, featureIds)] = value
        if len(features) == 0:
            print "WARNING: example has no features"
        if callback != None:
            callback(example=example, cls=cls, features=features, **callbackArgs)
        if "meta" in compiled:
            meta.append(compiled["meta"](label=cls, features=features, example=example, **lambdaArgs))
    saveMetaData(metaDataFileName, con, template, experimentName, options, clsIds, featureIds, meta, experimentMeta)
    return featureIds

def saveMetaData(metaDataFileName, con, template, experimentName, experimentOptions, clsIds, featureIds, meta, experimentMeta):
    if (metaDataFileName != None):
        if not os.path.exists(os.path.dirname(metaDataFileName)):
            os.makedirs(os.path.dirname(metaDataFileName))
        f = open(metaDataFileName, "wt")
        #template = getExperiment(experimentName).copy()
        if experimentMeta == None:
            experimentMeta = {}
        experimentMeta["name"] = experimentName
        if experimentOptions != None:
            experimentMeta["options"] = experimentOptions
        experimentMeta["time"] = time.strftime("%c")
        experimentMeta["dbFile"] = [x["file"] for x in con.execute("PRAGMA database_list;")][0]
        experimentMeta["dbModified"] = time.strftime("%c", time.localtime(os.path.getmtime(experimentMeta["dbFile"])))
        if clsIds == None:
            clsIds = {}
        output = OrderedDict((("experiment",experimentMeta), ("template",template), ("classes",clsIds), ("features",featureIds)))
        if len(meta) > 0:
            output["meta"] = meta
        json.dump(output, f, indent=4)#, separators=(',\n', ':'))
        f.close()

def writeExamples(dbPath, experimentName, experimentOptions, hiddenRule, featureFilePath, labelFilePath, metaFilePath, writer=writeNumpyText):
    if not os.path.exists(dbPath):
        raise Exception("No database at " + str(dbPath))
    print "Using database at", dbPath
    con = connect(dbPath)
    writerArgs, opened = openOutputFiles(featureFilePath, labelFilePath, writer)
    experimentMeta = {"X":featureFilePath,"y":labelFilePath,"writer":writer.__name__}
    if "fY" not in writerArgs:
        del experimentMeta["y"]
    featureIds = getExamples(con, experimentName, writer, writerArgs, metaFilePath, experimentOptions, experimentMeta, hiddenRule)
    closeOutputFiles(opened, writer, featureFilePath, len(featureIds))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(parents=[exampleOptions], description='Build examples from ICGC data')
    parser.add_argument('-x','--features', help='Output file for feature vectors (X)', default=None)
    parser.add_argument('-y','--labels', help='Output file for class labels (Y)', default=None)
    parser.add_argument('-m','--meta', help='Metadata output file name (optional)', default=None)
    options = parser.parse_args()
    
    writeExamples(dbPath=options.database, experimentName=options.experiment, experimentOptions=options.options, 
        hiddenRule=options.hidden, writer=eval(options.writer), featureFilePath=options.features, labelFilePath=options.labels, metaFilePath=options.meta)