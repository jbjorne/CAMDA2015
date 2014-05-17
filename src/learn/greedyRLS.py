import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
from rlscore.learner import RLS
from rlscore.learner import GreedyRLS
from rlscore.measure.cindex_measure import cindex
import numpy as np
import cPickle
from sklearn.cross_validation import KFold

def greedyRLS(X, Y, fcount=5, scount=50, logrp=20):
    tests = []
    kf = KFold(len(Y), n_folds=fcount, indices=True, shuffle=True, random_state=77)
    logrps = range(20, 22)
    perfs = []
    selected = []
    for train, test in kf:
        kwargs = {}
        kwargs['train_features'] = X[train]
        kwargs['train_labels'] = Y[train]
        kwargs['subsetsize'] = scount
        kwargs['regparam'] = 2.**logrp
        cb = CallbackFunction(X[test], Y[test])
        kwargs['callback_obj'] = cb
        rls = GreedyRLS.createLearner(**kwargs)
        rls.train()
        perfs.append(cb.perfs)
        selected.append(rls.selected)
    perfs = np.mean(perfs, axis=0)
    model = rls.getModel()
    print perfs
    print selected
    return model, perfs, selected



class CallbackFunction(object):

    def __init__(self, testX, testY):
        self.testX = testX
        self.testY = testY
        self.perfs = []

    def callback(self, learner):
        model = learner.getModel()
        P = model.predict(self.testX)
        perf = cindex(self.testY, P)
        self.perfs.append(perf)
    
    def finished(self, learner):
        pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Feature selection with Greedy RLS')
    parser.add_argument('-x','--features', help='Input file for feature vectors (X)', default=None)
    parser.add_argument('-y','--labels', help='Input file for class labels (Y)', default=None)
    parser.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=5)
    parser.add_argument('-l','--loglambda', help='Regularization parameter lambda=2^l', type=int, default=20)
    parser.add_argument('-s','--subsetsize', help='Number of features to be selected', type=int, default=100)
    parser.add_argument('-a','--outfeatures', help='Output file for features selected on each CV round', type=str, default="selected.txt")
    parser.add_argument('-b','--outaccuracies', help='Output file for accuracies on each CV round', type=str, default="accuracies.txt")
    options = parser.parse_args()
    X = np.loadtxt(options.features)
    Y = np.loadtxt(options.labels)
    f = open('X')
    X = cPickle.load(f)
    f.close()
    model, perfs, selected = greedyRLS(X, Y, options.numFolds, options.subsetsize, options.loglambda)
    np.savetxt(options.outfeatures, selected)
    np.savetxt(options.outaccuracies, perfs)
    #model.predict(testX)
