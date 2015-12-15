import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#from data.template import parseOptionString
from sklearn.cross_validation import StratifiedKFold, KFold
#from sklearn.grid_search import GridSearchCV
from skext.gridSearch import ExtendedGridSearchCV
#from skext.crossValidation import GroupedKFold
from sklearn.metrics import classification_report
from sklearn.metrics import average_precision_score, make_scorer
from collections import defaultdict
import data.hidden as hidden
import random
import sklearn.metrics
#from rlscore_interface import RLScore
#from RFEWrapper import RFEWrapper
import numpy
#import data.writer
from ExampleIO import SVMLightExampleIO
#import settings
from Meta import Meta

def getStratifiedKFoldCV(y, meta, numFolds=10):
    return StratifiedKFold(y, n_folds=numFolds)

def getKFoldCV(y, meta, numFolds=10):
    return KFold(y, n_folds=numFolds)

def getNoneCV(y, meta, numFolds=10):
    return None

class Classification():
    def __init__(self, classifierName, classifierArgs, numFolds=10, parallel=1, metric='roc_auc', getCV=None, preDispatch='2*n_jobs', classifyHidden=False):
        # Data
        self.X = None
        self.y = None
        self.meta = None
        self.exampleMeta = None
        # Settings
        self.randomize = False
        self.numFolds = numFolds
        self.classifierName = None
        self.classifierArgs = None
        if getCV == None:
            getCV = getStratifiedKFoldCV
        self.getCV = getCV
        self.preDispatch = preDispatch
        self.metric = metric
        self.verbose = 3
        self.parallel = parallel
        self.classifyHidden = classifyHidden
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
            exampleIO = SVMLightExampleIO(os.path.join(inDir, fileStem))
        self.X, self.y = exampleIO.readFiles()
        # Read metadata
        self.meta = Meta(os.path.join(inDir, fileStem + ".classification.sqlite"), copyFrom=os.path.join(inDir, fileStem + ".meta.sqlite"), clear=True)
        self.exampleMeta = self.meta.db["example"].all()
    
    def _getClassifier(self):
        if self.classifierName == "RLScore":
            raise NotImplementedError()
        #elif self.classifierName == "RFEWrapper":
        #    classifier = RFEWrapper
        else:
            classifier = self._importNamed(self.classifierName)
        classifierArgs = self._getClassifierArgs()
        print "Using classifier", classifier.__name__, "with arguments", classifierArgs
        return classifier, classifierArgs
    
    def _getClassifierArgs(self):
        if not isinstance(self.classifierArgs, basestring): # already in parsed form
            return self.classifierArgs
        if self.classifierArgs == None:
            return {}
        # Separate key and values into a list, allowing commas within values
        splits = []
        equalSignSplits = self.classifierArgs.split("=")
        for i in range(len(equalSignSplits)):
            if i < len(equalSignSplits) - 1: # potentially a "value,key2" structure from the middle of a string like "key1=value,key2=value2"
                splits.extend(equalSignSplits[i].rsplit(",", 1))
            else:
                splits.append(equalSignSplits[i])
        options = {}
        for key, value in zip(*[iter(splits)] * 2):
            try:
                options[key] = eval(value, globals()) #, {x:getattr(settings, x) for x in dir(settings)})
            except:
                options[key] = value
        return options
    
    def _getScorer(self):
        print "Using metric", self.metric
        if self.metric == "roc_auc":
            return self.metric
        try:
            metric = self._importNamed(self.metric)
            return make_scorer(metric)
        except Exception as e:
            print "Couldn't import named metric:", e
            return metric
    
    def _importNamed(self, name):
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
        if "class" in self.meta.db.tables:
            print "Class distribution = ", self._getClassDistribution(self.y)
            if self.randomize:
                self._randomizeLabels()
        X_train, X_hidden, y_train, y_hidden = hidden.split(self.X, self.y, meta=self.exampleMeta)
        print "Sizes", [X_train.shape[0], y_train.shape[0]], [X_hidden.shape[0], y_hidden.shape[0]]
        if "class" in self.meta.db.tables:
            print "Classes y_train = ", self._getClassDistribution(y_train)
            print "Classes y_hidden = ", self._getClassDistribution(y_hidden)
        
        search = self._crossValidate(y_train, X_train, self.classifyHidden and (X_hidden.shape[0] > 0))
        if self.classifyHidden:
            self._predictHidden(y_hidden, X_hidden, search)
        self._saveResults(resultPath)
        
    def _crossValidate(self, y_train, X_train, refit=False):
        print "Cross-validating for", self.numFolds, "folds"
        print "Args", self.classifierArgs
        cv = StratifiedKFold(y_train, n_folds=self.numFolds) #self.getCV(y_train, self.meta.meta, numFolds=self.numFolds)
        scorer = self._getScorer()
        classifier, classifierArgs = self._getClassifier()
        search = ExtendedGridSearchCV(classifier(), classifierArgs, refit=refit, cv=cv, scoring=scorer, verbose=self.verbose, n_jobs=self.parallel, pre_dispatch=self._getPreDispatch())
        search.fit(X_train, y_train)
        if hasattr(search, "best_estimator_"):
            print "----------------------------- Best Estimator -----------------------------------"
            print search.best_estimator_
            if hasattr(search.best_estimator_, "doRFE"):
                print "*** RFE ***"
                search.best_estimator_.doRFE(X_train, y_train)
        print "---------------------- Grid scores on development set --------------------------"
        self.results = []
        self.extras = None
        index = 0
        self.bestIndex = 0
        for params, mean_score, scores in search.grid_scores_:
            print scores
            print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
            self.results.append({"classifier":classifier.__name__, "cv":cv.__class__.__name__, "folds":self.numFolds,
                       "metric":self.metric, "score":None, "scores":",".join(list(scores)), 
                       "mean":float(mean_score), "std":float(scores.std() / 2), "params":params, "set":"train"})
            if index == 0 or float(mean_score) > self.results[self.bestIndex]["mean"]:
                self.bestIndex = index
                if hasattr(search, "extras_"):
                    print "EXTRAS"
                    self.extras = search.extras_[index]
                else:
                    print "NO_EXTRAS"
            index += 1
        self.meta.insert_many("result", self.results)
        print "---------------------- Best scores on development set --------------------------"
        params, mean_score, scores = search.grid_scores_[self.bestIndex]
        print scores
        print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
        return search
        
    def _predictHidden(self, y_hidden, X_hidden, search):
        self.hiddenResult = None
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
            self.hiddenResult = {"classifier":search.best_estimator_.__class__.__name__, 
                             #"score":scorer.score(search.best_estimator_, X_hidden, y_hidden),
                             "score":search.score(X_hidden, y_hidden),
                             "metric":self.metric,
                             "params":search.best_params_,
                             "set":"hidden"}
            self.meta.insert("result", self.hiddenResult)
            print "Score =", self.hiddenResult["score"], "(" + self.metric + ")"
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
    
    def _saveResults(self, resultPath, details=True):
        if resultPath == None:
            print "Results not saved"
            return
        if self.extras == None:
            print "No detailed information for cross-validation"
            return
        if not os.path.exists(os.path.dirname(resultPath)):
            os.makedirs(os.path.dirname(resultPath))
        # Add general results
        #self.meta["results"] = {"best":self.results[self.bestIndex], "all":self.results}
        #if self.hiddenResults != None:
        #    self.meta["results"]["hidden"] = self.hiddenResults
        for result in self.results:
            self.meta.insert("result", result)
        if self.hiddenResult != None:
            self.meta.insert("result", self.hiddenResult)
        # Insert detailed results
        if details:
            featureByIndex = self.meta.getFeaturesByIndex()
            if self.hiddenDetails != None:
                self._saveDetails(self.hiddenDetails.get("predictions", None), self.hiddenDetails.get("importances", None), "hidden", featureByIndex)
            fold = 0
            for extra in self.extras:
                self._saveDetails(extra.get("predictions", None), extra.get("importances", None), fold, featureByIndex)
                fold += 1
#         else:
#             self.meta.remove("examples")
#             self.meta.remove("features")
                
        # Save results
        if resultPath != None:
            self.meta.write(resultPath)

    def _saveDetails(self, predictions, importances, fold, featureByIndex=None):
        if featureByIndex == None:
            featureByIndex = self.meta.getFeaturesByIndex()
        if predictions != None:
            for index in predictions:
                if fold == "hidden":
                    example = self.meta.getExampleFromSet(index, "hidden")
                else:
                    example = self.meta.getExampleFromSet(index, "train")
                if "classification" in example:
                    raise Exception("Example " + str(index) + " has already been classified " + str([fold, str(example)]))
                self._setValue(example, "prediction", predictions[index], "classification")
                self._setValue(example, "fold", fold, "classification")
        if importances != None:
            for i in range(len(importances)):
                if importances[i] != 0:
                    feature = self.meta.getFeature(i, featureByIndex)
                    if fold != "hidden":
                        self._setValue(feature, fold, importances[i], "importances")
                    else:
                        self._setValue(feature, "hidden-importance", importances[i])
                        self._setValue(feature, "sort", importances[i])
    
    def _setValue(self, target, key, value, parent=None):
        if parent != None:
            if not parent in target:
                target[parent] = {}
            target = target[parent]
        target[key] = value
    
# if __name__ == "__main__":
#     import argparse
#     parser = argparse.ArgumentParser(parents=[exampleOptions], description='Learning with examples')
#     parser.add_argument('-x','--features', help='Input file for feature vectors (X)', default=None)
#     parser.add_argument('-y','--labels', help='Input file for class labels (Y)', default=None)
#     parser.add_argument('-m','--meta', help='Metadata input file name (optional)', default=None)
#     parser.add_argument('--noCache', help='Do not use cache', default=False, action="store_true")
#     parser.add_argument('--cacheDir', help='Cache directory, used if x, y or m are undefined (optional)', default=os.path.join(tempfile.gettempdir(), "CAMDA2014"))
#     parser.add_argument('-c','--classifier', help='', default='ensemble.RandomForestClassifier')
#     parser.add_argument('-a','--classifierArguments', help='', default=None)
#     parser.add_argument('--metric', help='', default="roc_auc")
#     parser.add_argument('-i','--iteratorCV', help='', default='getStratifiedKFoldCV')
#     parser.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=5)
#     parser.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
#     parser.add_argument('-p', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
#     parser.add_argument('--preDispatch', help='', default='2*n_jobs')
#     parser.add_argument('-r', '--result', help='Output file for detailed results (optional)', default=None)
#     parser.add_argument('--randomize', help='', default=False, action="store_true")
#     parser.add_argument('--analyze', help='Analyze feature selection results', default=False, action="store_true")
#     parser.add_argument('--databaseCGI', help='Analysis database', default=None)
#     parser.add_argument('--clearCache', default=False, action="store_true")
#     parser.add_argument('--buildOnly', default=False, action="store_true")
#     parser.add_argument('--batch', default=False, action="store_true")
#     parser.add_argument('--dummy', default=False, action="store_true")
#     parser.add_argument('--hiddenFilter', default=None)
#     options = parser.parse_args()
    
#     if options.hiddenFilter != None:
#         options.hiddenFilter = options.hiddenFilter.split(",")
#         hidden.hiddenFilter = options.hiddenFilter
#     
#     if options.batch:
#         connection = batch.getConnection(options.slurm)
#         if not os.path.exists(options.jobDir):
#             os.makedirs(options.jobDir)
#         connection.debug = True
#         batch.batch(runDir, jobDir, resultPath, experiments, projects, classifiers, features, limit, sleepTime, dummy, rerun, hideFinished, clearCache, icgcDB, cgiDB, connection, metric)
#     
#     if options.result != None:
#         Stream.openLog(options.result + "-log.txt")
#     
#     classifier, classifierArgs = getClassifier(options.classifier, options.classifierArguments)
#     cvFunction = eval(options.iteratorCV)
#     featureFilePath, labelFilePath, metaFilePath = getExperiment(experiment=options.experiment, experimentOptions=options.options, 
#                                                                  database=options.database, writer=options.writer, 
#                                                                  useCached=not options.noCache, featureFilePath=options.features, 
#                                                                  labelFilePath=options.labels, metaFilePath=options.meta,
#                                                                  cacheDir=options.cacheDir)
#     if options.buildOnly:
#         sys.exit()
#     test(featureFilePath, labelFilePath, metaFilePath, classifier=classifier, classifierArgs=classifierArgs, 
#          getCV=cvFunction, numFolds=options.numFolds, verbose=options.verbose, parallel=options.parallel, 
#          preDispatch=options.preDispatch, resultPath=options.result, randomize=options.randomize, analyzeResults=options.analyze, databaseCGI=options.databaseCGI, metric=options.metric)
#     if options.clearCache:
#         print "Removing cache files"
#         for filename in [featureFilePath, labelFilePath, metaFilePath]:
#             if os.path.exists(filename):
#                 os.remove(filename)