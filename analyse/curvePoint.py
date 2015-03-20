import sys, os, shutil
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import result, cache
from learn import learn
from learn.learn import getStratifiedKFoldCV as StratifiedKFold
import sklearn
import settings
import inspect
from collections import OrderedDict

def curvePoint(XPath, yPath, meta, featureCount, resultPath, classifier, classifierArgs, getCV, numFolds, verbose, parallel, preDispatch, randomize, metric):
    if isinstance(meta, basestring):
        meta = result.getMeta(meta)
    
    features = meta["features"][:featureCount]
    featureSet = [x["id"] for x in features]
    
    cls = meta["results"]["best"]
    paramSets = [x["params"] for x in meta["results"]["all"]]
    params = {}
    for paramSet in paramSets:
        for key in paramSet:
            if not key in params:
                params[key] = []
            params[key].append(paramSet[key])
    classifierNameMap = {"LinearSVC":"svm.LinearSVC","ExtraTreesClassifier":"ensemble.ExtraTreesClassifier","RLScore":"RLScore"}
    classifierName = classifierNameMap[cls["classifier"]]
    classifier, params = learn.getClassifier(classifierName, params)
    
    meta, results, extras, hiddenResults, hiddenDetails = learn.test(
        XPath, yPath, meta, resultPath, 
        classifier=classifier, classifierArgs=params, getCV=eval(getCV), 
        numFolds=numFolds, verbose=verbose, parallel=parallel, preDispatch=preDispatch, 
        randomize=randomize, analyzeResults=False, 
        metric=metric, useFeatures=featureSet)
    return [meta, results, extras, hiddenResults, hiddenDetails]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Learning with examples')
    parser.add_argument('-X','--features', help='Metadata input file name', default=None)
    parser.add_argument('-y','--classes', help='Metadata input file name', default=None)
    parser.add_argument('-m','--meta', help='Metadata input file name', default=None)
    parser.add_argument('-r','--result', help='Result path', default=None)
    parser.add_argument('--cutoff', help='Number of features to test', type=int, default=30)
    parser.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
    parser.add_argument('-p', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    parser.add_argument('--preDispatch', help='', default='2*n_jobs')
    parser.add_argument('--randomize', help='', default=False, action="store_true")
    parser.add_argument('--clearCache', default=False, action="store_true")
    options = parser.parse_args()
    
    curvePoint(options.X, options.y, options.meta, options.result, options.cutoff,
            verbose=options.verbose, parallel=options.parallel, preDispatch=options.preDispatch, 
            randomize=options.randomize)