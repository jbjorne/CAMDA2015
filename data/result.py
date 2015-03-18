from collections import OrderedDict
import json
import os

###############################################################################
# Output directory processing
###############################################################################

def countExamples(meta):
    counts = {"1":0, "-1":0}
    for example in meta["examples"]:
        counts[example["label"]] += 1
    return counts

def getProjects(dirname, filter=None, numTopFeatures=0):
    projects = {}
    print "Reading results from", dirname
    filenames = os.listdir(dirname)
    index = 0
    if filter == None:
        filter = {}
    for dirpath, dirnames, filenames in os.walk(dirname):
        for filename in filenames:
            index += 1
            filePath = os.path.join(dirpath, filename)
            found = True
            if filter.get("filename") != None:
                found = False
                for substring in filter["filename"]:
                    if substring in filename:
                        found = True
                        break
            if found and os.path.isfile(filePath) and filePath.endswith(".json"):
                # Read project results
                meta = getMeta(filePath)
                options = {}
                optionsList = meta["experiment"]["options"]
                if optionsList != None:
                    optionsList = optionsList.split(",")
                    for optionPair in optionsList:
                        key, value = optionPair.split("=")
                        options[key] = value
                # Filter by features
                if filter.get("features") == None or ("features" in options and options["features"] == filter.get("features")):
                    # Add results for project...
                    projectName = meta["template"]["project"]
                    if projectName not in filter.get("projects"):
                        continue
                    if projectName not in projects:
                        projects[projectName] = {}
                    project = projects[projectName]
                    # ... for experiment ...
                    experimentName = meta["experiment"]["name"]
                    if experimentName not in filter.get("experiments"):
                        continue
                    if experimentName not in project:
                        project[experimentName] = {}
                    experiment = project[experimentName]
                    # ... for classifier ...
                    classifierName = meta["results"]["best"]["classifier"]
                    if classifierName not in filter.get("classifiers"):
                        continue
                    experiment[classifierName] = meta
                    print "Read", filename, str(index+1) #+ "/" + str(len(filenames))
                    #experiment["classifier"] = meta["results"]["best"]["classifier"]
    return projects

###############################################################################
# JSON metadata read/write
###############################################################################

def getMeta(meta, verbose=True):
    if not isinstance(meta, basestring):
        return meta
    print "Loading metadata from", meta
    f = open(meta, "rt")
    meta = json.load(f, object_pairs_hook=OrderedDict)
    f.close()
    return meta

def saveMeta(meta, filename, verbose=True):
    sortFeatures(meta)
    meta = sortMeta(meta)
    print "Saving metadata to", filename
    f = open(filename, "wt")
    json.dump(meta, f, indent=4)
    f.close()

###############################################################################
# Individual examples and features
###############################################################################

def getExampleFromSet(meta, index, setName):
    i = -1
    for example in meta["examples"]:
        if example["set"] == setName:
            i += 1
        if i == index:
            return example

def getExample(meta, index):
    return meta["examples"][index]

def getExamples(meta, indices):
    return {i:meta["examples"][i] for i in indices}

def getFeaturesByIndex(meta):
    featuresByIndex = {}
    for name, index in meta["features"].iteritems():
        if isinstance(index, int):
            featuresByIndex[index] = name
        else:
            featuresByIndex[index["id"]] = name
    return featuresByIndex

def getFeature(meta, index, featuresByIndex=None):
    if featuresByIndex == None:
        featuresByIndex = getFeaturesByIndex(meta)
    name = featuresByIndex[index]
    if isinstance(meta["features"][name], int):
        meta["features"][name] = {"id":meta["features"][name]}
    return meta["features"][name]

def getFeatures(meta, indices, featuresByIndex=None):
    if featuresByIndex == None:
        featuresByIndex = getFeaturesByIndex(meta)
    rv = {}
    features = meta["features"]
    for index in indices:
        name = featuresByIndex[index]
        if isinstance(features[name], int):
            features[name] = {"id":features[name]}
        rv[index] = features[name]
    return rv

###############################################################################
# Utilities
###############################################################################

def setValue(target, key, value, parent=None):
    if parent != None:
        if not parent in target:
            target[parent] = {}
        target = target[parent]
    target[key] = value

def sortMeta(meta):
    keys = meta.keys()
    sortedKeys = []
    for named in ["experiment", "template", "classes", "results", "analysis", "features", "examples"]:
        if named in keys:
            sortedKeys.append(named)
            keys.remove(named)
    sortedKeys += sorted(keys)
    output = OrderedDict()
    for key in sortedKeys:
        output[key] = meta[key]
    return output

def sortFeatures(meta, featuresByIndex=None, addRank=True):
    if featuresByIndex == None:
        featuresByIndex = getFeaturesByIndex(meta)
    # Sort features
    featureValues = meta["features"].values()
    featureValues.sort(cmp=compareFeatures)
    features = OrderedDict()
    for index, feature in enumerate(featureValues):
        if isinstance(feature, int):
            features[featuresByIndex[feature]] = feature
        else:
            features[featuresByIndex[feature["id"]]] = feature
            if addRank:
                feature["rank"] = index + 1
    meta["features"] = features

def compareFeatures(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return a - b
    elif isinstance(a, dict) and isinstance(b, int):
        return -1
    elif isinstance(a, int) and isinstance(b, dict):
        return 1
    elif "sort" in a and "sort" in b:
        return -cmp(a["sort"], b["sort"])
    elif "sort" in a:
        return -1
    elif "sort" in b:
        return 1
    else: # a and b are dict, neither has a sort attribute
        return a["id"] - b["id"]
