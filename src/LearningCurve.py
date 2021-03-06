import sys, os
from _random import Random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Classification import Classification, countUnique
import utils.Stream as Stream
from utils.common import splitOptions

class LearningCurve(Classification):
    def __init__(self, classifierName, classifierArgs, numFolds=10, parallel=1, metric='roc_auc', getCV=None, preDispatch='2*n_jobs', classifyHidden=False,
                 steps=10, seed=2):
        super(LearningCurve, self).__init__(classifierName, classifierArgs, numFolds, parallel, metric, getCV, preDispatch, classifyHidden)
        self.steps = steps
        self.random = Random(seed)
        self.thresholds = None
        self.currentCutoff = None
        self.saveExtra = False
    
    def subsample(self, array, thresholds, cutoff):
        indices = []
        assert array.shape[0] == len(thresholds)
        for i in range(len(thresholds)):
            if thresholds[i] < cutoff:
                indices.append(i)
        return array[indices]
    
    def _getResult(self, setName, classifier, cv, params, score=None, fold=None, mean_score=None, scores=None, extra=None):
        result = super(LearningCurve, self)._getResult(setName=setName, classifier=classifier, cv=cv, params=params, score=score, fold=fold, mean_score=mean_score, scores=scores, extra=extra)
        result["cutoff"] = self.currentCutoff
        result["step"] = self.currentStep
        return result
    
    def _insert(self, tableName, rows):
        if tableName == "result":
            tableName = "learning_curve"
        super(LearningCurve, self)._insert(tableName, rows)
        
    def classify(self):
        self.indices, X_train, X_hidden, y_train, y_hidden = self._splitData()
        thresholds = [self.random.random() for x in y_train]
        for i in range(self.steps):
            print "----------------------", "Learning curve step", i + 1, "----------------------"
            self.currentCutoff = float(i + 1) / self.steps
            self.currentStep = i
            print "Cutoff", self.currentCutoff
            y_sample = self.subsample(y_train, thresholds, self.currentCutoff)
            X_sample = self.subsample(X_train, thresholds, self.currentCutoff)
            if "class" in self.meta.db.tables:
                print "Classes y_sample = ", countUnique(y_sample)
            search = self._crossValidate(y_sample, X_sample, self.classifyHidden and (X_hidden.shape[0] > 0))
            if self.classifyHidden:
                self._predictHidden(y_hidden, X_hidden, search, y_sample.shape[0])
        self.currentCutoff = None
        self.indices = None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-a', "--action", default=None, dest="action")
    groupC = parser.add_argument_group('classify', 'Example Classification')
    groupC.add_argument('-c','--classifier', help='', default=None)
    groupC.add_argument('-r','--classifierArguments', help='', default=None)
    groupC.add_argument('-m','--metric', help='', default="roc_auc")
    groupC.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=10)
    groupC.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
    groupC.add_argument('-l', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    groupC.add_argument("--hidden", default=False, action="store_true", dest="hidden")
    groupC.add_argument('--preDispatch', help='', default='2*n_jobs')
    options = parser.parse_args()
    
    actions = splitOptions(options.action, ["classify", "analyse"])
    Stream.openLog(os.path.join(options.output, "log.txt"), False)
    print "Options:", options.__dict__
    
    if "classify" in actions:
        print "======================================================"
        print "Learning Curve"
        print "======================================================"
        classification = LearningCurve(options.classifier, options.classifierArguments, options.numFolds, options.parallel, options.metric, classifyHidden=options.hidden)
        classification.readExamples(options.output, preserveTables=["result", "prediction", "importance"])
        classification.classify()