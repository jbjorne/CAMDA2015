import os
import inspect
from experiments import *
from learn.Classification import Classification
import utils.Stream as Stream
from utils.common import splitOptions

DATA_PATH = os.path.expanduser("~/data/CAMDA2015-data-local/")
DB_PATH = os.path.join(DATA_PATH, "database/ICGC-18-150514.sqlite")

def getFeatureGroups(names, dummy=False):
    groups = [eval(x) for x in names]
    for i in range(len(groups)): # Initialize classes
        if inspect.isclass(groups[i]):
            groups[i] = groups[i]()
        groups[i].dummy = dummy
    return groups

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run University of Turku experiments for CAMDA 2015')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    #parser.add_argument('-d', "--debug", default=False, action="store_true", dest="debug")
    parser.add_argument('-a', "--action", default=None, dest="action")
    groupE = parser.add_argument_group('build', 'Example Generation')
    #groupE.add_argument('-e', "--examples", default=False, action="store_true", dest="examples")
    groupE.add_argument('-e', '--experiment', help='Experiment class', default="RemissionMutTest")
    groupE.add_argument('-f', '--features', help='Feature groups (comma-separated list)', default=None)
    groupE.add_argument('-d', '--dummy', help='Feature groups used only for filtering (comma-separated list)', default=None)
    groupE.add_argument('-p', '--projects', help='Projects used in example generation', default=None)
    groupE.add_argument('-b', '--icgcDB', default=DB_PATH, dest="icgcDB")
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
    groupA.add_argument("-y", "--analyses", default="COSMICAnalysis")
    options = parser.parse_args()
    
    actions = splitOptions(options.action, ["build", "classify", "analyse"])
    
    Stream.openLog(os.path.join(options.output, "log.txt"), clear = "build" in actions)
    print "Options:", options.__dict__
    
    if "build" in actions:
        print "======================================================"
        print "Building Examples"
        print "======================================================"
        ExperimentClass = eval(options.experiment)
        e = ExperimentClass()
        e.includeSets = ("train", "hidden") if options.hidden else ("train",)
        if options.projects != None:
            e.projects = options.projects.split(",")
        if options.features != None:
            print "Using feature groups:", options.features
            e.featureGroups = getFeatureGroups(options.features.split(","))
            if options.dummy != None:
                print "With dummy groups:", options.dummy
                e.featureGroups = getFeatureGroups(options.dummy.split(","), dummy=True) + e.featureGroups
        e.databasePath = options.icgcDB
        e.writeExamples(options.output)
    
    resultPath = os.path.join(options.output, "classification.json")
    classification = None
    if "classify" in actions:
        print "======================================================"
        print "Classifying"
        print "======================================================"
        classification = Classification(options.classifier, options.classifierArguments, options.numFolds, options.parallel, options.metric, classifyHidden=options.hidden)
        classification.readExamples(options.output)
        classification.classify()
    
    if "analyse" in actions and options.analyses is not None:
        meta = resultPath
        if classification != None:
            meta = classification.meta
        for analysisName in options.analyses.split(","):
            print "======================================================"
            print "Analysing", analysisName
            print "======================================================"
            exec "from learn.analyse." + analysisName + " import " + analysisName
            analysisClass = eval(analysisName)
            analysisObj = analysisClass(dataPath=DATA_PATH)
            analysisObj.analyse(options.output, hidden=options.hidden)