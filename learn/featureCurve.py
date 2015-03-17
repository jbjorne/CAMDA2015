import sys, os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import result, cache
import learn
from learn import getStratifiedKFoldCV as StratifiedKFold
import sklearn
import settings

def process(database, templateMetaPath, resultDir, cutoff=30, verbose=3, parallel=1, 
         preDispatch='2*n_jobs', randomize=False):
    meta = result.getMeta(templateMetaPath)
    
    baseResultPath = None
    if resultDir != None:
        baseResultPath = os.path.join(resultDir, "base.json")
    baseXPath, baseYPath, baseMetaPath = cache.getExperiment(
         experiment=meta["experiment"]["name"], experimentOptions=meta["experiment"]["options"], 
         database=database, writer="writeNumpyText", useCached=True, metaFilePath=baseResultPath)

    features = meta["features"]
    count = 0
    featureSet = []
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
    for featureName in features:
        feature = features[featureName]
        print "Processing feature", featureName
        print feature
        featureSet.append(feature["id"])
        pointResultPath = None
        if resultDir != None:
            pointResultPath = os.path.join(resultDir, "feature-" + str(feature["rank"]) + ".json")
        print "Feature set", featureSet
        if len(featureSet) > 1:
            curvePoint(baseXPath, baseYPath, baseMetaPath, featureSet, pointResultPath, 
                       classifier=classifier, classifierArgs=params, getCV=eval(cls["cv"]),
                       numFolds=cls["folds"], verbose=verbose, parallel=parallel,
                       preDispatch=preDispatch, randomize=randomize, metric=cls["metric"])
        count += 1
        if count > cutoff:
            break
    

def curvePoint(XPath, yPath, metaPath, featureSet, resultPath, classifier, classifierArgs, getCV, numFolds, verbose, parallel, preDispatch, randomize, metric):
    learn.test(XPath, yPath, metaPath, resultPath, 
               classifier=classifier, classifierArgs=classifierArgs, getCV=getCV, 
               numFolds=numFolds, verbose=verbose, parallel=parallel, preDispatch=preDispatch, 
               randomize=randomize, analyzeResults=False, 
               metric=metric, useFeatures=featureSet)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Learning with examples')
    parser.add_argument('-b','--database', help='Database location', default=settings.DB_PATH)
    parser.add_argument('-r', '--result', help='Output directory', default=None)
    parser.add_argument('-m','--meta', help='Metadata input file name (optional)', default=None)
    parser.add_argument('--cutoff', help='Number of features to test', type=int, default=30)
    parser.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
    parser.add_argument('-p', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    parser.add_argument('--preDispatch', help='', default='2*n_jobs')
    parser.add_argument('--randomize', help='', default=False, action="store_true")
    parser.add_argument('--clearCache', default=False, action="store_true")
    options = parser.parse_args()
    
    process(options.database, options.meta, options.result, options.cutoff,
        verbose=options.verbose, 
        parallel=options.parallel, 
        preDispatch=options.preDispatch, 
        randomize=options.randomize)
