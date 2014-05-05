import sqlite3
import os, sys
from collections import OrderedDict
import json
import time

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

def writeSVMLight(f, example, cls, features):
    f.write(str(cls) + " " + " ".join([str(key) + ":" + '{0:f}'.format(features[key]) for key in sorted(features.keys())]) + "\n")

def compileTemplate(template, arguments, key=None):
    template = template.replace("/{", "BRACKET_OPEN").replace("/}", "BRACKET_CLOSE")
    s = "\"" + template.replace("{","\" + ").replace("}"," + \"") + "\""
    if template[0] != "{" and template[-1] != "}":
        s = "con.execute(" + s + ")"
    template = template.replace("BRACKET_OPEN", "{").replace("BRACKET_CLOSE", "}")
    s = s.replace("\"\" + ", "").replace(" + \"\"", "")
    s = "lambda " + ",".join(arguments) + ": " + s
    print "Compiled template", [key, s]
    return eval(s)

def updateTemplateOptions(template, options):
    if "options" not in template:
        return None
    if options == None:
        return
    for key in options:
        template["options"][key] = options[key]

def parseTemplateOptions(string):
    if string == None:
        return None
    options = {}
    for split in string.split(","):
        split = split.strip()
        key, value = split.split("=", 1)
        try:
            options[key] = eval(value)
        except:
            options[key] = value
    return options

def getExamples(con, experimentName, callback, callbackArgs, metaDataFileName=None, options=None):
    con = connect(con)
    template = getExperiment(experimentName).copy()
    updateTemplateOptions(template)
    compiled = template.copy()
    for key in ["example", "class", "features", "meta"]:
        if isinstance(compiled[key], basestring):
            compiled[key] = compileTemplate(compiled[key], ["con", "example", "options"], key)
        elif isinstance(compiled[key], list):
            compiled[key] = [compileTemplate(x, ["con", "example", "options"], key) for x in compiled[key]]
    print "Compiled experiment"
    examples = [x for x in compiled["example"](con, None, options)]
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
        if count % 10 == 0:
            print "Processing example", example, cls, str(count) + "/" + str(numExamples)
        features = {}
        for featureGroup in featureGroups:
            for feature in featureGroup(con, example, options):
                features[getId(feature[0], featureIds)] = feature[1]
        if callback != None:
            callback(example=example, cls=cls, features=features, **callbackArgs)
        if "meta" in compiled:
            meta.append(compiled["meta"](con, example, options))
        count += 1
    saveMetaData(metaDataFileName, template, experimentName, clsIds, featureIds, meta)

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
    parser = argparse.ArgumentParser(description='Build examples from ICGC data')
    parser.add_argument('-o','--output', help='SVM-light format examples output file name', default=None)
    parser.add_argument('-m','--meta', help='Metadata output file name (optional)', default=None)
    parser.add_argument('-e','--experiment', help='Experiment template', default=None)
    parser.add_argument('-p','--options', help='Experiment template options', default=None)
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
    
    if options.meta != None and not os.path.exists(os.path.dirname(options.meta)):
        os.makedirs(os.path.dirname(options.meta))
    
    con = connect(options.database)
    getExamples(con, options.experiment, writer, writerArgs, options.meta, parseTemplateOptions(options.options))
    #getExamples2(con, options.experiment)
    
    if outFile != None:
        outFile.close()