import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
from rlscore.learner import RLS
from rlscore.learner import GreedyRLS
from rlscore.measure.cindex_measure import cindex
import numpy as np
from sklearn.cross_validation import KFold


def nfoldRLS(X, Y, fcount):
    kwargs = {}
    kwargs['train_features'] = X
    kwargs['train_labels'] = Y
    rls = RLS.createLearner(**kwargs)
    rls.train()
    bestperf = -1. 
    for logrp in range(5, 25):
        rp = 2. ** logrp
        rls.solve(rp)
        perfs = []
        kf = KFold(len(Y), n_folds=fcount, indices=True, shuffle=True, random_state=77)
        for train, test in kf:
            P = rls.computeHO(test)
            perf = cindex(Y[test], P)
            perfs.append(perf)
        perf = np.mean(perfs)
        print "N-fold CV %f for lambda 2^%d" %(perf, logrp)
        if perf > bestperf:
            bestperf = perf
            bestlogrp = logrp
    rp = 2. ** bestlogrp
    print "Best N-fold CV %f for lambda 2^%d" %(bestperf, bestlogrp)
    rls.solve(rp)
    model = rls.getModel()
    return model

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Feature selection with Greedy RLS')
    parser.add_argument('-x','--features', help='Input file for feature vectors (X)', default=None)
    parser.add_argument('-y','--labels', help='Input file for class labels (Y)', default=None)
    parser.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=5)
    options = parser.parse_args()
    X = np.loadtxt(options.features)
    Y = np.loadtxt(options.labels)
    model = nfoldRLS(X, Y, options.numFolds)
    #model.predict(testX)
