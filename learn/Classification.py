import sys, os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.example import exampleOptions, readAuto
from data.template import parseOptionString
from data.cache import getExperiment
from sklearn.cross_validation import StratifiedKFold, KFold
#from sklearn.grid_search import GridSearchCV
from skext.gridSearch import ExtendedGridSearchCV
#from skext.crossValidation import GroupedKFold
from sklearn.metrics import classification_report
from sklearn.metrics import average_precision_score, make_scorer
from collections import defaultdict
import tempfile
import data.result as result
import data.hidden as hidden
import random
import gene.analyze
import sklearn.metrics
#from rlscore_interface import RLScore
from RFEWrapper import RFEWrapper
from utils import Stream
import batch
import numpy
import data.writer

def getStratifiedKFoldCV(y, meta, numFolds=10):
    return StratifiedKFold(y, n_folds=numFolds)

def getKFoldCV(y, meta, numFolds=10):
    return KFold(y, n_folds=numFolds)

def getNoneCV(y, meta, numFolds=10):
    return None

class Classification():
    def __init__(self):
        # Data
        self.X = None
        self.y = None
        self.meta = None
        # Settings
        self.randomize = False
        self.numFolds = 10
        self.classifierName = None
        self.classifierArgs = None
        self.getCV = getStratifiedKFoldCV
        self.preDispatch = '2*n_jobs'
        self.metric = 'roc_auc'
        self.verbose = 3
        self.parallel = 1
        # Results
        self.bestIndex = None
        self.results = None
        self.extras = None
        self.hiddenResults = None
        self.hiddenDetails = None
    
    def buildExamples(self, experiment, outDir):
        experiment.writeExamples(outDir)
    
    def readExamples(self, inDir, fileStem=None, exampleIO=None):
        if fileStem == None:
            fileStem = "examples"
        # Read examples
        if exampleIO == None:
            exampleIO = data.writer.SVMLightExampleIO(os.path.join(inDir, fileStem))
        self.X, self.y = exampleIO.readFiles()
        # Read metadata
        metaPath = os.path.join(inDir, fileStem + ".meta.json")
        if os.path.exists(metaPath):
            self.meta = result.getMeta(metaPath)
    
    def _getClassifier(self):
        if self.classifierName == "RLScore":
            raise NotImplementedError()
        elif self.classifierName == "RFEWrapper":
            classifier = RFEWrapper
        else:
            classifier = importNamed(self.classifierName)
        if isinstance(self.classifierArgs, basestring):
            classifierArgs = parseOptionString(self.classifierArgs)
        print "Using classifier", self.classifierName, "with arguments", self.classifierArgs
        return classifier, classifierArgs
    
    def _getScorer(self):
        print "Using metric", self.metric
        if self.metric == "roc_auc":
            return self.metric
        try:
            metric = importNamed(self.metric)
            return make_scorer(metric)
        except Exception as e:
            print "Couldn't import named metric:", e
            return metric
    
    def _getClassDistribution(self, labels):
        counts = defaultdict(int)
        for value in labels:
            counts[value] += 1
        return dict(counts)
    
    def _getPreDispatch(self):
        if self.preDispatch.isdigit():
            return int(self.preDispatch)
        return self.preDispatch
    
    def _randomizeLabels(self):
        if self.randomize:
            classes = self.meta["classes"].values()
            self.y = numpy.asarray([random.choice(classes) for x in range(len(self.y))])
            print "Randomized class distribution = ", self._getClassDistribution(self.y)
                
    def classify(self, resultPath):
        if "classes" in self.meta:
            print "Class distribution = ", self._getClassDistribution(self.y)
            if self.randomize:
                self._randomizeLabels()
        X_train, X_hidden, y_train, y_hidden = hidden.split(self.X, self.y, meta=self.meta)
        print "Sizes", [X_train.shape[0], y_train.shape[0]], [X_hidden.shape[0], y_hidden.shape[0]]
        if "classes" in self.meta:
            print "Classes y_train = ", self._getClassDistribution(y_train)
            print "Classes y_hidden = ", self._getClassDistribution(y_hidden)
        
        print "Cross-validating for", self.numFolds, "folds"
        print "Args", self.classifierArgs
        cv = self.getCV(y_train, self.meta, numFolds=self.numFolds)
        scorer = self._getScorer()
        search = ExtendedGridSearchCV(classifier(), classifierArgs, refit=X_hidden.shape[0] > 0, cv=cv, scoring=scorer, verbose=self.verbose, n_jobs=self.parallel, pre_dispatch=self.getPreDispatch())
        search.fit(X_train, y_train) 
        if hasattr(search, "best_estimator_"):
            print "----------------------------- Best Estimator -----------------------------------"
            print search.best_estimator_
            if hasattr(search.best_estimator_, "doRFE"):
                print "*** RFE ***"
                search.best_estimator_.doRFE(X_train, y_train)
        #print "--------------------------------------------------------------------------------"
        print "---------------------- Grid scores on development set --------------------------"
        self.results = []
        self.extras = None
        index = 0
        self.bestIndex = 0
        for params, mean_score, scores in search.grid_scores_:
            print scores
            print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
            self.results.append({"classifier":classifier.__name__, "cv":cv.__class__.__name__, "folds":self.numFolds,
                       "metric":self.metric,"scores":list(scores), 
                       "mean":float(mean_score), "std":float(scores.std() / 2), "params":params})
            if index == 0 or float(mean_score) > self.results[self.bestIndex]["mean"]:
                self.bestIndex = index
                if hasattr(search, "extras_"):
                    print "EXTRAS"
                    self.extras = search.extras_[index]
                else:
                    print "NO_EXTRAS"
            index += 1
        print "---------------------- Best scores on development set --------------------------"
        params, mean_score, scores = search.grid_scores_[self.bestIndex]
        print scores
        print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
        self.hiddenResults = None
        self.hiddenDetails = None
        if X_hidden.shape[0] > 0:
            print "----------------------------- Classifying Hidden Set -----------------------------------"
            print "search.scoring", search.scoring
            print "search.scorer_", search.scorer_
            print "search.best_estimator_.score", search.best_estimator_.score
            print search.scorer_(search.best_estimator_, X_hidden, y_hidden)
            y_hidden_score = search.predict_proba(X_hidden)
            y_hidden_score = [x[1] for x in y_hidden_score]
            print "AUC", sklearn.metrics.roc_auc_score(y_hidden, y_hidden_score)
            self.hiddenResults = {"classifier":search.best_estimator_.__class__.__name__, 
                             #"score":scorer.score(search.best_estimator_, X_hidden, y_hidden),
                             "score":search.score(X_hidden, y_hidden),
                             "metric":self.metric,
                             "params":search.best_params_}
            print "Score =", self.hiddenResults["score"], "(" + self.metric + ")"
            y_hidden_pred = [list(x) for x in search.predict_proba(X_hidden)]
            #print y_hidden_pred
            #print search.predict_proba(X_hidden)
            self.hiddenDetails = {"predictions":{i:x for i,x in enumerate(y_hidden_pred)}}
            if hasattr(search.best_estimator_, "feature_importances_"):
                self.hiddenDetails["importances"] = search.best_estimator_.feature_importances_
            try:
                #print y_hidden
                #print y_hidden_pred
                print classification_report(y_hidden, y_hidden_pred)
            except ValueError, e:
                print "ValueError in classification_report:", e
        print "--------------------------------------------------------------------------------"
        if resultPath != None:
            saveResults(resultPath)
        return self.meta
    
    def _saveResults(self, resultPath, details=True):
        if self.extras == None:
            print "No detailed information for cross-validation"
            return
        if not os.path.exists(os.path.dirname(resultPath)):
            os.makedirs(os.path.dirname(resultPath))
        self.meta = result.getMeta(self.meta)
        # Add general results
        self.meta["results"] = {"best":self.results[self.bestIndex], "all":self.results}
        if self.hiddenResults != None:
            self.meta["results"]["hidden"] = self.hiddenResults
        # Insert detailed results
        if details:
            featureByIndex = result.getFeaturesByIndex(self.meta)
            if self.hiddenDetails != None:
                saveDetails(self.meta, self.hiddenDetails.get("predictions", None), self.hiddenDetails.get("importances", None), "hidden", featureByIndex)
            fold = 0
            for extra in self.extras:
                saveDetails(self.meta, extra.get("predictions", None), extra.get("importances", None), fold, featureByIndex)
                fold += 1
        else:
            if "examples" in self.meta:
                del self.meta["examples"]
            if "features" in self.meta:
                del self.meta["features"]
                
        # Save results
        if resultPath != None:
            result.saveMeta(self.meta, resultPath)

    def _saveDetails(self, meta, predictions, importances, fold, featureByIndex=None):
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
                    else:
                        result.setValue(feature, "hidden-importance", importances[i])
                        result.setValue(feature, "sort", importances[i])


def checkSets(X, y, X_train, X_hidden, y_train, y_hidden, meta):
    trainIndex = 0
    hiddenIndex = 0
    for index, example in enumerate(meta["examples"]): 
        if example.get("set", None) == 'hidden':
            print "hidden", (index, y[index]), (hiddenIndex, y_hidden[hiddenIndex])
            assert y[index] == y_hidden[hiddenIndex], (y[index], y_hidden[trainIndex], index, hiddenIndex, example)
            #assert X[index] == X_hidden[hiddenIndex]
            hiddenIndex += 1
        else:
            print "train", (index, y[index]), (trainIndex, y_train[trainIndex])
            assert y[index] == y_train[trainIndex], (y[index], y_hidden[trainIndex], index, trainIndex, example)
            #assert X[index] == X_hidden[trainIndex]
            trainIndex += 1

def checkExamples(meta):
    hidden = {}
    train = {}
    for index, example in enumerate(meta["examples"]):
        if example.get("set", None) == 'hidden':
            group = hidden
        else:
            group = train
        if example["project_code"] not in group:
            group[example["project_code"]] = {"-1":0, "1":0}
        group[example["project_code"]][example["label"]] += 1
    print "Examples hidden", hidden
    print "Examples train", train

def test(XPath, yPath, metaPath, resultPath, classifier, classifierArgs, 
         getCV=getStratifiedKFoldCV, numFolds=10, verbose=3, parallel=1, 
         preDispatch='2*n_jobs', randomize=False, analyzeResults=False,
         databaseCGI=None, metric="roc_auc", useFeatures=None, reclassify=False, details=True):
    X, y = readAuto(XPath, yPath, useFeatures=useFeatures)
    meta = {}
    if metaPath != None:
        meta = result.getMeta(metaPath)
    if "classes" in meta:
        print "Class distribution = ", getClassDistribution(y)
        if randomize:
            classes = meta["classes"].values()
            y = numpy.asarray([random.choice(classes) for x in range(len(y))])
            print "Randomized class distribution = ", getClassDistribution(y)
    X_train, X_hidden, y_train, y_hidden = hidden.split(X, y, meta=meta)
    print "Sizes", [X_train.shape[0], y_train.shape[0]], [X_hidden.shape[0], y_hidden.shape[0]]
    if "classes" in meta:
        print "Classes y_train = ", getClassDistribution(y_train)
        print "Classes y_hidden = ", getClassDistribution(y_hidden)
    #checkSets(X, y, X_train, X_hidden, y_train, y_hidden, meta)
    #checkExamples(meta)
    
    print "Cross-validating for", numFolds, "folds"
    print "Args", classifierArgs
    cv = getCV(y_train, meta, numFolds=numFolds)
    if preDispatch.isdigit():
        preDispatch = int(preDispatch)
    scorer = getScorer(metric)
    search = ExtendedGridSearchCV(classifier(), classifierArgs, refit=X_hidden.shape[0] > 0, cv=cv, scoring=scorer, verbose=verbose, n_jobs=parallel, pre_dispatch=preDispatch)
    search.fit(X_train, y_train) 
    if hasattr(search, "best_estimator_"):
        print "----------------------------- Best Estimator -----------------------------------"
        print search.best_estimator_
        if hasattr(search.best_estimator_, "doRFE"):
            print "*** RFE ***"
            search.best_estimator_.doRFE(X_train, y_train)
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
                print "EXTRAS"
                extras = search.extras_[index]
            else:
                print "NO_EXTRAS"
        index += 1
    print "---------------------- Best scores on development set --------------------------"
    params, mean_score, scores = search.grid_scores_[bestIndex]
    print scores
    print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
    hiddenResults = None
    hiddenDetails = None
    if X_hidden.shape[0] > 0:
        print "----------------------------- Classifying Hidden Set -----------------------------------"
        print "search.scoring", search.scoring
        print "search.scorer_", search.scorer_
        print "search.best_estimator_.score", search.best_estimator_.score
        print search.scorer_(search.best_estimator_, X_hidden, y_hidden)
        y_hidden_score = search.predict_proba(X_hidden)
        y_hidden_score = [x[1] for x in y_hidden_score]
        print "AUC", sklearn.metrics.roc_auc_score(y_hidden, y_hidden_score)
        hiddenResults = {"classifier":search.best_estimator_.__class__.__name__, 
                         #"score":scorer.score(search.best_estimator_, X_hidden, y_hidden),
                         "score":search.score(X_hidden, y_hidden),
                         "metric":metric,
                         "params":search.best_params_}
        print "Score =", hiddenResults["score"], "(" + metric + ")"
        y_hidden_pred = [list(x) for x in search.predict_proba(X_hidden)]
        #print y_hidden_pred
        #print search.predict_proba(X_hidden)
        hiddenDetails = {"predictions":{i:x for i,x in enumerate(y_hidden_pred)}}
        if hasattr(search.best_estimator_, "feature_importances_"):
            hiddenDetails["importances"] = search.best_estimator_.feature_importances_
        try:
            #print y_hidden
            #print y_hidden_pred
            print classification_report(y_hidden, y_hidden_pred)
        except ValueError, e:
            print "ValueError in classification_report:", e
    print "--------------------------------------------------------------------------------"
    if resultPath != None:
        saveResults(meta, resultPath, results, extras, bestIndex, analyzeResults, hiddenResults, hiddenDetails, databaseCGI=databaseCGI, reclassify=reclassify, details=details)
    return meta, results, extras, hiddenResults, hiddenDetails

def saveDetails(meta, predictions, importances, fold, featureByIndex=None, reclassify=False):
    if featureByIndex == None:
        featureByIndex = result.getFeaturesByIndex(meta)
    if predictions != None:
        for index in predictions:
            if fold == "hidden":
                example = result.getExampleFromSet(meta, index, "hidden")
            else:
                example = result.getExampleFromSet(meta, index, "train")
            if reclassify and ("classification" in example):
                del example["classification"]
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
                
def saveResults(meta, resultPath, results, extras, bestIndex, analyze, hiddenResults=None, hiddenDetails=None, databaseCGI=None, reclassify=False, details=True):
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
    if details:
        featureByIndex = result.getFeaturesByIndex(meta)
        if hiddenDetails != None:
            saveDetails(meta, hiddenDetails.get("predictions", None), hiddenDetails.get("importances", None), "hidden", featureByIndex, reclassify=reclassify)
        fold = 0
        for extra in extras:
            saveDetails(meta, extra.get("predictions", None), extra.get("importances", None), fold, featureByIndex, reclassify=reclassify)
            fold += 1
    else:
        if "examples" in meta:
            del meta["examples"]
        if "features" in meta:
            del meta["features"]
    
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
        #classifier = RLScore
        raise NotImplementedError()
    elif classifierName == "RFEWrapper":
        classifier = RFEWrapper
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
    try:
        metric = importNamed(metric)
        return make_scorer(metric)
    except Exception as e:
        print "Couldn't import named metric:", e
        return metric
    
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
    parser.add_argument('--buildOnly', default=False, action="store_true")
    parser.add_argument('--batch', default=False, action="store_true")
    parser.add_argument('--dummy', default=False, action="store_true")
    parser.add_argument('--hiddenFilter', default=None)
    options = parser.parse_args()
    
    if options.hiddenFilter != None:
        options.hiddenFilter = options.hiddenFilter.split(",")
        hidden.hiddenFilter = options.hiddenFilter
    
    if options.batch:
        connection = batch.getConnection(options.slurm)
        if not os.path.exists(options.jobDir):
            os.makedirs(options.jobDir)
        connection.debug = True
        batch.batch(runDir, jobDir, resultPath, experiments, projects, classifiers, features, limit, sleepTime, dummy, rerun, hideFinished, clearCache, icgcDB, cgiDB, connection, metric)
    
    if options.result != None:
        Stream.openLog(options.result + "-log.txt")
    
    classifier, classifierArgs = getClassifier(options.classifier, options.classifierArguments)
    cvFunction = eval(options.iteratorCV)
    featureFilePath, labelFilePath, metaFilePath = getExperiment(experiment=options.experiment, experimentOptions=options.options, 
                                                                 database=options.database, writer=options.writer, 
                                                                 useCached=not options.noCache, featureFilePath=options.features, 
                                                                 labelFilePath=options.labels, metaFilePath=options.meta,
                                                                 cacheDir=options.cacheDir)
    if options.buildOnly:
        sys.exit()
    test(featureFilePath, labelFilePath, metaFilePath, classifier=classifier, classifierArgs=classifierArgs, 
         getCV=cvFunction, numFolds=options.numFolds, verbose=options.verbose, parallel=options.parallel, 
         preDispatch=options.preDispatch, resultPath=options.result, randomize=options.randomize, analyzeResults=options.analyze, databaseCGI=options.databaseCGI, metric=options.metric)
    if options.clearCache:
        print "Removing cache files"
        for filename in [featureFilePath, labelFilePath, metaFilePath]:
            if os.path.exists(filename):
                os.remove(filename)