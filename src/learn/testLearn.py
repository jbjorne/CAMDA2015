import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.example import exampleOptions, evalWriter, readAuto
from data import buildExamples
from data.template import parseOptionString, getMeta, getTemplateId
from sklearn.cross_validation import StratifiedKFold
#from sklearn.grid_search import GridSearchCV
from learn.skext.gridSearch import ExtendedGridSearchCV
from collections import defaultdict
import tempfile

def getClassDistribution(y):
    counts = defaultdict(int)
    for value in y:
        counts[value] += 1
    return dict(counts)
    #bincount = numpy.nonzero(numpy.bincount(y))[0]
    #return zip(bincount,y[bincount])

def test(XPath, yPath, metaPath, classifier, classifierArgs, numFolds=10, verbose=3, parallel=1):
    X, y = readAuto(XPath, yPath)
    meta = {}
    if metaPath != None:
        print "Loading metadata from", metaPath
        meta = getMeta(metaPath)
    if "classes" in meta:
        print "Class distribution = ", getClassDistribution(y)

    print "Cross-validating for", numFolds, "folds"
    print "Args", classifierArgs
    cv = StratifiedKFold(y, n_folds=numFolds)
    search = ExtendedGridSearchCV(classifier(), [classifierArgs], cv=cv, scoring="roc_auc", verbose=verbose, n_jobs=parallel)
    search.fit(X, y) 
    print "----------------- Best Estimator ---------------------"
    print search.best_estimator_
    print "------------------------------------------------------"
    print "----------- Grid scores on development set -----------"
    for params, mean_score, scores in search.grid_scores_:
        print scores
        print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
    print "------------------------------------------------------"
    
def getClassifier(classifierName, classifierArguments):
    if "." in classifierName:
        importCmd = "from sklearn." + classifierName.rsplit(".", 1)[0] + " import " + classifierName.rsplit(".", 1)[1]
    else:
        importCmd = "import " + classifierName
    print importCmd
    exec importCmd
    classifier = eval(classifierName.rsplit(".", 1)[1]) 
    classifierArgs=parseOptionString(classifierArguments)
    print "Using classifier", classifierName, "with arguments", classifierArgs
    return classifier, classifierArgs
    
def getExperiment(experiment, experimentOptions, database, hidden='skip', writer='writeNumpyText', useCache=True,
                  featureFilePath=None, labelFilePath=None, metaFilePath=None, cacheDir=os.path.join(tempfile.gettempdir(), "CAMDA2014")):
    """
    Get a cached experiment, or re-calculate if not cached.
    
    experiment = Name of the experiment template in settings.py (such as REMISSION)
    experimentOptions = comma-separated list of key=value pairs, the keys will replace those
                        with the same name in the experiment template. Values are evaluated.
    database = Path to the SQLite database (see data/example.py)
    hidden = How to process hidden donors (see data/example.py)
    writer = Output format (see data/example.py)
    useCache = Whether to use the cache directory. If False, X, y and meta paths must be defined.
    featureFilePath = X, can be None if useCache == True.
    labelFilePath = y, can be None if useCache == True.
    metaFilePath = Meta-data, can be None if useCache == True. If already exists, the experiment
                   will be compared to this. If they are identical, the cached version is used.
    cacheDir = Where cached experiments are stored.
    """
    cached = None
    if experiment != None and useCache:
        template = buildExamples.getExperiment(experiment).copy()
        template = buildExamples.parseTemplateOptions(experimentOptions, template)
        project = template.get("project", "")
        projectId = "".join([c if c.isalpha() or c.isdigit() or c=="-" else "_" for c in project]).strip()
        tId = options.experiment + "_" + projectId + "_" + getTemplateId(template)
        if featureFilePath == None:
            featureFilePath = os.path.join(cacheDir, tId + "-X")
        if labelFilePath == None:
            labelFilePath = os.path.join(cacheDir, tId + "-y")
        if metaFilePath == None:
            metaFilePath = os.path.join(cacheDir, tId + "-meta.json")
        if os.path.exists(metaFilePath):
            print "Comparing to cached experiment", metaFilePath
            cached = buildExamples.getCached(database, experiment, experimentOptions, metaFilePath)
    
    if cached != None:
        print "Using cached examples"
        featureFilePath = cached["experiment"].get("X", None)
        labelFilePath = cached["experiment"].get("y", None)
    print "Experiment files"
    print "X:", featureFilePath
    print "y:", labelFilePath
    print "meta:", metaFilePath
    
    if cached == None:
        print "Building examples for experiment", experiment, "at cache directory:", cacheDir
        buildExamples.writeExamples(dbPath=options.database, experimentName=options.experiment, experimentOptions=options.options, 
                                    hiddenRule=options.hidden, writer=evalWriter(options.writer), featureFilePath=options.features, labelFilePath=options.labels, metaFilePath=options.meta)
    
    return featureFilePath, labelFilePath, metaFilePath

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(parents=[exampleOptions], description='Learning with examples')
    parser.add_argument('-x','--features', help='Input file for feature vectors (X)', default=None)
    parser.add_argument('-y','--labels', help='Input file for class labels (Y)', default=None)
    parser.add_argument('-m','--meta', help='Metadata input file name (optional)', default=None)
    parser.add_argument('--noCache', help='Do not use cache', default=False, action="store_true")
    parser.add_argument('--cacheDir', help='Cache directory, used if x, y or m are undefined (optional)', default=os.path.join(tempfile.gettempdir(), "CAMDA2014"))
    parser.add_argument('-c','--classifier', help='', default='ensemble.RandomForestClassifier')
    parser.add_argument('-a','--classifierArguments', help='', default=None)
    parser.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=10)
    parser.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
    parser.add_argument('-p', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    options = parser.parse_args()
    
    classifier, classifierArgs = getClassifier(options.classifier, options.classifierArguments)
    featureFilePath, labelFilePath, metaFilePath = getExperiment(experiment=options.experiment, experimentOptions=options.options, 
                                                                 database=options.database, hidden=options.hidden, writer=options.writer, 
                                                                 useCache=not options.noCache, featureFilePath=options.features, 
                                                                 labelFilePath=options.labels, metaFilePath=options.meta)
    test(featureFilePath, labelFilePath, metaFilePath, classifier=classifier, classifierArgs=classifierArgs, numFolds=options.numFolds, verbose=options.verbose, parallel=options.parallel)