"""
For calculating a hidden set of donors.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.pymersennetwister.mtwister import MTwister

__hiddenRandom = MTwister()
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

def getInclude(example, templateHidden, hiddenRule, verbose=True):
    if hiddenRule not in ("skip", "include", "only"):
        raise Exception("Unknown hidden set rule '" + str(hiddenRule) + "'")
    if templateHidden == None:
        return True
    if hiddenRule == "skip" and example["hidden"] < templateHidden:
        if verbose:
            print "Skipping example from hidden donor", example["icgc_donor_id"]
        return False
    elif hiddenRule == "only" and example["hidden"] >= templateHidden:
        if verbose:
            print "Skipping example " + str(example) + " from non-hidden donor", example["icgc_donor_id"]
        return False
    else:
        return True