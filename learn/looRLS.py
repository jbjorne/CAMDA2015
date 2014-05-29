import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
from rlscore.learner import RLS
from rlscore.measure.cindex_measure import cindex
import numpy as np
import cPickle

def looRLS(X, Y):
    kwargs = {}
    kwargs['train_features'] = X
    kwargs['train_labels'] = Y
    kwargs['regparam'] = 1.0
    rls = RLS.createLearner(**kwargs)
    rls.train()
    bestperf = -1. 
    for logrp in range(5, 25):
        rp = 2. ** logrp
        rls.solve(rp)
        Ploo = rls.computeLOO()
        perf = cindex(Y, Ploo)
        print "Leave-one-out %f for lambda 2^%d" %(perf, logrp)
        if perf > bestperf:
            bestperf = perf
            bestlogrp = logrp
    rp = 2. ** bestlogrp
    print "Best leave-one-out %f for lambda 2^%d" %(bestperf, bestlogrp)
    rls.solve(rp)
    model = rls.getModel()
    return model


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Feature selection with Greedy RLS')
    parser.add_argument('-x','--features', help='Input file for feature vectors (X)', default=None)
    parser.add_argument('-y','--labels', help='Input file for class labels (Y)', default=None)
    options = parser.parse_args()
    X = np.loadtxt(options.features)
    Y = np.loadtxt(options.labels)
    model = looRLS(X, Y)
    #model.predict(testX)

