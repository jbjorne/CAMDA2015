from collections import OrderedDict
import json

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

def getMeta(meta):
    if not isinstance(meta, basestring):
        return meta
    f = open(meta, "rt")
    meta = json.load(f)
    f.close()
    return meta

def saveMeta(meta, filename):
    sortFeatures(meta)
    meta = sortMeta(meta)
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
    for named in ["experiment", "template", "classes", "results", "features", "examples"]:
        if named in keys:
            sortedKeys.append(named)
            keys.remove(named)
    sortedKeys += sorted(keys)
    output = OrderedDict()
    for key in sortedKeys:
        output[key] = meta[key]
    return output

def sortFeatures(meta, featuresByIndex=None):
    if featuresByIndex == None:
        featuresByIndex = getFeaturesByIndex(meta)
    # Sort features
    featureValues = meta["features"].values()
    featureValues.sort(cmp=compareFeatures)
    features = OrderedDict()
    for feature in featureValues:
        if isinstance(feature, int):
            features[featuresByIndex[feature]] = feature
        else:
            features[featuresByIndex[feature["id"]]] = feature
    meta["features"] = features

def compareFeatures(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return a - b
    elif isinstance(a, dict) and isinstance(b, int):
        return -1
    elif isinstance(a, int) and isinstance(b, dict):
        return 1
    else:
        return -cmp(a["sort"], b["sort"])
