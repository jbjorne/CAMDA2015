import sys, os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.example import exampleOptions, readAuto
from data.template import parseOptionString
from data.cache import getExperiment
from sklearn.cross_validation import StratifiedKFold
#from sklearn.grid_search import GridSearchCV
from skext.gridSearch import ExtendedGridSearchCV
from skext.crossValidation import GroupedKFold
from sklearn.metrics import classification_report
from sklearn.metrics import average_precision_score, make_scorer
from collections import defaultdict
import tempfile
import data.result as result
import data.hidden as hidden
import random
import gene.analyze
from rlscore_interface import RLScore

def getClassDistribution(y):
    counts = defaultdict(int)
    for value in y:
        counts[value] += 1
    return dict(counts)
    #bincount = numpy.nonzero(numpy.bincount(y))[0]
    #return zip(bincount,y[bincount])

def getDonorCV(y, meta, numFolds=10):
    groups = []
    examples = meta["meta"]
    for i in range(len(examples)):
        groups.append(examples[i]["icgc_donor_id"])
    if not len(groups) == len(y):
        raise Exception("Metadata example count differs from y: " + str((len(examples), len(y))))
    return GroupedKFold(groups, n_folds=numFolds, shuffle=True)

def getStratifiedKFoldCV(y, meta, numFolds=10):
    return StratifiedKFold(y, n_folds=numFolds)

def test(XPath, yPath, metaPath, resultPath, classifier, classifierArgs, 
         getCV=getStratifiedKFoldCV, numFolds=10, verbose=3, parallel=1, 
         preDispatch='2*n_jobs', randomize=False, analyzeResults=False,
         databaseCGI=None, metric="roc_auc", useFeatures=None):
    X, y = readAuto(XPath, yPath, useFeatures=useFeatures)
    meta = {}
    if metaPath != None:
        meta = result.getMeta(metaPath)
    if "classes" in meta:
        print "Class distribution = ", getClassDistribution(y)
        if randomize:
            classes = meta["classes"].values()
            y = [random.choice(classes) for x in range(len(y))]
            print "Class distribution = ", getClassDistribution(y)
    X_train, X_hidden, y_train, y_hidden = hidden.split(X, y, meta=meta)

    print "Cross-validating for", numFolds, "folds"
    print "Args", classifierArgs
    cv = getCV(y_train, meta, numFolds=numFolds)
    if preDispatch.isdigit():
        preDispatch = int(preDispatch)
    scorer = getScorer(metric)
    search = ExtendedGridSearchCV(classifier(), [classifierArgs], refit=len(X_hidden) > 0, cv=cv, scoring=scorer, verbose=verbose, n_jobs=parallel, pre_dispatch=preDispatch)
    search.fit(X_train, y_train) 
    if hasattr(search, "best_estimator_"):
        print "----------------------------- Best Estimator -----------------------------------"
        print search.best_estimator_
    #print "--------------------------------------------------------------------------------"
    print "---------------------- Grid scores on development set --------------------------"
    results = []
    extras = None
    index = 0
    bestIndex = 0
    for params, mean_score, scores in search.grid_scores_:
        print scores
        print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
        results.append({"classifier":classifier.__name__, "cv":cv.__class__.__name__, "folds":numFolds,
                   "metric":metric,"scores":list(scores), 
                   "mean":float(mean_score), "std":float(scores.std() / 2), "params":params})
        if index == 0 or float(mean_score) > results[bestIndex]["mean"]:
            bestIndex = index
            if hasattr(search, "extras_"):
                extras = search.extras_[index]
        index += 1
    print "---------------------- Best scores on development set --------------------------"
    params, mean_score, scores = search.grid_scores_[bestIndex]
    print scores
    print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
    hiddenResults = None
    hiddenDetails = None
    if len(X_hidden) > 0:
        print "----------------------------- Classifying Hidden Set -----------------------------------"
        hiddenResults = {"classifier":search.best_estimator_.__class__.__name__, 
                         "score":search.score(X_hidden, y_hidden),
                         "metric":metric,
                         "params":search.best_params_}
        print "Score =", hiddenResults["score"], "(" + metric + ")"
        y_hidden_pred = search.predict(X_hidden)
        #print y_hidden_pred
        #print search.predict_proba(X_hidden)
        hiddenDetails = {"predictions":{i:x for i,x in enumerate(y_hidden_pred)}}
        if hasattr(search.best_estimator_, "feature_importances_"):
            hiddenDetails["importances"] = search.best_estimator_.feature_importances_
        try:
            print classification_report(y_hidden, y_hidden_pred)
        except ValueError, e:
            print "ValueError in classification_report:", e
    print "--------------------------------------------------------------------------------"
    if resultPath != None:
        saveResults(meta, resultPath, results, extras, bestIndex, analyzeResults, hiddenResults, hiddenDetails, databaseCGI=databaseCGI)

def saveDetails(meta, predictions, importances, fold, featureByIndex=None):
    if featureByIndex == None:
        featureByIndex = result.getFeaturesByIndex(meta)
    if predictions != None:
        for index in predictions:
            if fold == "hidden":
                example = result.getExampleFromSet(meta, index, "hidden")
            else:
                example = result.getExampleFromSet(meta, index, "train")
            if "classification" in example:
                raise Exception("Example " + str(index) + " has already been classified " + str([fold, str(example)]))
            result.setValue(example, "prediction", predictions[index], "classification")
            result.setValue(example, "fold", fold, "classification")
    if importances != None:
        for i in range(len(importances)):
            if importances[i] != 0:
                feature = result.getFeature(meta, i, featureByIndex)
                if fold != "hidden":
                    result.setValue(feature, fold, importances[i], "importances")
                    #if "sort" not in feature:
                    #    result.setValue(feature, "sort", 0)
                else:
                    result.setValue(feature, "hidden-importance", importances[i])
                    result.setValue(feature, "sort", importances[i])
                #if "importances" in feature:
                #    result.setValue(feature, "sort", sum(feature["importances"].values()) / len(feature["importances"]))
                #else:
                #    result.setValue(feature, "sort", 0)
                
def saveResults(meta, resultPath, results, extras, bestIndex, analyze, hiddenResults=None, hiddenDetails=None, databaseCGI=None):
    if extras == None:
        print "No detailed information for cross-validation"
        return
    if not os.path.exists(os.path.dirname(resultPath)):
        os.makedirs(os.path.dirname(resultPath))
    meta = result.getMeta(meta)
    # Add general results
    meta["results"] = {"best":results[bestIndex], "all":results}
    if hiddenResults != None:
        meta["results"]["hidden"] = hiddenResults
    # Insert detailed results
    featureByIndex = result.getFeaturesByIndex(meta)
    if hiddenDetails != None:
        saveDetails(meta, hiddenDetails.get("predictions", None), hiddenDetails.get("importances", None), "hidden", featureByIndex)
    fold = 0
    for extra in extras:
        saveDetails(meta, extra.get("predictions", None), extra.get("importances", None), fold, featureByIndex)
        fold += 1
    # Analyze results
    if analyze:
        print "Analyzing results"
        meta = gene.analyze.analyze(meta, databaseCGI)              
    # Save results
    if resultPath != None:
        result.saveMeta(meta, resultPath)

def importNamed(name):
    asName = name.rsplit(".", 1)[-1]
    imported = False
    attempts = ["from sklearn." + name.rsplit(".", 1)[0] + " import " + asName,
                "from " + name.rsplit(".", 1)[0] + " import " + asName,
                "import " + name + " as " + asName]
    for attempt in attempts:
        try:
            print "Importing '" + attempt + "', ",
            exec attempt
            imported = True
            print "OK"
            break;
        except ImportError:
            print "failed"
    if not imported:
        raise Exception("Could not import '" + name + "'")
    return eval(asName)
    
def getClassifier(classifierName, classifierArgs):
    if classifierName == "RLScore":
        classifier = RLScore
    else:
        classifier = importNamed(classifierName)
    if isinstance(classifierArgs, basestring):
        classifierArgs = parseOptionString(classifierArgs)
    print "Using classifier", classifierName, "with arguments", classifierArgs
    return classifier, classifierArgs

def getScorer(metric):
    print "Using metric", metric
    if metric == "roc_auc":
        return metric
    metric = importNamed(metric)
    return make_scorer(metric)
    
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
    parser.add_argument('--metric', help='', default="roc_auc")
    parser.add_argument('-i','--iteratorCV', help='', default='getStratifiedKFoldCV')
    parser.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=5)
    parser.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
    parser.add_argument('-p', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    parser.add_argument('--preDispatch', help='', default='2*n_jobs')
    parser.add_argument('-r', '--result', help='Output file for detailed results (optional)', default=None)
    parser.add_argument('--randomize', help='', default=False, action="store_true")
    parser.add_argument('--analyze', help='Analyze feature selection results', default=False, action="store_true")
    parser.add_argument('--databaseCGI', help='Analysis database', default=None)
    parser.add_argument('--clearCache', default=False, action="store_true")
    options = parser.parse_args()
    
    classifier, classifierArgs = getClassifier(options.classifier, options.classifierArguments)
    cvFunction = eval(options.iteratorCV)
    featureFilePath, labelFilePath, metaFilePath = getExperiment(experiment=options.experiment, experimentOptions=options.options, 
                                                                 database=options.database, writer=options.writer, 
                                                                 useCached=not options.noCache, featureFilePath=options.features, 
                                                                 labelFilePath=options.labels, metaFilePath=options.meta)
    test(featureFilePath, labelFilePath, metaFilePath, classifier=classifier, classifierArgs=classifierArgs, 
         getCV=cvFunction, numFolds=options.numFolds, verbose=options.verbose, parallel=options.parallel, 
         preDispatch=options.preDispatch, resultPath=options.result, randomize=options.randomize, analyzeResults=options.analyze, databaseCGI=options.databaseCGI, metric=options.metric)
    if options.clearCache:
        print "Removing cache files"
        for filename in [featureFilePath, labelFilePath, metaFilePath]:
            if os.path.exists(filename):
                os.remove(filename)