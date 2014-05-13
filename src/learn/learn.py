import sys, os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.example import exampleOptions, readAuto
from data.template import parseOptionString, getMeta
from data.cache import getExperiment
from sklearn.cross_validation import StratifiedKFold
#from sklearn.grid_search import GridSearchCV
from skext.gridSearch import ExtendedGridSearchCV
from collections import defaultdict
import tempfile
from collections import OrderedDict

def getClassDistribution(y):
    counts = defaultdict(int)
    for value in y:
        counts[value] += 1
    return dict(counts)
    #bincount = numpy.nonzero(numpy.bincount(y))[0]
    #return zip(bincount,y[bincount])

def test(XPath, yPath, metaPath, resultPath, classifier, classifierArgs, numFolds=10, verbose=3, parallel=1, preDispatch='2*n_jobs'):
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
    if preDispatch.isdigit():
        preDispatch = int(preDispatch)
    search = ExtendedGridSearchCV(classifier(), [classifierArgs], cv=cv, scoring="roc_auc", verbose=verbose, n_jobs=parallel, pre_dispatch=preDispatch)
    search.fit(X, y) 
    print "----------------------------- Best Estimator -----------------------------------"
    print search.best_estimator_
    print "--------------------------------------------------------------------------------"
    print "---------------------- Grid scores on development set --------------------------"
    for params, mean_score, scores in search.grid_scores_:
        print scores
        print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
    print "--------------------------------------------------------------------------------"
    if resultPath != None:
        saveResults(search, meta, resultPath)

def setResultValue(target, key, value, parent=None, append=False):
    if parent != None and not parent in target:
        target[parent] = {}
        target = target[parent]
    if append:
        value = [value]
    if append and key in target:
        target[key].append(value)
    else:
        target[key] = value

def compareFeatures(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return a - b
    elif isinstance(a, dict) and isinstance(b, int):
        return 1
    elif isinstance(a, int) and isinstance(b, dict):
        return -1
    else:
        if len(a["importances"]) != len(b["importances"]):
            return len(a["importances"]) - len(b["importances"])
        else:
            return int(sum(a["importances"].values()) - len(b["importances"].values()))
                
def saveResults(search, meta, resultPath):
    if not hasattr(search, "extras_"):
        print "No detailed information for cross-validation"
        return
    if not os.path.exists(os.path.dirname(resultPath)):
        os.makedirs(os.path.dirname(resultPath))
    meta = getMeta(meta)
    # Insert results
    examples = meta["meta"]
    features = meta["features"]
    featureByIndex = {}
    for featureName in features:
        featureByIndex[features[featureName]] = featureName
    #for i in range(len(examples)):
    #    example = examples[i]
    fold = 0
    for extra in search.extras_:
        if "predictions" in extra:
            predictions = extra["predictions"]
            for index in predictions:
                example = examples[index]
                setResultValue(example, "prediction", predictions[index], "classification")
                setResultValue(example, "fold", fold, "classification")
        if "importances" in extra:
            foldImportances = extra["importances"]
            for i in range(len(foldImportances)):
                if foldImportances[i] != 0:
                    name = featureByIndex[i]
                    if isinstance(features[name], int):
                        features[name] = {"id":features[name]}
                    if not "importances" in features[name]:
                        features[name]["importances"] = {}
                    featureImportances = features[name]["importances"]
                    setResultValue(featureImportances, fold, foldImportances[i])
        fold += 1
    features = features.values()
    features.sort(cmp=compareFeatures)
    output = OrderedDict()
    for feature in features:
        if isinstance(feature, int):
            output[featureByIndex[feature]] = feature
        else:
            output[featureByIndex[feature["id"]]] = feature
    meta["features"] = output
                    
    # Save results
    f = open(resultPath, "wt")
    json.dump(meta, f, indent=4)
    f.close()
    
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
    parser.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=5)
    parser.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
    parser.add_argument('-p', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    parser.add_argument('--preDispatch', help='', default='2*n_jobs')
    parser.add_argument('-r', '--result', help='Output file for detailed results (optional)', default=None)
    options = parser.parse_args()
    
    classifier, classifierArgs = getClassifier(options.classifier, options.classifierArguments)
    featureFilePath, labelFilePath, metaFilePath = getExperiment(experiment=options.experiment, experimentOptions=options.options, 
                                                                 database=options.database, hidden=options.hidden, writer=options.writer, 
                                                                 useCached=not options.noCache, featureFilePath=options.features, 
                                                                 labelFilePath=options.labels, metaFilePath=options.meta)
    test(featureFilePath, labelFilePath, metaFilePath, classifier=classifier, classifierArgs=classifierArgs, 
         numFolds=options.numFolds, verbose=options.verbose, parallel=options.parallel, 
         preDispatch=options.preDispatch, resultPath=options.result)