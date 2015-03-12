import sys, os
basePath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(basePath)
sys.path.append(os.path.join(basePath, "lib"))
from rlscore.learner import RLS
from rlscore.measure.cindex_measure import cindex
import numpy as np
import cPickle
from data.example import exampleOptions, readAuto
from data.cache import getExperiment
import data.result as result
import data.hidden as hidden

def looRLS(XPath, yPath, metaPath):
    X, Y = readAuto(XPath, yPath)
    meta = {}
    if metaPath != None:
        print "Loading metadata from", metaPath
        meta = result.getMeta(metaPath)
    X_train, X_hidden, Y_train, Y_hidden = hidden.split(X, Y, meta=meta) 
    kwargs = {}
    kwargs['train_features'] = X_train
    kwargs['train_labels'] = Y_train
    kwargs['regparam'] = 1.0
    rls = RLS.createLearner(**kwargs)
    rls.train()
    bestperf = -1. 
    for logrp in range(5, 25):
        rp = 2. ** logrp
        rls.solve(rp)
        Ploo = rls.computeLOO()
        perf = cindex(Y_train, Ploo)
        print "Leave-one-out %f for lambda 2^%d" %(perf, logrp)
        if perf > bestperf:
            bestperf = perf
            bestlogrp = logrp
    rp = 2. ** bestlogrp
    print "Best leave-one-out %f for lambda 2^%d" %(bestperf, bestlogrp)
    rls.solve(rp)
    model = rls.getModel()
    P = model.predict(X_hidden)
    perf = cindex(Y_hidden, P)
    print "final performance: %f" %perf
    #return model


if __name__ == "__main__":
    import argparse, tempfile
    parser = argparse.ArgumentParser(parents=[exampleOptions], description='Feature selection with Greedy RLS')
    parser.add_argument('-x','--features', help='Input file for feature vectors (X)', default=None)
    parser.add_argument('-y','--labels', help='Input file for class labels (Y)', default=None)
    parser.add_argument('-m','--meta', help='Metadata input file name (optional)', default=None)
    parser.add_argument('--noCache', help='Do not use cache', default=False, action="store_true")
    parser.add_argument('--cacheDir', help='Cache directory, used if x, y or m are undefined (optional)', default=os.path.join(tempfile.gettempdir(), "CAMDA2014"))
    options = parser.parse_args()
    featureFilePath, labelFilePath, metaFilePath = getExperiment(experiment=options.experiment, experimentOptions=options.options, 
                                                                 database=options.database, writer=options.writer, 
                                                                 useCached=not options.noCache, featureFilePath=options.features, 
                                                                 labelFilePath=options.labels, metaFilePath=options.meta)

    looRLS(featureFilePath, labelFilePath, metaFilePath)

