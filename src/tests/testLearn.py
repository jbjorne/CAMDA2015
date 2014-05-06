import numpy
import json
from sklearn import svm
from sklearn.cross_validation import StratifiedKFold
import sklearn.cross_validation

def test(XPath, yPath, metaPath):
    y = numpy.loadtxt(yPath)
    X = numpy.loadtxt(XPath)
    meta = {}
    if metaPath != None:
        meta = json.load(metaPath)

    # Run classifier with crossvalidation
    print "Initializing classifier"
    cv = StratifiedKFold(y, n_folds=5)
    classifier = svm.SVC(kernel='linear', probability=True)
    print sklearn.cross_validation.cross_val_score(classifier, X, y, cv=cv, scoring="roc_auc")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Learning with examples')
    parser.add_argument('-x','--features', help='Input file for feature vectors (X)')
    parser.add_argument('-y','--labels', help='Input file for class labels (Y)')
    parser.add_argument('-m','--meta', help='Metadata input file name (optional)', default=None)
    options = parser.parse_args()
    
    test(options.features, options.labels, options.meta)