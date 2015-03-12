from sklearn.datasets import svmlight_format
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
from rlscore.learner import RLS
from rlscore.measure.cindex_measure import cindex

def testRLS(input):
    X, Y = svmlight_format.load_svmlight_file(input)
    
    hoindices = range(int(0.1*len(Y)))
    hocompl = list(set(range(len(Y))) - set(hoindices))
    trainX = X[hocompl]
    testX = X[hoindices]
    trainY = Y[hocompl]
    testY = Y[hoindices]
    print len(trainY), len(testY)
    
    kwargs = {}
    kwargs['train_features'] = trainX
    kwargs['train_labels'] = trainY
    
    rls = RLS.createLearner(**kwargs)
    rls.train()
    bestperf = -1.
    for logrp in range(-5, 5):
        rp = 2. ** logrp
        rls.solve(rp)
        Ploo = rls.computeLOO()
        perf = cindex(trainY, Ploo)
        print logrp, perf
        if perf > bestperf:
            bestperf = perf
            bestlogrp = logrp
    rp = 2. ** bestlogrp
    rls.solve(rp)
    P = rls.getModel().predict(testX)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Import ICGC data')
    parser.add_argument('-i','--input', default=None)
    parser.add_argument('-o','--output', default=None)
    options = parser.parse_args()
    
    testRLS(options.input)