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

def greedyRLS(XPath, yPath, metaPath, fcount=5, scount=50, logrp=20, resultPath=None):
    X, Y = readAuto(XPath, yPath)
    meta = {}
    if metaPath != None:
        print "Loading metadata from", metaPath
        meta = result.getMeta(metaPath)
    #if "classes" in meta:
    #    print "Class distribution = ", getClassDistribution(y)

    tests = []
    kf = KFold(len(Y), n_folds=fcount, indices=True, shuffle=True, random_state=77)
    logrps = range(20, 22)
    perfs = []
    selected = []
    print "Training RLS"
    loopCount = 1
    for train, test in kf:
        print "------------ Processing fold", str(loopCount) + "/" + str(fcount), "------------"
        kwargs = {}
        kwargs['train_features'] = X[train]
        kwargs['train_labels'] = Y[train]
        kwargs['subsetsize'] = scount
        kwargs['regparam'] = 2.**logrp
        cb = CallbackFunction(X[test], Y[test])
        kwargs['callback_obj'] = cb
        rls = GreedyRLS.createLearner(**kwargs)
        rls.train()
        print cb.perfs
        perfs.append(cb.perfs)
        print rls.selected
        selected.append(rls.selected)
        loopCount += 1
        print "---------------------------------------------------"
    perfs = np.mean(perfs, axis=0)
    model = rls.getModel()
    print perfs
    print selected
    if resultPath != None:
        saveResults(meta, resultPath, perfs, selected)
    return model, perfs, selected

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
    parser.add_argument('-l','--loglambda', help='Regularization parameter lambda=2^l', type=int, default=20)
    parser.add_argument('-s','--subsetsize', help='Number of features to be selected', type=int, default=100)
    parser.add_argument('--useOrigOut', help='', default=False, action="store_true")
    parser.add_argument('--outfeatures', help='Output file for features selected on each CV round', type=str, default="selected.txt")
    parser.add_argument('--outaccuracies', help='Output file for accuracies on each CV round', type=str, default="accuracies.txt")
    parser.add_argument('-r', '--result', help='Output file for detailed results (optional)', default=None)
    options = parser.parse_args()
    
    featureFilePath, labelFilePath, metaFilePath = getExperiment(experiment=options.experiment, experimentOptions=options.options, 
                                                                 database=options.database, hidden=options.hidden, writer=options.writer, 
                                                                 useCached=not options.noCache, featureFilePath=options.features, 
                                                                 labelFilePath=options.labels, metaFilePath=options.meta)
    
    #X = np.loadtxt(options.features)
    #Y = np.loadtxt(options.labels)
    #f = open('X')
    #X = cPickle.load(f)
    #f.close()
    model, perfs, selected = greedyRLS(featureFilePath, labelFilePath, metaFilePath, options.numFolds, options.subsetsize, options.loglambda, resultPath=options.result)
    if (options.useOrigOut):
        np.savetxt(options.outfeatures, selected)
        np.savetxt(options.outaccuracies, perfs)
    #model.predict(testX)
