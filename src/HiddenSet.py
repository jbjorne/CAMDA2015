from numpy import array
from lib.pymersennetwister.mtwister import MTwister

def splitArray(array, setNames):
    assert array.shape[0] == len(setNames)
    indices = {}
    for i in range(len(setNames)):
        setName = setNames[i]
        if setName == None: # skip this example
            continue
        if setName not in indices:
            indices[setName] = []
        indices[setName].append(i)
    divided = {}
    for setName in indices:
        divided[setName] = array[indices[setName]]
    return divided, indices

# def splitExamples(examples, labels, meta):
#     return splitData(examples, labels, [x["set"] for x in meta.db["example"].all()])
    
def splitData(examples, labels, setNames):
    e, indices = splitArray(examples, setNames)
    l, indices = splitArray(labels, setNames)
    return indices, e.get("train", array([])), e.get("hidden", array([])), l.get("train", array([])), l.get("hidden", array([]))   

class HiddenSet():
    def __init__(self, seed=1):
        self.__random = MTwister()
        self.__random.set_seed(seed)
        self.__thresholds = []
    
    def getThreshold(self, index):
        while len(self.__thresholds) <= index:
            self.__thresholds.append(self.__random.random())
        return self.__thresholds[index]
    
    def getDonorThreshold(self, donorId):
        donorIndex = int(donorId[2:])
        return self.getThreshold(donorIndex)