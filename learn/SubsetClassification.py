import sys, os
from _random import Random
from learn.analyse.ProjectAnalysis import ProjectAnalysis
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Classification import Classification, countUnique
import utils.Stream as Stream
from utils.common import splitOptions

DATA_PATH = os.path.expanduser("~/data/CAMDA2015-data-local/")
DB_PATH = os.path.join(DATA_PATH, "database/ICGC-18-150514.sqlite")

class SubsetClassification(Classification):
    def __init__(self, classifierName, classifierArgs, numFolds=10, parallel=1, metric='roc_auc', getCV=None, preDispatch='2*n_jobs', classifyHidden=False,
                 steps=10, seed=2):
        super(SubsetClassification, self).__init__(classifierName, classifierArgs, numFolds, parallel, metric, getCV, preDispatch, classifyHidden)
        self.steps = steps
        self.random = Random(seed)
        self.thresholds = None
        self.currentCutoff = None
        self.saveExtra = False
        self.analysis = None
        
    def classifyProjects(self, X_train, X_hidden, y_train, y_hidden, projects):
        print "----------------------", "Classifying projects", projects, "----------------------"
        search = self._crossValidate(y_train, X_train, self.classifyHidden and (X_hidden.shape[0] > 0))
        if self.classifyHidden:
            self._predictHidden(y_hidden, X_hidden, search, y_train.shape[0])
        self.analysis.analyse(self.inDir, None, X_hidden.shape[0] > 0, tag=",".join(projects), clear=False)
    
    def readExamples(self, inDir, fileStem=None, exampleIO=None, preserveTables=None):
        Classification.readExamples(self, inDir, fileStem=fileStem, exampleIO=exampleIO, preserveTables=preserveTables)
        self.analysis = ProjectAnalysis(inDir)
        self.inDir = inDir
        
    def classify(self):
        projects = sorted(set([x["project_code"] for x in self.examples]))
        self.indices, X_train, X_hidden, y_train, y_hidden = self._splitData()
        for project in projects:
            self.classifyProjects(X_train, X_hidden, y_train, y_hidden, [project])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run University of Turku experiments for CAMDA 2015')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    #parser.add_argument('-d', "--debug", default=False, action="store_true", dest="debug")
    parser.add_argument('-a', "--action", default="build,classify,analyse", dest="action")
    groupE = parser.add_argument_group('build', 'Example Generation')
    #groupE.add_argument('-e', "--examples", default=False, action="store_true", dest="examples")
    groupE.add_argument('-e', '--experiment', help='Experiment class', default="RemissionMutTest")
    groupE.add_argument('-f', '--features', help='Feature groups (comma-separated list)', default=None)
    groupE.add_argument('-d', '--dummy', help='Feature groups used only for filtering (comma-separated list)', default=None)
    groupE.add_argument('-p', '--projects', help='Projects used in example generation', default=None)
    groupE.add_argument('-b', '--icgcDB', default=DB_PATH, dest="icgcDB")
    groupE.add_argument('-x', '--extra', default=None)
    groupC = parser.add_argument_group('classify', 'Example Classification')
    groupC.add_argument('-c','--classifier', help='', default=None)
    groupC.add_argument('-r','--classifierArguments', help='', default=None)
    groupC.add_argument('-m','--metric', help='', default="roc_auc")
    #groupC.add_argument('-i','--iteratorCV', help='', default='getStratifiedKFoldCV')
    groupC.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=10)
    groupC.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
    groupC.add_argument('-l', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    groupC.add_argument("--hidden", default=False, action="store_true", dest="hidden")
    groupC.add_argument('--preDispatch', help='', default='2*n_jobs')
    groupA = parser.add_argument_group('Analysis', 'Analysis for classified data')
    groupA.add_argument("-y", "--analyses", default="ProjectAnalysis")
    options = parser.parse_args()
    
    actions = splitOptions(options.action, ["classify", "analyse"])
    Stream.openLog(os.path.join(options.output, "log.txt"), False)
    print "Options:", options.__dict__
    
    if "classify" in actions:
        print "======================================================"
        print "Learning Curve"
        print "======================================================"
        classification = PairClassification(options.classifier, options.classifierArguments, options.numFolds, options.parallel, options.metric, classifyHidden=options.hidden)
        classification.readExamples(options.output, preserveTables=["result", "prediction", "importance"])
        classification.classify()