import sys, os, shutil
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import result, cache
from learn import learn, batch
from learn.learn import getStratifiedKFoldCV as StratifiedKFold
import sklearn
import settings
import inspect
from collections import OrderedDict

def processDir(database, inputDir, inputFilter, resultDir, cutoff=30, verbose=3, parallel=1, 
               preDispatch='2*n_jobs', randomize=False, slurm=False, limit=1, debug=False,
               dummy=False, rerun=None, hideFinished=False):
#     _, _, _, argDict = inspect.getargvalues(inspect.currentframe())
#     output = OrderedDict()
#     output["call"] = argDict
#     results = OrderedDict()
#     output["results"] = results
    projects = result.getProjects(inputDir, inputFilter, returnPaths=True)
    for projectName in sorted(projects.keys()):
        print "---------", "Processing project", projectName, "---------"
        for experiment in projects[projectName]:
            for classifier in projects[projectName][experiment]:
                # initialize results structure
                project = projects[projectName][experiment][classifier]
                # determine subdirectory for results
                #resultSubDir = None
                #if resultDir != None:
                #    resultSubDir = os.path.join(resultDir, "_".join([projectName, experiment, classifier]))
                #points = 
                process(database, project, resultDir, cutoff, verbose=verbose, parallel=parallel, 
                                 preDispatch=preDispatch, randomize=randomize,
                                 limit=limit, debug=debug, dummy=dummy, rerun=rerun, hideFinished=hideFinished,
                                 slurm=slurm)
                #results[projectName][experiment][classifier] = points
    
#     if resultDir != None:
#         f = open(os.path.join(resultDir, "results.json"), "wt")
#         json.dump(output, f, indent=4)
#         f.close()   
#     return output

def makeDir(dirname, clear=False):
    if clear and os.path.exists(dirname):
        shutil.rmtree(dirname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    return dirname
    
def process(database, inputMetaPath, resultBaseDir, cutoff=50, verbose=3, parallel=1, 
            preDispatch='2*n_jobs', randomize=False, limit=1, debug=False,
            dummy=False, rerun=None, hideFinished=False, slurm=False):
    meta = result.getMeta(inputMetaPath)
    
    connection = batch.getConnection(slurm, debug)
    
    makeDir(resultBaseDir)
    cacheDir = makeDir(os.path.join(resultBaseDir, "cache"))
    resultDir = makeDir(os.path.join(resultBaseDir, "results"))
    jobDir = makeDir(os.path.join(resultBaseDir, "jobs"))

    #cachedMetaPath = os.path.join(cacheDir, "base.json")
    
    baseXPath, baseYPath, baseMetaPath = cache.getExperiment(
         experiment=meta["experiment"]["name"], experimentOptions=meta["experiment"]["options"], 
         database=database, writer="writeNumpyText", useCached=True, cacheDir=cacheDir)

    features = meta["features"]
    count = 0
    featureSet = []
    cls = meta["results"]["best"]
    paramSets = [x["params"] for x in meta["results"]["all"]]
    classifierArgs = {}
    for paramSet in paramSets:
        for key in paramSet:
            if not key in classifierArgs:
                classifierArgs[key] = []
            classifierArgs[key].append(paramSet[key])
    classifierNameMap = {
        "LinearSVC":"svm.LinearSVC",
        "svm.LinearSVC":"svm.LinearSVC",
        "ExtraTreesClassifier":"ensemble.ExtraTreesClassifier",
        "ensemble.ExtraTreesClassifier":"ensemble.ExtraTreesClassifier",
        "RLScore":"RLScore"
    }
    classifierName = classifierNameMap[cls["classifier"]]
    #classifier, classifierArgs = learn.getClassifier(classifierName, params)
    submitCount = 0
    sleepTime = 15
    for featureName in features:
        feature = features[featureName]
        batch.waitForJobs(limit, submitCount, connection, sleepTime)
        print "Processing feature", featureName
        print feature
        featureSet.append(feature["id"])
        jobName = "_".join([meta["experiment"]["name"], meta["template"]["project"], classifierName, "feature-" + str(feature["rank"])])
        pointResultPath = os.path.join(resultDir, jobName + ".json")
        print "Feature set", featureSet
        if len(featureSet) > 1:
#             hiddenResults = curvePoint(baseXPath, baseYPath, baseMetaPath, featureSet, pointResultPath, 
#                        classifier=classifier, classifierArgs=params, getCV=eval(cls["cv"]),
#                        numFolds=cls["folds"], verbose=verbose, parallel=parallel,
#                        preDispatch=preDispatch, randomize=randomize, metric=cls["metric"])[3]
            #results.append(hiddenResults)
            command = "python curvePoint.py"
            command +=  " -X " + baseXPath
            command +=  " -y " + baseYPath
            command +=  " -m " + inputMetaPath
            command +=  " -o " + pointResultPath
            command +=  " --cutoff " + str(count)
            command +=  " --classifier " + classifierName
            command +=  " --classifierArgs \"" + str(classifierArgs) + "\"" 
            command +=  " --iteratorCV " + cls["cv"]
            command +=  " --numFolds " + str(cls["folds"])
            command +=  " --verbose " + str(verbose)
            command +=  " --parallel " + str(parallel)
            command +=  " --preDispatch \"" + str(preDispatch) + "\""
            if randomize: 
                command +=  " --randomize "
            command +=  " --metric " + cls["metric"]
            
            if batch.submitJob(command, connection, jobDir, jobName, dummy, rerun, hideFinished):
                submitCount += 1
        count += 1
        if count > cutoff:
            break
    
#     if resultDir != None:
#         f = open(os.path.join(resultDir, "results.json"), "wt")
#         json.dump(results, f, indent=4)
#         f.close()   
#     return results

# def curvePoint(XPath, yPath, metaPath, featureSet, resultPath, classifier, classifierArgs, getCV, numFolds, verbose, parallel, preDispatch, randomize, metric):
#     meta, results, extras, hiddenResults, hiddenDetails = learn.test(
#         XPath, yPath, metaPath, resultPath, 
#         classifier=classifier, classifierArgs=classifierArgs, getCV=getCV, 
#         numFolds=numFolds, verbose=verbose, parallel=parallel, preDispatch=preDispatch, 
#         randomize=randomize, analyzeResults=False, 
#         metric=metric, useFeatures=featureSet)
#     return [meta, results, extras, hiddenResults, hiddenDetails]

def submitJob(command, connection, jobDir, jobName, dummy=False, rerun=None, hideFinished=False):
    print >> sys.stderr, "Processing job", jobName, "for input", input
    jobStatus = connection.getJobStatusByName(jobDir, jobName)
    if jobStatus != None:
        if rerun != None and jobStatus in rerun:
            print >> sys.stderr, "Rerunning job", jobName, "with status", jobStatus
        else:
            if jobStatus == "RUNNING":
                print >> sys.stderr, "Skipping currently running job"
            elif not hideFinished:
                print >> sys.stderr, "Skipping already processed job with status", jobStatus
            return False
    
    if not dummy:
        connection.submit(command, jobDir, jobName, 
                          os.path.join(jobDir, jobName + ".stdout"),
                          os.path.join(jobDir, jobName + ".stderr"))
    else:
        print >> sys.stderr, "Dummy mode"
        if connection.debug:
            print >> sys.stderr, "------- Job command -------"
            print >> sys.stderr, connection.makeJobScript(command, jobDir, jobName)
            print >> sys.stderr, "--------------------------"
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Learning with examples')
    parser.add_argument('-b','--database', help='Database location', default=settings.DB_PATH)
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-i','--input', help='Input directory', default=None)
    parser.add_argument('-f','--inputFilter', help='Input directory filter', default="default")
    parser.add_argument('-m','--meta', help='Metadata input file name', default=None)
    parser.add_argument('--cutoff', help='Number of features to test', type=int, default=30)
    parser.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
    parser.add_argument('-p', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    parser.add_argument('--preDispatch', help='', default='2*n_jobs')
    parser.add_argument('--randomize', help='', default=False, action="store_true")
    parser.add_argument('--clearCache', default=False, action="store_true")
    # Batch commands
    parser.add_argument('--slurm', help='', default=False, action="store_true")
    parser.add_argument("--debug", default=False, action="store_true", dest="debug", help="Print jobs on screen")
    parser.add_argument("--dummy", default=False, action="store_true", dest="dummy", help="Don't submit jobs")
    parser.add_argument("--rerun", default=None, action="store_true", dest="rerun", help="Rerun all jobs")
    parser.add_argument("-l", "--limit", default=None, type=int, dest="limit", help="Maximum number of jobs in queue/running")
    parser.add_argument("--hideFinished", default=False, action="store_true", dest="hideFinished", help="")
    parser.add_argument("--runDir", default=None, dest="runDir", help="")
    parser.add_argument("--jobDir", default="/tmp/jobs", dest="jobDir", help="")
    options = parser.parse_args()
    
    if options.rerun == True:
        options.rerun = ["FINISHED","FAILED"]
    
    if options.inputFilter != None:
        if options.inputFilter == "default":
            options.inputFilter = {"projects":["KIRC-US", "LUAD-US", "HNSC-US"], "experiments":["REMISSION"], "filename":["REMISSION", "ExtraTreesClassifier"]}
        else:
            options.inputFilter = eval(options.inputFilter)
    if options.inputFilter == None:
        options.inputFilter = {}
    options.inputFilter["classifiers"] = "ExtraTreesClassifier"
    
    if options.input != None:
        processDir(options.database, options.input, options.inputFilter, options.output, options.cutoff,
            verbose=options.verbose, parallel=options.parallel, preDispatch=options.preDispatch, randomize=options.randomize,
            slurm=options.slurm, limit=options.limit, dummy=options.dummy, debug=options.debug, rerun=options.rerun, hideFinished=options.hideFinished)
    else:
        process(options.database, options.meta, options.output, options.cutoff,
            verbose=options.verbose, parallel=options.parallel, preDispatch=options.preDispatch, randomize=options.randomize,
            slurm=options.slurm, limit=options.limit, dummy=options.dummy, debug=options.debug, rerun=options.rerun, hideFinished=options.hideFinished)