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

def process(database, meta, resultDir, cutoff=30, verbose=3, parallel=1, preDispatch='2*n_jobs', randomize=False):
    if isinstance(meta, basestring):
        meta = result.getMeta(meta)
    
    baseResultPath = None
    if resultDir != None:
        if os.path.exists(resultDir):
            shutil.rmtree(resultDir)
        os.makedirs(resultDir)
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
    results = []
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
            hiddenResults = curvePoint(baseXPath, baseYPath, baseMetaPath, featureSet, pointResultPath, 
                       classifier=classifier, classifierArgs=params, getCV=eval(cls["cv"]),
                       numFolds=cls["folds"], verbose=verbose, parallel=parallel,
                       preDispatch=preDispatch, randomize=randomize, metric=cls["metric"])[3]
            results.append(hiddenResults)
        count += 1
        if count > cutoff:
            break
    
    if resultDir != None:
        f = open(os.path.join(resultDir, "results.json"), "wt")
        json.dump(results, f, indent=4)
        f.close()   
    return results

def curvePoint(XPath, yPath, metaPath, featureSet, resultPath, classifier, classifierArgs, getCV, numFolds, verbose, parallel, preDispatch, randomize, metric):
    meta, results, extras, hiddenResults, hiddenDetails = learn.test(
        XPath, yPath, metaPath, resultPath, 
        classifier=classifier, classifierArgs=classifierArgs, getCV=getCV, 
        numFolds=numFolds, verbose=verbose, parallel=parallel, preDispatch=preDispatch, 
        randomize=randomize, analyzeResults=False, 
        metric=metric, useFeatures=featureSet)
    return [meta, results, extras, hiddenResults, hiddenDetails]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Learning with examples')
    parser.add_argument('-b','--database', help='Database location', default=settings.DB_PATH)
    parser.add_argument('-r', '--result', help='Output directory', default=None)
    parser.add_argument('-i','--input', help='Input directory', default=None)
    parser.add_argument('-f','--inputFilter', help='Input directory filter', default=None)
    parser.add_argument('-m','--meta', help='Metadata input file name', default=None)
    parser.add_argument('--cutoff', help='Number of features to test', type=int, default=30)
    parser.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
    parser.add_argument('-p', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    parser.add_argument('--preDispatch', help='', default='2*n_jobs')
    parser.add_argument('--randomize', help='', default=False, action="store_true")
    parser.add_argument('--clearCache', default=False, action="store_true")
    # Batch commands
    parser.add_argument('--slurm', help='', default=False, action="store_true")
    parser.add_argument("--debug", default=False, action="store_true", dest="debug", help="Print jobs on screen")
    parser.add_argument("--dummy", default=False, action="store_true", dest="dummy", help="Don't submit jobs")
    parser.add_argument("--rerun", default=None, dest="rerun", help="Rerun jobs which have one of these states (comma-separated list)")
    parser.add_argument("-l", "--limit", default=None, type=int, dest="limit", help="Maximum number of jobs in queue/running")
    parser.add_argument("--hideFinished", default=False, action="store_true", dest="hideFinished", help="")
    parser.add_argument("--runDir", default=None, dest="runDir", help="")
    parser.add_argument("--jobDir", default="/tmp/jobs", dest="jobDir", help="")

    options = parser.parse_args()
    
    if options.inputFilter != None:
        options.inputFilter = eval(options.inputFilter)
    if options.inputFilter == None:
        options.inputFilter = {}
    options.inputFilter["classifiers"] = "ExtraTreesClassifier"
    
    if options.input != None:
        processDir(options.database, options.input, options.inputFilter, options.result, options.cutoff,
            verbose=options.verbose, parallel=options.parallel, preDispatch=options.preDispatch, randomize=options.randomize)
    else:
        process(options.database, options.meta, options.result, options.cutoff,
            verbose=options.verbose, parallel=options.parallel, preDispatch=options.preDispatch, randomize=options.randomize)