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
from numbers import Number

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

def getExamples(con, experimentName, callback, callbackArgs, metaDataFileName=None, options=None, hiddenRule="skip"):
    con = connect(con)
    template = getExperiment(experimentName).copy()
    template = parseTemplateOptions(options, template)
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
    clsIds = compiled.get("classIds", {})
    featureIds = {}
    meta = []
    featureGroups = compiled.get("features", [])
    for example in examples:
        count += 1
        cls = getId(compiled["label"](con=con, example=example, **lambdaArgs), clsIds)
        if not hidden.getInclude(example, compiled.get("hidden", None), hiddenRule):
            continue
        #print experiment["class"](con, example)
        #if count % 10 == 0:
        print "Processing example", example, cls, str(count) + "/" + str(numExamples)
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
    parser.add_argument('--hidden', help='Inclusion of hidden examples: skip,include,only (default=skip)', default="skip")
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
    featureIds = getExamples(con, options.experiment, writer, writerArgs, options.meta, options.options)
    #getExamples2(con, options.experiment)
    
    for outFile in opened.values():
        outFile.close()
    if options.writer == "writeNumpyText" and options.features != None:
        padNumpyFeatureFile(options.features, len(featureIds))