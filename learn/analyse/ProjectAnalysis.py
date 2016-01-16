import os
from learn.analyse.Analysis import Analysis

class ProjectAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(ProjectAnalysis, self).__init__(dataPath=dataPath)
        
    def analyse(self, inDir, fileStem=None, hidden=False):
        meta = self._getMeta(inDir, fileStem)
        meta.drop("project_analysis", 100000)