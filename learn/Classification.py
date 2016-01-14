import sys, os
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
    
    def readExamples(self, inDir, fileStem=None, exampleIO=None, preserveTables=None):
        if fileStem == None:
            fileStem = "examples"
        # Read examples
        if exampleIO == None:
            exampleIO = SVMLightExampleIO(os.path.join(inDir, fileStem))
        self.X, self.y = exampleIO.readFiles()
        # Read metadata
        self.meta = Meta(os.path.join(inDir, fileStem + ".meta.sqlite"))
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
        if "class" in self.meta.db.tables:
            print "Class distribution = ", countUnique(self.y)
        X_train, X_hidden, y_train, y_hidden = splitData(self.X, self.y, self.meta) #hidden.split(self.X, self.y, meta=self.meta.db["example"].all())
        print "Sizes", [X_train.shape[0], y_train.shape[0]], [X_hidden.shape[0], y_hidden.shape[0]]
        if "class" in self.meta.db.tables:
            print "Classes y_train = ", countUnique(y_train)
            print "Classes y_hidden = ", countUnique(y_hidden)
        return X_train, X_hidden, y_train, y_hidden
                
    def classify(self):
        X_train, X_hidden, y_train, y_hidden = self._splitData()
        search = self._crossValidate(y_train, X_train, self.classifyHidden and (X_hidden.shape[0] > 0))
        if self.classifyHidden:
            self._predictHidden(y_hidden, X_hidden, search)
    
    def _getResult(self, setName, classifier, cv, params, score=None, mean_score=None, scores=None, numFolds=None):
        result = {"classifier":classifier.__name__, "cv":cv.__class__.__name__ if cv else None,
                  "params":str(params), "numFolds":numFolds, "score":score}
        if mean_score is not None:
            result["mean"] = float(mean_score)
            result["scores"] = ",".join([str(x) for x in list(scores)])
            result["std"] = float(scores.std() / 2)
        return result
        
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
        # Show the grid search results
        print "---------------------- Grid scores on development set --------------------------"
        results = []
        index = 0
        bestIndex = 0
        bestExtras = None
        self.meta.drop("result", 100000)
        self.meta.drop("prediction", 100000)
        self.meta.drop("importance", 100000)
        for params, mean_score, scores in search.grid_scores_:
            print scores
            print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
            results.append(self._getResult("train", classifier, cv, params, None, mean_score, scores, self.numFolds))
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
        self._saveExtras(bestExtras, "train")
        self.meta.flush() 
        return search
    
    def _saveExtras(self, folds, setName, noFold=False):
        if folds == None:
            return
        for fold in range(len(folds)):
            extras = folds[fold]
            foldIndex = None if noFold else fold
            if "predictions" in extras:
                rows = []
                for key in extras["predictions"]:
                    row = OrderedDict([("example",key), ("fold",foldIndex), ("set",setName)])
                    values = extras["predictions"][key]
                    for i in range(len(values)):
                        row["class_" + str(i+1)] = values[i]
                    rows.append(row)
                self.meta.insert_many("prediction", rows)
            if "importances" in extras:
                importances = extras["importances"]
                self.meta.insert_many("importance", [OrderedDict([("feature",i), ("fold",foldIndex), ("value",importances[i]), ("set",setName)]) for i in range(len(importances)) if importances[i] != 0])        
        
    def _predictHidden(self, y_hidden, X_hidden, search):
        if X_hidden.shape[0] > 0:
            print "----------------------------- Classifying Hidden Set -----------------------------------"
            print "search.scoring", search.scoring
            print "search.scorer_", search.scorer_
            print "search.best_estimator_.score", search.best_estimator_.score
            print search.scorer_(search.best_estimator_, X_hidden, y_hidden)
            y_hidden_score = search.predict_proba(X_hidden)
            y_hidden_score = [x[1] for x in y_hidden_score]
            hiddenResult = self._getResult("hidden", search.best_estimator_.__class__, None, search.best_params_, search.score(X_hidden, y_hidden)) 
            print "Score =", hiddenResult["score"], "(" + self.metric + ")"
            y_hidden_pred = search.predict_proba(X_hidden) #[list(x) for x in search.predict_proba(X_hidden)]
            hiddenExtra = {"predictions":{i:x for i,x in enumerate([list(x) for x in y_hidden_pred])}}
            if hasattr(search.best_estimator_, "feature_importances_"):
                hiddenExtra["importances"] = search.best_estimator_.feature_importances_
            
            print "Saving results"
            self.meta.insert("result", hiddenResult)
            self._saveExtras([hiddenExtra], "hidden", True)
            self.meta.flush()
            try:
                print classification_report(y_hidden, y_hidden_pred)
            except ValueError, e:
                print "ValueError in classification_report:", e
        print "--------------------------------------------------------------------------------"