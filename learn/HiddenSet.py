import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.pymersennetwister.mtwister import MTwister

def splitArray(array, setNames):
    assert array.shape[0] == len(setNames)
    indices = {}
    for i in range(len(setNames)):
        setName = setNames[i]
        if setName not in indices:
            indices[setName] = []
        indices[setName].append(i)
    divided = {}
    for key in indices:
        divided[key] = array[indices[key]]
    return divided

def splitData(examples, labels, meta):
    setNames = [x["set"] for x in meta.db["example"].all()]
    e = splitArray(examples, setNames)
    l = splitArray(labels, setNames)
    return e.get("train", []), e.get("hidden", []), l.get("train", []), l.get("hidden", [])   

class HiddenSet():
    def __init__(self):
        self.__random = MTwister()
        self.__random.set_seed(1)
        self.__thresholds = []
    
    def getThreshold(self, index):
        while len(self.__thresholds) <= index:
            self.__thresholds.append(self.__random.random())
        return self.__thresholds[index]
    
    def getDonorThreshold(self, donorId):
        donorIndex = int(donorId[2:])
        return self.getThreshold(donorIndex)