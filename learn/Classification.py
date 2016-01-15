import sys, os
from learn.evaluation import aucForPredictions, aucForProbabilites, getClassPredictions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sklearn.cross_validation import StratifiedKFold
from skext.gridSearch import ExtendedGridSearchCV
from sklearn.metrics import classification_report
from collections import defaultdict, OrderedDict
from HiddenSet import splitData
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

class Classification(object):
    def __init__(self, classifierName, classifierArgs, numFolds=10, parallel=1, metric='roc_auc', getCV=None, preDispatch='2*n_jobs', classifyHidden=False):
        # Data
        self.X = None
        self.y = None
        self.meta = None
        self.classes = None
        # Settings
        self.randomize = False
        self.numFolds = numFolds
        self.classifierName = classifierName
        self.classifierArgs = classifierArgs
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
    
    def readExamples(self, inDir, fileStem=None, exampleIO=None, preserveTables=None):
        if fileStem == None:
            fileStem = "examples"
        # Read examples
        if exampleIO == None:
            exampleIO = SVMLightExampleIO(os.path.join(inDir, fileStem))
        self.X, self.y = exampleIO.readFiles()
        # Read metadata
        self.meta = Meta(os.path.join(inDir, fileStem + ".meta.sqlite"))
        self.classes = None
        if "class" in self.meta.db.tables:
            self.classes = [x["value"] for x in self.meta.db["class"].all()]
        self._clearResults(preserveTables)
    
    def _clearResults(self, preserveTables):
        preserveTables = set(preserveTables if preserveTables else [])
        preserveTables = preserveTables.union(set(["class", "example", "experiment", "feature"]))
        for tableName in self.meta.db.tables:
            if tableName not in preserveTables:
                self.meta.drop(tableName)
    
    def _getClassifier(self):
        classifier = importNamed(self.classifierName)
        classifierArgs = getOptions(self.classifierArgs)
        print "Using classifier", classifier.__name__, "with arguments", classifierArgs
        return classifier, classifierArgs
    
    def _splitData(self):
        if self.classes:
            print "Class distribution = ", countUnique(self.y)
        X_train, X_hidden, y_train, y_hidden = splitData(self.X, self.y, self.meta) #hidden.split(self.X, self.y, meta=self.meta.db["example"].all())
        print "Sizes", [X_train.shape[0], y_train.shape[0]], [X_hidden.shape[0], y_hidden.shape[0]]
        if self.classes:
            print "Classes y_train = ", countUnique(y_train)
            print "Classes y_hidden = ", countUnique(y_hidden)
        return X_train, X_hidden, y_train, y_hidden
                
    def classify(self):
        self.meta.dropTables(["result", "prediction", "importance"], 100000)
        X_train, X_hidden, y_train, y_hidden = self._splitData()
        search = self._crossValidate(y_train, X_train, self.classifyHidden and (X_hidden.shape[0] > 0))
        if self.classifyHidden:
            self._predictHidden(y_hidden, X_hidden, search, len(y_train))
    
    def _getResult(self, setName, classifier, cv, params, score=None, mean_score=None, scores=None, numFolds=None):
        result = {"classifier":classifier.__name__, "cv":cv.__class__.__name__ if cv else None,
                  "params":str(params), "numFolds":numFolds, "score":score}
        if mean_score is not None:
            result["mean"] = float(mean_score)
            result["scores"] = ",".join([str(x) for x in list(scores)])
            result["std"] = float(scores.std() / 2)
        return result
    
    def _insert(self, tableName, rows):
        self.meta.insert_many("result", rows)
        
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
        print "---------------------- Grid scores on development set --------------------------"
        results = []
        index = 0
        bestIndex = 0
        bestExtras = None
        for params, mean_score, scores in search.grid_scores_:
            print "Grid:", params
            result = self._getResult("train", classifier, cv, params, None, mean_score, scores, self.numFolds)
            if index == 0 or float(mean_score) > results[bestIndex]["mean"]:
                bestIndex = index
                if hasattr(search, "extras_"):
                    bestExtras = search.extras_[index]
            if hasattr(search, "extras_") and self.classes and len(self.classes) == 2:
                for key in search.extras_[index].get("counts", {}).keys():
                    result[key + "_size"] = search.extras_[index]["counts"][key]
                print self._validateExtras(search.extras_[index], y_train), "(eval:auc)"
            print scores, "(" + self.metric + ")"
            print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)                    
            index += 1
            results.append(result)
        print "---------------------- Best scores on development set --------------------------"
        params, mean_score, scores = search.grid_scores_[bestIndex]
        print scores
        print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
        print "--------------------------------------------------------------------------------"
        # Save the grid search results
        print "Saving results"
        self._insert("result", results)
        self._saveExtras(bestExtras, "train")
        self.meta.flush() 
        return search
    
    def _validateExtras(self, folds, y_train):
        validationScores = []
        for fold in range(len(folds)):
            predictions = folds[fold].get("predictions")
            if predictions:
                foldLabels = []
                foldProbabilities = []
                for exampleIndex in predictions:
                    foldLabels.append(y_train[exampleIndex])
                    foldProbabilities.append(predictions[exampleIndex])
                #print fold, foldProbabilities
                validationScores.append(aucForProbabilites(foldLabels, foldProbabilities, self.classes))
        return validationScores   
    
    def _saveExtras(self, folds, setName, noFold=False):
        if folds == None:
            return
        for fold in range(len(folds)):
            extras = folds[fold]
            foldIndex = None if noFold else fold
            if "predictions" in extras:
                rows = [OrderedDict([("example",key), ("fold",foldIndex), ("set",setName), ("predicted", str(extras["predictions"][key]))]) for key in extras["predictions"]]
                self.meta.insert_many("prediction", rows)
            if "importances" in extras:
                importances = extras["importances"]
                self.meta.insert_many("importance", [OrderedDict([("feature",i), ("fold",foldIndex), ("value",importances[i]), ("set",setName)]) for i in range(len(importances)) if importances[i] != 0])        
        
    def _predictHidden(self, y_hidden, X_hidden, search, trainSize=None):
        if X_hidden.shape[0] > 0:
            print "----------------------------- Classifying Hidden Set -----------------------------------"
            print "search.scoring", search.scoring
            print "search.scorer_", search.scorer_
            print "search.best_estimator_.score", search.best_estimator_.score
            score = search.score(X_hidden, y_hidden) #roc_auc_score(y_hidden, search.best_estimator_.predict(X_hidden))
            print "Score =", score, "(" + self.metric + ")"
            hiddenResult = self._getResult("hidden", search.best_estimator_.__class__, None, search.best_params_, score)
            hiddenResult["train_size"] = trainSize
            hiddenResult["test_size"] = y_hidden.shape[0]
            y_hidden_proba = search.predict_proba(X_hidden)
            if self.classes and len(self.classes) == 2:
                y_hidden_pred = getClassPredictions(y_hidden_proba, self.classes)
                print "AUC =", aucForPredictions(y_hidden, y_hidden_pred), "(eval:auc)"
                hiddenExtra = {"predictions":{i:x for i,x in enumerate(y_hidden_pred)}}
            else:
                hiddenExtra = {"predictions":{i:x for i,x in enumerate([str(list(x)) for x in y_hidden_proba])}}
            if hasattr(search.best_estimator_, "feature_importances_"):
                hiddenExtra["importances"] = search.best_estimator_.feature_importances_
            print "Saving results"
            self._insert("result", hiddenResult)
            self._saveExtras([hiddenExtra], "hidden", True)
            self.meta.flush()
            try:
                print classification_report(y_hidden, y_hidden_pred)
            except ValueError, e:
                print "ValueError in classification_report:", e
        print "--------------------------------------------------------------------------------"