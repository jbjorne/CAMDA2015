"""
Functions for caching example generation
"""
import os, tempfile
import buildExamples
from example import evalWriter
from data.template import getTemplateId

def getExperiment(experiment, experimentOptions, database, hidden='skip', writer='writeNumpyText', useCache=True,
                  featureFilePath=None, labelFilePath=None, metaFilePath=None, cacheDir=os.path.join(tempfile.gettempdir(), "CAMDA2014")):
    """
    Get a cached experiment, or re-calculate if not cached.
    
    experiment = Name of the experiment template in settings.py (such as REMISSION)
    experimentOptions = comma-separated list of key=value pairs, the keys will replace those
                        with the same name in the experiment template. Values are evaluated.
    database = Path to the SQLite database (see data/example.py)
    hidden = How to process hidden donors (see data/example.py)
    writer = Output format (see data/example.py)
    useCache = Whether to use the cache directory. If False, X, y and meta paths must be defined.
    featureFilePath = X, can be None if useCache == True.
    labelFilePath = y, can be None if useCache == True.
    metaFilePath = Meta-data, can be None if useCache == True. If already exists, the experiment
                   will be compared to this. If they are identical, the cached version is used.
    cacheDir = Where cached experiments are stored.
    """
    cached = None
    if experiment != None and useCache:
        template = buildExamples.getExperiment(experiment).copy()
        template = buildExamples.parseTemplateOptions(experimentOptions, template)
        project = template.get("project", "")
        projectId = "".join([c if c.isalpha() or c.isdigit() or c=="-" else "_" for c in project]).strip()
        tId = experiment + "_" + projectId + "_" + getTemplateId(template)
        if featureFilePath == None:
            featureFilePath = os.path.join(cacheDir, tId + "-X")
        if labelFilePath == None:
            labelFilePath = os.path.join(cacheDir, tId + "-y")
        if metaFilePath == None:
            metaFilePath = os.path.join(cacheDir, tId + "-meta.json")
        if os.path.exists(metaFilePath):
            print "Comparing to cached experiment", metaFilePath
            cached = buildExamples.getCached(database, experiment, experimentOptions, metaFilePath)
    
    if cached != None:
        print "Using cached examples"
        featureFilePath = cached["experiment"].get("X", None)
        labelFilePath = cached["experiment"].get("y", None)
    print "Experiment files"
    print "X:", featureFilePath
    print "y:", labelFilePath
    print "meta:", metaFilePath
    
    if cached == None:
        print "Building examples for experiment", experiment, "at cache directory:", cacheDir
        buildExamples.writeExamples(dbPath=database, experimentName=experiment, experimentOptions=experimentOptions, 
                                    hiddenRule=hidden, writer=evalWriter(writer), featureFilePath=featureFilePath, 
                                    labelFilePath=labelFilePath, metaFilePath=metaFilePath)
    
    return featureFilePath, labelFilePath, metaFilePath
