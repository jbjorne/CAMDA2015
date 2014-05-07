import numpy
import json
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.example import *
from data import buildExamples
from data.template import *
from sklearn.cross_validation import StratifiedKFold
import sklearn.cross_validation

def test(XPath, yPath, metaPath, classifier, classifierArgs, numFolds=10):
    print "Loading labels from", yPath
    y = numpy.loadtxt(yPath)
    print "Loading features from", XPath
    X = numpy.loadtxt(XPath)
    meta = {}
    if metaPath != None:
        print "Loading metadata from", metaPath
        f = open(metaPath, "rt")
        meta = json.load(f)
        f.close()

    # Run classifier with crossvalidation
    print "Initializing classifier"
    #classifier = svm.SVC(kernel='linear', probability=True)
    classifier = classifier(**classifierArgs) #sklearn.ensemble.RandomForestClassifier(n_jobs=-1)
    print "Cross-validating for", numFolds, "folds"
    cv = StratifiedKFold(y, n_folds=numFolds)
    scores = sklearn.cross_validation.cross_val_score(classifier, X, y, cv=cv, scoring="roc_auc", verbose=2)
    print "Scores:", scores
    print("Mean: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))

if __name__ == "__main__":
    import argparse
    import tempfile
    parser = argparse.ArgumentParser(parents=[exampleOptions], description='Learning with examples')
    parser.add_argument('-x','--features', help='Input file for feature vectors (X)', default=None)
    parser.add_argument('-y','--labels', help='Input file for class labels (Y)', default=None)
    parser.add_argument('-m','--meta', help='Metadata input file name (optional)', default=None)
    parser.add_argument('--noCache', help='Do not use cache', default=False, action="store_true")
    parser.add_argument('--cacheDir', help='Cache directory, used if x, y or m are undefined (optional)', default=os.path.join(tempfile.gettempdir(), "CAMDA2014"))
    parser.add_argument('-w','--writer', help='Output writer function (optional)', default='writeNumpyText')
    parser.add_argument('-c','--classifier', help='', default='ensemble.RandomForestClassifier')
    parser.add_argument('-a','--classifierArguments', help='', default=None)
    parser.add_argument('-n','--numFolds', help='Number of folds in cross-validation', type=int, default=10)
    options = parser.parse_args()
    
    if "." in options.classifier:
        importCmd = "from sklearn." + options.classifier.rsplit(".", 1)[0] + " import " + options.classifier.rsplit(".", 1)[1]
    else:
        importCmd = "import " + options.classifier
    print importCmd
    exec importCmd
    classifier = eval(options.classifier.rsplit(".", 1)[1])
    
    cached = None
    if options.experiment != None and not options.noCache:
        template = buildExamples.getExperiment(options.experiment).copy()
        template = buildExamples.parseTemplateOptions(options.options, template)
        project = template.get("project", "")
        tId = options.experiment + "-" + project + "-" + getTemplateId(template)
        if options.features == None:
            options.features = os.path.join(options.cacheDir, tId + "-X")
        if options.labels == None:
            options.labels = os.path.join(options.cacheDir, tId + "-y")
        if options.meta == None:
            options.meta = os.path.join(options.cacheDir, tId + "-meta.json")
        print "Comparing to cached experiment", options.meta
        cached = buildExamples.getCached(options.database, options.experiment, options.options, options.meta)
    
    if cached != None:
        print "Using cached examples"
        options.features = cached["experiment"]["X"]
        options.labels = cached["experiment"]["y"]
        print "X:", options.features
        print "Y:", options.labels
        print "meta:", options.meta
    else:
        print "Building examples for experiment", options.experiment
        print "cache:", options.cache
        print "X:", options.features
        print "Y:", options.labels
        print "meta:", options.meta
        buildExamples.writeExamples(dbPath=options.database, experimentName=options.experiment, experimentOptions=options.options, 
                                    hiddenRule=options.hidden, writer=eval(options.writer), featureFilePath=options.features, labelFilePath=options.labels, metaFilePath=options.meta)
    classifierArgs=parseOptionString(options.classifierArguments)
    print "Using classifier", options.classifier, "with arguments", classifierArgs
    test(options.features, options.labels, options.meta, classifier=classifier, classifierArgs=classifierArgs, numFolds=options.numFolds)