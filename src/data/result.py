from collections import OrderedDict
import json

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

def getMeta(meta, verbose=True):
    if not isinstance(meta, basestring):
        return meta
    print "Loading metadata from", meta
    f = open(meta, "rt")
    meta = json.load(f)
    f.close()
    return meta

def saveMeta(meta, filename, verbose=True):
    sortFeatures(meta)
    meta = sortMeta(meta)
    print "Saving metadata to", filename
    f = open(filename, "wt")
    json.dump(meta, f, indent=4)
    f.close()

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
