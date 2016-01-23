import sys, os
from learn.analyse.ProjectAnalysis import ProjectAnalysis
#import inspect
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Classification import Classification
#import utils.Stream as Stream
#from utils.common import splitOptions, getOptions
import traceback
#from experiments import *

# DATA_PATH = os.path.expanduser("~/data/CAMDA2015-data-local/")
# DB_PATH = os.path.join(DATA_PATH, "database/ICGC-18-150514.sqlite")
# 
# def getFeatureGroups(names, dataPath, dummy=False):
#     global DATA_PATH
#     groups = [eval(x) for x in names]
#     for i in range(len(groups)): # Initialize classes
#         if inspect.isclass(groups[i]):
#             groups[i] = groups[i]()
#         groups[i].dummy = dummy
#         groups[i].initialize(DATA_PATH)
#     return groups

class SubsetClassification(Classification):
    def __init__(self, classifierName, classifierArgs, numFolds=10, parallel=1, metric='roc_auc', getCV=None, preDispatch='2*n_jobs', classifyHidden=False):
        super(SubsetClassification, self).__init__(classifierName, classifierArgs, numFolds, parallel, metric, getCV, preDispatch, classifyHidden)
        self.analysis = None
    
    def _getTag(self, projects):
        return ",".join(projects)
    
    def classifyProjects(self, projects):
        print "----------------------", "Classifying projects", projects, "----------------------"
        setNames = []
        for example in self.meta.db["example"].all():
            if example["project_code"] in projects:
                setNames.append(example["set"])
            else:
                setNames.append(None)
        try:
            self.indices, X_train, X_hidden, y_train, y_hidden = self._splitData(setNames=setNames)
            search = self._crossValidate(y_train, X_train, self.classifyHidden and (X_hidden.shape[0] > 0))
            if self.classifyHidden:
                self._predictHidden(y_hidden, X_hidden, search, y_train.shape[0])
            print "Analysing project performance"
            self.analysis.analyse(self.inDir, None, X_hidden.shape[0] > 0, tag=self._getTag(projects), clear=False, projects=projects)
        except ValueError, err:
            print(traceback.format_exc())
    
    def readExamples(self, inDir, fileStem=None, exampleIO=None, preserveTables=None):
        super(SubsetClassification, self).readExamples(inDir=inDir, fileStem=fileStem, exampleIO=exampleIO, preserveTables=preserveTables)
        self.analysis = ProjectAnalysis(inDir)
        self.inDir = inDir
        
    def classify(self):
        examples = self.meta.db["example"].all()
        projects = sorted(set([x["project_code"] for x in examples]))
        self.classifyGrow([], projects)
#         combinations = [[x] for x in projects]
#         for combination in combinations:
#             self.classifyGrow(combination, projects)
        
    def classifyGrow(self, combination, allProjects, prevResults=None):
        if prevResults == None:
            prevResults = {}
        for project in allProjects:
            if project in combination:
                continue
            extended = combination + [project]
            self.classifyProjects(extended)
            rows = self.meta.db.query("SELECT * FROM project_analysis WHERE setName=='train' AND tag='{TAG}'".replace("{TAG}", self._getTag(extended)))
            results = {row["project"]:row["auc"] for row in rows}
            for key in results:
                if results[key] != None and results[key] < results.get(key, -1):
                    return # Performance dropped
            self.classifyGrow(extended, allProjects, results)
                        

# if __name__ == "__main__":
#     import argparse
#     parser = argparse.ArgumentParser(description='Run University of Turku experiments for CAMDA 2015')
#     parser.add_argument('-o', '--output', help='Output directory', default=None)
#     #parser.add_argument('-d', "--debug", default=False, action="store_true", dest="debug")
#     parser.add_argument('-a', "--action", default="build,classify,analyse", dest="action")
#     groupE = parser.add_argument_group('build', 'Example Generation')
#     #groupE.add_argument('-e', "--examples", default=False, action="store_true", dest="examples")
#     groupE.add_argument('-e', '--experiment', help='Experiment class', default="RemissionMutTest")
#     groupE.add_argument('-f', '--features', help='Feature groups (comma-separated list)', default=None)
#     groupE.add_argument('-d', '--dummy', help='Feature groups used only for filtering (comma-separated list)', default=None)
#     groupE.add_argument('-p', '--projects', help='Projects used in example generation', default=None)
#     groupE.add_argument('-b', '--icgcDB', default=DB_PATH, dest="icgcDB")
#     groupE.add_argument('-x', '--extra', default=None)
#     groupC = parser.add_argument_group('classify', 'Example Classification')
#     groupC.add_argument('-c','--classifier', help='', default=None)
#     groupC.add_argument('-r','--classifierArguments', help='', default=None)
#     groupC.add_argument('-m','--metric', help='', default="roc_auc")
#     #groupC.add_argument('-i','--iteratorCV', help='', default='getStratifiedKFoldCV')
#     groupC.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=10)
#     groupC.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
#     groupC.add_argument('-l', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
#     groupC.add_argument("--hidden", default=False, action="store_true", dest="hidden")
#     groupC.add_argument('--preDispatch', help='', default='2*n_jobs')
#     groupA = parser.add_argument_group('Analysis', 'Analysis for classified data')
#     groupA.add_argument("-y", "--analyses", default="ProjectAnalysis")
#     options = parser.parse_args()
#     
#     actions = splitOptions(options.action, ["classify", "analyse"])
#     Stream.openLog(os.path.join(options.output, "log.txt"), False)
#     print "Options:", options.__dict__
#     
#     if "build" in actions:
#         print "======================================================"
#         print "Building Examples"
#         print "======================================================"
#         ExperimentClass = eval(options.experiment)
#         if options.extra:
#             e = ExperimentClass(**getOptions(options.extra))
#         else:
#             e = ExperimentClass()
#         e.includeSets = ("train", "hidden") if options.hidden else ("train",)
#         e.projects = options.projects
#         if options.features != None:
#             print "Using feature groups:", options.features
#             e.featureGroups = getFeatureGroups(options.features.split(","))
#             if options.dummy != None:
#                 print "With dummy groups:", options.dummy
#                 e.featureGroups = getFeatureGroups(options.dummy.split(","), dummy=True) + e.featureGroups
#         e.databasePath = options.icgcDB
#         e.writeExamples(options.output)
#         e = None
#     
#     if "classify" in actions:
#         print "======================================================"
#         print "Learning Curve"
#         print "======================================================"
#         classification = SubsetClassification(options.classifier, options.classifierArguments, options.numFolds, options.parallel, options.metric, classifyHidden=options.hidden)
#         classification.readExamples(options.output, preserveTables=["result", "prediction", "importance"])
#         classification.classify()