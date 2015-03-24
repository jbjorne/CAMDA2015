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

def curvePoint(XPath, yPath, meta, resultPath, featureCount, classifier, classifierArgs, getCV, numFolds, verbose, parallel, preDispatch, randomize, metric):
    if isinstance(meta, basestring):
        meta = result.getMeta(meta)
    
    count = 0
    featureSet = []
    for featureName in meta["features"]: # features must be already analysed
        featureSet.append(meta["features"][featureName]["id"])
        count += 1
        if count > featureCount:
            break
    print "Testing", len(featureSet), "features", featureSet
    
    classifierNameMap = {
        "LinearSVC":"svm.LinearSVC",
        "svm.LinearSVC":"svm.LinearSVC",
        "ExtraTreesClassifier":"ensemble.ExtraTreesClassifier",
        "ensemble.ExtraTreesClassifier":"ensemble.ExtraTreesClassifier",
        "RLScore":"RLScore"
    }
    classifierName = classifierNameMap[classifier]
    classifier, classifierArgs = learn.getClassifier(classifierName, eval(classifierArgs))
    
    meta, results, extras, hiddenResults, hiddenDetails = learn.test(
        XPath, yPath, meta, resultPath, 
        classifier=classifier, classifierArgs=classifierArgs, getCV=eval(getCV), 
        numFolds=numFolds, verbose=verbose, parallel=parallel, preDispatch=preDispatch, 
        randomize=randomize, analyzeResults=False, 
        metric=metric, useFeatures=featureSet, reclassify=True)
    return [meta, results, extras, hiddenResults, hiddenDetails]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Learning with examples')
    parser.add_argument('-X','--features', help='Metadata input file name', default=None)
    parser.add_argument('-y','--classes', help='Metadata input file name', default=None)
    parser.add_argument('-m','--meta', help='Metadata input file name', default=None)
    parser.add_argument('-o','--output', help='Result path', default=None)
    parser.add_argument('--cutoff', help='Number of features to test', type=int, default=30)
    parser.add_argument('-c','--classifier', help='', default='ensemble.RandomForestClassifier')
    parser.add_argument('-a','--classifierArgs', help='', default=None)
    parser.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
    parser.add_argument('-p', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    parser.add_argument('--metric', help='', default="roc_auc")
    parser.add_argument('-i','--iteratorCV', help='', default='getStratifiedKFoldCV')
    parser.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=5)
    parser.add_argument('--preDispatch', help='', default='2*n_jobs')
    parser.add_argument('--randomize', help='', default=False, action="store_true")
    parser.add_argument('--clearCache', default=False, action="store_true")
    options = parser.parse_args()
    
    curvePoint(options.features, options.classes, options.meta, options.output, options.cutoff,
            classifier=options.classifier, classifierArgs=options.classifierArgs,
            verbose=options.verbose, parallel=options.parallel, metric=options.metric,
            getCV=options.iteratorCV,numFolds=options.numFolds,preDispatch=options.preDispatch, 
            randomize=options.randomize)