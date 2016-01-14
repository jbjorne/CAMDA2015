import sys, os
from _random import Random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Classification import Classification, countUnique
import utils.Stream as Stream

class LearningCurve(Classification):
    def __init__(self, classifierName, classifierArgs, numFolds=10, parallel=1, metric='roc_auc', getCV=None, preDispatch='2*n_jobs', classifyHidden=False,
                 steps=10, seed=2):
        super(LearningCurve, self).__init__(classifierName, classifierArgs, numFolds, parallel, metric, getCV, preDispatch, classifyHidden)
        self.steps = steps
        self.random = Random(seed)
        self.thresholds = None
        self.currentCutoff = None
    
    def subsample(self, array, thresholds, cutoff):
        indices = []
        assert array.shape[0] == len(thresholds)
        for i in range(len(self.thresholds)):
            if self.thresholds[i] > cutoff:
                indices.append(i)
        return array[indices]
    
    def _getResult(self, setName, classifier, cv, params, score=None, mean_score=None, scores=None, numFolds=None):
        result = super(LearningCurve, self)._getResult(self, setName, classifier, cv, params, score=score, mean_score=mean_score, scores=scores, numFolds=numFolds)
        result["cutoff"] = self.currentCutoff
        return result
        
    def classify(self):
        X_train, X_hidden, y_train, y_hidden = self._splitData()
        thresholds = [self.random.random() for x in y_train]
        for i in range(self.steps):
            print "------------", "Learning curve step", i + 1, "------------"
            self.currentCutoff = float(i + 1) / self.steps
            print "Cutoff", self.currentCutoff
            y_sample = self.subsample(y_train, thresholds, self.currentCutoff)
            X_sample = self.subsample(X_train, thresholds, self.currentCutoff)
            if "class" in self.meta.db.tables:
                print "Classes y_sample = ", countUnique(y_sample)
            search = self._crossValidate(y_sample, X_sample, self.classifyHidden and (X_hidden.shape[0] > 0))
            if self.classifyHidden:
                self._predictHidden(y_hidden, X_hidden, search)
        self.currentCutoff = None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run University of Turku experiments for CAMDA 2015')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
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
    
    Stream.openLog(os.path.join(options.output, "log.txt"), False)
    print "Options:", options.__dict__

    print "======================================================"
    print "Learning Curve"
    print "======================================================"
    classification = Classification(options.classifier, options.classifierArguments, options.numFolds, options.parallel, options.metric, classifyHidden=options.hidden)
    classification.classifierName = options.classifier
    classification.classifierArgs = options.classifierArguments
    classification.metric = options.metric
    classification.readExamples(options.output, preserveTables=["results"])
    classification.classify()