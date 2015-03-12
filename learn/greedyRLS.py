import sys, os
basePath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(basePath)
sys.path.append(os.path.join(basePath, "lib"))
from rlscore.learner import RLS
from rlscore.learner import GreedyRLS
from rlscore.measure.cindex_measure import cindex
import numpy as np
import cPickle
from sklearn.cross_validation import KFold
from data.example import exampleOptions, readAuto
import data.result as result
from learn import getClassDistribution
from data.cache import getExperiment
import data.result as result
import data.hidden as hidden

def greedyRLS(XPath, yPath, metaPath, fcount=5, scount=50, resultPath=None):
    X, Y = readAuto(XPath, yPath)
    meta = {}
    if metaPath != None:
        print "Loading metadata from", metaPath
        meta = result.getMeta(metaPath)
    X_train, X_hidden, Y_train, Y_hidden = hidden.split(X, Y, meta=meta) 
    #if "classes" in meta:
    #    print "Class distribution = ", getClassDistribution(y)

    #logrps = range(15, 25)
    logrps = range(15, 26)
    print "Training RLS"
    loopCount = 1
    best_perf = -1
    best_logrp = None
    best_scount = None
    for logrp in logrps:
        kf = KFold(len(Y_train), n_folds=fcount, indices=True, shuffle=True, random_state=77)
        for train, test in kf:
            perfs = []
            print "------------ Processing fold", str(loopCount) + "/" + str(fcount), "------------"
            kwargs = {}
            kwargs['train_features'] = X_train[train]
            kwargs['train_labels'] = Y_train[train]
            kwargs['subsetsize'] = scount
            kwargs['regparam'] = 2.**logrp
            kwargs['bias'] = 1
            cb = CallbackFunction(X_train[test], Y_train[test])
            kwargs['callback_obj'] = cb
            rls = GreedyRLS.createLearner(**kwargs)
            rls.train()
            perfs.append(cb.perfs)
            loopCount += 1
            print "---------------------------------------------------"
        perfs = np.mean(perfs, axis=0)
        perf = np.max(perfs)
        perf = perfs[-1]
        sc = np.argmax(perfs)+1
        print "%f AUC, %d logrp, %d selected" %(perf, logrp, sc)
        if perf>best_perf:
            best_perf = perf
            best_logrp = logrp
            best_scount = sc
    kwargs = {}
    kwargs['train_features'] = X_train
    kwargs['train_labels'] = Y_train
    kwargs['subsetsize'] = scount
    kwargs['regparam'] = 2.**best_logrp
    kwargs['bias'] = 1
    cb = CallbackFunction(X_hidden, Y_hidden)
    kwargs['callback_obj'] = cb
    rls = GreedyRLS.createLearner(**kwargs)
    rls.train()
    perfs = cb.perfs
    selected = rls.selected
    model = rls.getModel()
    #if resultPath != None:
    #    saveResults(meta, resultPath, perfs, selected)
    return model, perfs, selected, best_logrp, best_scount

def saveResults(meta, resultPath, perfs, selected):
    if not os.path.exists(os.path.dirname(resultPath)):
        os.makedirs(os.path.dirname(resultPath))
    meta = result.getMeta(meta)
    featureByIndex = result.getFeaturesByIndex(meta)
    for foldIndex in range(len(selected)):
        ranks = selected[foldIndex]
        for featureRank in range(len(ranks)):
            featureIndex = ranks[featureRank]
            feature = result.getFeature(meta, featureIndex, featureByIndex)
            result.setValue(feature, foldIndex, featureRank, "ranks")
            result.setValue(feature, "sort", -sum(feature["ranks"].values()) / len(feature["ranks"]))
    result.saveMeta(meta, resultPath)

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
    import argparse, tempfile
    parser = argparse.ArgumentParser(parents=[exampleOptions], description='Feature selection with Greedy RLS')
    parser.add_argument('-x','--features', help='Input file for feature vectors (X)', default=None)
    parser.add_argument('-y','--labels', help='Input file for class labels (Y)', default=None)
    parser.add_argument('-m','--meta', help='Metadata input file name (optional)', default=None)
    parser.add_argument('--noCache', help='Do not use cache', default=False, action="store_true")
    parser.add_argument('--cacheDir', help='Cache directory, used if x, y or m are undefined (optional)', default=os.path.join(tempfile.gettempdir(), "CAMDA2014"))
    parser.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=5)
    parser.add_argument('-s','--subsetsize', help='Number of features to be selected', type=int, default=50)
    parser.add_argument('--useOrigOut', help='', default=True, action="store_true")
    parser.add_argument('--outfile', help='Output file for results', type=str, default="selected.txt")
    #parser.add_argument('--outaccuracies', help='Output file for accuracies on each CV round', type=str, default="accuracies.txt")
    parser.add_argument('-r', '--result', help='Output file for detailed results (optional)', default=None)
    options = parser.parse_args()
    
    featureFilePath, labelFilePath, metaFilePath = getExperiment(experiment=options.experiment, experimentOptions=options.options, 
                                                                 database=options.database, writer=options.writer, 
                                                                 useCached=not options.noCache, featureFilePath=options.features, 
                                                                 labelFilePath=options.labels, metaFilePath=options.meta)
    
    #X = np.loadtxt(options.features)
    #Y = np.loadtxt(options.labels)
    #f = open('X')
    #X = cPickle.load(f)
    #f.close()
    model, perfs, selected, best_logrp, best_scount = greedyRLS(featureFilePath, labelFilePath, metaFilePath, options.numFolds, options.subsetsize, resultPath=options.result)
    if (options.useOrigOut):
        f = open(options.outfile, 'w')
        f.write(str(best_logrp)+" " +str(best_scount)+"\n")
        f.write("".join(str(x)+" " for x in perfs)+"\n")
        f.write("".join(str(x)+" " for x in selected)+"\n")
        f.close()
        #np.savetxt(options.outfeatures, selected, fmt="%d")
        #np.savetxt(options.outaccuracies, perfs)
    #model.predict(testX)
