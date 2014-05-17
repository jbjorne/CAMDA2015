"""
Functions for caching example generation
"""
import sys, os, tempfile
import time
import json
import buildExamples
from example import evalWriter
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.template import getTemplateId, parseTemplateOptions
from data.result import getMeta
import settings

def getExperiment(experiment, experimentOptions=None, database=settings.DB_PATH, hidden='skip', writer='writeNumpyText', useCached=True,
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
    if experiment != None and useCached:
        template = buildExamples.parseExperiment(experiment).copy()
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
            cached = getCached(database, experiment, experimentOptions, metaFilePath)
    
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

def getCached(dbPath, experimentName, experimentOptions, meta, verbose=False):
    if meta == None or (isinstance(meta, basestring) and not os.path.exists(meta)): # nothing to compare with
        if verbose:
            print "No existing metadata file", [meta]
        return None
    # Load previous experiment
    meta = getMeta(meta)
    # Load current experiment
    template = buildExamples.parseExperiment(experimentName).copy()
    template = parseTemplateOptions(experimentOptions, template)
    # Get database information
    dbPath = os.path.abspath(os.path.expanduser(dbPath))
    dbModified = time.strftime("%c", time.localtime(os.path.getmtime(dbPath)))
    # Compare settings
    metaExp = meta["experiment"]
    if verbose:
        print dbPath
        print metaExp["dbFile"]
        print dbModified
        print metaExp["dbModified"]
        print json.dumps(template)
        print json.dumps(meta["template"])
    if metaExp["dbFile"] == dbPath and metaExp["dbModified"] == dbModified and template == meta["template"]:
        return meta # is the same experiment
    else:
        return None # previous experiment differs
