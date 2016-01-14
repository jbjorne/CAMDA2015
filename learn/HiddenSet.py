import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.pymersennetwister.mtwister import MTwister

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