import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sklearn.cross_validation import StratifiedKFold
from skext.gridSearch import ExtendedGridSearchCV
from sklearn.metrics import classification_report, make_scorer
from collections import defaultdict, OrderedDict
import data.hidden as hidden
import sklearn.metrics
from ExampleIO import SVMLightExampleIO
from Meta import Meta

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

def countUnique(values):
    counts = defaultdict(int)
    for value in values:
        counts[value] += 1
    return dict(counts)
    
def getOptions(execString):
    exec(execString)
    execLocals = locals()
    execReturn = {}
    for execKey in execLocals:
        if not execKey.startswith("exec"):
            execReturn[execKey] = execLocals[execKey]
    return execReturn
        
    #return {key:locals()[key] for key in locals() if key != "execString"}

class Classification():
    def __init__(self, classifierName, classifierArgs, numFolds=10, parallel=1, metric='roc_auc', getCV=None, preDispatch='2*n_jobs', classifyHidden=False):
        # Data
        self.X = None
        self.y = None
        self.meta = None
        # Settings
        self.randomize = False
        self.numFolds = numFolds
        self.classifierName = None
        self.classifierArgs = None
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
    
    def readExamples(self, inDir, fileStem=None, exampleIO=None):
        if fileStem == None:
            fileStem = "examples"
        # Read examples
        if exampleIO == None:
            exampleIO = SVMLightExampleIO(os.path.join(inDir, fileStem))
        self.X, self.y = exampleIO.readFiles()
        # Read metadata
        self.meta = Meta(os.path.join(inDir, fileStem + ".meta.sqlite"))
    
    def _getClassifier(self):
        classifier = importNamed(self.classifierName)
        classifierArgs = getOptions(self.classifierArgs) #self._getClassifierArgs()
        print "Using classifier", classifier.__name__, "with arguments", classifierArgs
        return classifier, classifierArgs
                
    def classify(self, resultPath):
        if "class" in self.meta.db.tables:
            print "Class distribution = ", countUnique(self.y)
            if self.randomize:
                self._randomizeLabels()
        X_train, X_hidden, y_train, y_hidden = hidden.split(self.X, self.y, meta=self.meta.db["example"].all())
        print "Sizes", [X_train.shape[0], y_train.shape[0]], [X_hidden.shape[0], y_hidden.shape[0]]
        if "class" in self.meta.db.tables:
            print "Classes y_train = ", countUnique(y_train)
            print "Classes y_hidden = ", countUnique(y_hidden)
        
        search = self._crossValidate(y_train, X_train, self.classifyHidden and (X_hidden.shape[0] > 0))
        if self.classifyHidden:
            self._predictHidden(y_hidden, X_hidden, search)
        self._saveResults(resultPath)
        
    def _crossValidate(self, y_train, X_train, refit=False):
        # Run the grid search
        print "Cross-validating for", self.numFolds, "folds"
        print "Args", self.classifierArgs
        cv = StratifiedKFold(y_train, n_folds=self.numFolds) #self.getCV(y_train, self.meta.meta, numFolds=self.numFolds)
        classifier, classifierArgs = self._getClassifier()
        search = ExtendedGridSearchCV(classifier(), classifierArgs, refit=refit, cv=cv, 
                                      scoring=self.metric, verbose=self.verbose, n_jobs=self.parallel, 
                                      pre_dispatch=int(self.preDispatch) if self.preDispatch.isdigit() else self.preDispatch)
        search.fit(X_train, y_train)
#         if hasattr(search, "best_estimator_"):
#             print "----------------------------- Best Estimator -----------------------------------"
#             print search.best_estimator_
#             if hasattr(search.best_estimator_, "doRFE"):
#                 print "*** RFE ***"
#                 search.best_estimator_.doRFE(X_train, y_train)
        # Show the grid search results
        print "---------------------- Grid scores on development set --------------------------"
        results = []
        #self.extras = None
        index = 0
        bestIndex = 0
        bestExtras = None
        self.meta.drop("prediction")
        self.meta.drop("importance")
        for params, mean_score, scores in search.grid_scores_:
            print scores
            print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
            results.append({"classifier":classifier.__name__, "cv":cv.__class__.__name__, "folds":self.numFolds,
                       "metric":self.metric, "score":None, "scores":",".join([str(x) for x in list(scores)]), 
                       "mean":float(mean_score), "std":float(scores.std() / 2), "params":str(params), "set":"train"})
            if index == 0 or float(mean_score) > results[bestIndex]["mean"]:
                bestIndex = index
                if hasattr(search, "extras_"):
                    bestExtras = search.extras_[index]
            index += 1
        print "---------------------- Best scores on development set --------------------------"
        params, mean_score, scores = search.grid_scores_[bestIndex]
        print scores
        print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
        # Save the grid search results
        print "Saving results"
        self.meta.insert_many("result", results)
        if bestExtras:
            for fold in range(len(bestExtras)):
                extras = bestExtras[fold]
                if "predictions" in extras:
                    rows = []
                    for key in extras["predictions"]:
                        row = OrderedDict(("example",key), ("fold",fold), ("set","train"))
                        values = extras["predictions"][key]
                        for i in range(len(values)):
                            row["class_" + str(i+1)] = values[i]
                        rows.append(row)
                    self.meta.insert_many("prediction", rows)
                if "importances" in extras:
                    importances = extras["importances"]
                    self.meta.insert_many("importance", [OrderedDict(("feature",i), ("fold",fold), ("value",importances[i]), ("set","train")) for i in range(len(importances)) if importances[i] != 0])
        self.meta.flush() 
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
            self.meta.insert("result", self.hiddenResult, immediate=True)
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
#         if resultPath == None:
#             print "Results not saved"
#             return
#         if self.extras == None:
#             print "No detailed information for cross-validation"
#             return
#         if not os.path.exists(os.path.dirname(resultPath)):
#             os.makedirs(os.path.dirname(resultPath))
        # Add general results
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
    
#     def _setValue(self, target, key, value, parent=None):
#         if parent != None:
#             if not parent in target:
#                 target[parent] = {}
#             target = target[parent]
#         target[key] = value