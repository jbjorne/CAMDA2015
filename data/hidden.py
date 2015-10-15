"""
For calculating a hidden set of donors.
"""
import sys, os
import result
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.pymersennetwister.mtwister import MTwister
import numpy

__hiddenRandom = MTwister()
#__hiddenRandom.set_seed(300000) #__hiddenRandom.set_seed(1)
__hiddenRandom.set_seed(1)
__hidden = []

def getHiddenValue(index):
    while len(__hidden) <= index:
        __hidden.append(__hiddenRandom.random())
    return __hidden[index]

def getDonorHiddenValue(icgc_donor_id):
    return getHiddenValue(int(icgc_donor_id[2:]))

def setHiddenValues(examples, template, donorIdKey="icgc_donor_id"):
    numHidden = 0
    if "hidden" in template:
        for example in examples:
            example["hidden"] = getDonorHiddenValue(example[donorIdKey])
            if example["hidden"] < template["hidden"]:
                numHidden += 1
    return numHidden

def setHiddenValuesByFraction(examples, hiddenFraction, donorIdKey="icgc_donor_id"):
    numHidden = 0
    if hiddenFraction > 0:
        for example in examples:
            example["hidden"] = getDonorHiddenValue(example[donorIdKey])
            if example["hidden"] < hiddenFraction:
                numHidden += 1
    return numHidden

def getInclude(example, templateHidden, hiddenRule, verbose=True):
    if hiddenRule not in ("train", "hidden", "both"):
        raise Exception("Unknown hidden set rule '" + str(hiddenRule) + "'")
    if templateHidden == None:
        return True
    if hiddenRule == "train" and example["hidden"] < templateHidden:
        if verbose:
            print "Skipping example from hidden donor", example["icgc_donor_id"]
        return False
    elif hiddenRule == "hidden" and example["hidden"] >= templateHidden:
        if verbose:
            print "Skipping example " + str(example) + " from non-hidden donor", example["icgc_donor_id"]
        return False
    else:
        return True

def setSet(example, templateHidden):
    if example.get("hidden", None) != None and example["hidden"] < templateHidden:
        example["set"] = "hidden"
    else:
        example["set"] = "train"
    return example["set"]

hiddenFilter = None

def split(*arrays, **options):
    global hiddenFilter
    """
    Get train and hidden sets using example metadata. Call with e.g.
    X_train, X_hidden, y_train, y_hidden = hidden.split(X, y, meta=meta)
    where X and y are Numpy arrays and meta is the metadata dictionary.
    """
    # Modified from sklearn.cross_validation.train_test_split
    n_arrays = len(arrays)
    if n_arrays == 0:
        raise ValueError("At least one array required as input")
    
    hidden = options.pop('hidden', None)
    if hidden == None:
        meta = options.pop('meta', None)
        meta = result.getMeta(meta)
        hidden = set()
        for index, example in enumerate(meta["examples"]):
            addToHidden = False
            if example.get("set", None) == 'hidden':
                addToHidden = True
            if hiddenFilter != None and example.get(hiddenFilter[0], None) != hiddenFilter[1]:
                addToHidden = False
            if addToHidden:
                hidden.add(index)
    
    numColumns = arrays[0].shape[0] #len(arrays[0])
    #print numColumns
    train = set()
    for index in range(numColumns):
        if index not in hidden:
            train.add(index)
    train = sorted(list(train))
    hidden = sorted(list(hidden))
    #print "Train", train
    #print "Hidden", hidden
    
    #for a in arrays:
    #    print "A", a
    splitted = []
    for a in arrays:
        if a.shape[0] != numColumns: #len(a) != numColumns:
            raise Exception("Array sizes differ")
        if len(train) > 0:
            splitted.append(a[train])
        else:
            splitted.append(numpy.zeros(0))
        if len(hidden) > 0:
            splitted.append(a[hidden])
        else:
            splitted.append(numpy.zeros(0))
    #for a in splitted:
    #    print "S", a
    return splitted