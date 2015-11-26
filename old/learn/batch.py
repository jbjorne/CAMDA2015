import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
from data.example import exampleOptions
import time
import tempfile
from connection.UnixConnection import UnixConnection
from connection.SLURMConnection import SLURMConnection

CLASSIFIER_ARGS = {
    #'ensemble.RandomForest':{'n_estimators':[10,100],'max_features':['auto',None]},
    'ensemble.ExtraTreesClassifier':'n_estimators=[10,100,1000],random_state=[1]',
    'svm.LinearSVC':'C=logrange(-10, 10)',
    'RFEWrapper':'C=logrange(-10, 10)',
    'RLScore':'alpha=logrange(-10, 10),subsetsize=[200]',
    'linear_model.Ridge':'alpha=logrange(5, 10)'}

ANALYZE = ['ensemble.ExtraTreesClassifier']
ALL_CAMDA_PROJECTS = ["KIRC-US", "LUAD-US", "HNSC-US"]
ALL_PROJECTS = [
    'ALL-US', 'BLCA-CN', 'BLCA-US', 'BOCA-FR', 'BOCA-UK', 'BRCA-UK', 'BRCA-US', 
    'CESC-US', 'CLLE-ES', 'CMDI-UK', 'COAD-US', 'COCA-CN', 'EOPC-DE', 'ESAD-UK', 
    'ESCA-CN', 'GACA-CN', 'GBM-US', 'HNSC-US', 'KIRC-US', 'KIRP-US', 'LAML-KR', 
    'LAML-US', 'LGG-US', 'LIAD-FR', 'LICA-FR', 'LIHC-US', 'LIHM-FR', 'LINC-JP', 
    'LIRI-JP', 'LUAD-US', 'LUSC-CN', 'LUSC-KR', 'LUSC-US', 'MALY-DE', 'NBL-US', 
    'ORCA-IN', 'OV-AU', 'OV-US', 'PAAD-US', 'PACA-AU', 'PACA-CA', 'PACA-IT', 
    'PAEN-AU', 'PBCA-DE', 'PRAD-CA', 'PRAD-UK', 'PRAD-US', 'READ-US', 'RECA-CN', 
    'RECA-EU', 'SKCM-US', 'STAD-US', 'THCA-SA', 'THCA-US', 'UCEC-US']

ALL_FEATURES = ["[EXP]","[PEXP]","[MIRNA]","[SSM]","[CNSM]","ALL_FEATURES"]


def getJobs(resultPath, experiments=None, projects=None, classifiers=None, features=None):
    global ALL_CAMDA_PROJECTS, ALL_PROJECTS
    if experiments == None:
        experiments = "ALL"
    if isinstance(experiments, basestring):
        experiments = experiments.replace("ALL", "CANCER_OR_CONTROL,REMISSION")
        experiments = experiments.split(",")
    if projects == None:
        projects = "ALL_CAMDA"
    if isinstance(projects, basestring):
        projects = projects.replace("ALL_CAMDA", ",".join(ALL_CAMDA_PROJECTS))
        projects = projects.replace("ALL", ",".join(ALL_PROJECTS))
        projects = projects.split(",")
    if classifiers == None:
        classifiers = 'ensemble.ExtraTreesClassifier'
    if isinstance(classifiers, basestring):
        classifiers = classifiers.split(",")
    if features == None:
        features = [None]
    elif features == "ALL":
        features = ALL_FEATURES
    elif isinstance(features, basestring):
        features = features.split(",")
    
    jobs = []
    for experiment in experiments:
        for project in projects:
            for classifier in classifiers:
                for feature in features:
                    resultFileName = experiment + "-" + project + "-" + classifier
                    if feature != None:
                        resultFileName += "-" + feature.replace("[", "").replace("]", "")
                    resultFileName += ".json"
                    job = {"result":os.path.join(resultPath, resultFileName),
                           "experiment":experiment,
                           "project":project,
                           "classifier":classifier,
                           "features":feature
                           }
                    jobs.append(job)
    return jobs

def waitForJobs(maxJobs, submitCount, connection, sleepTime=15):
    currentJobs = connection.getNumJobs()
    print >> sys.stderr, "Current jobs", str(currentJobs) + ", max jobs", str(maxJobs) + ", submitted jobs", submitCount
    if maxJobs != None:
        while(currentJobs >= maxJobs):
            time.sleep(sleepTime)
            currentJobs = connection.getNumJobs()
            print >> sys.stderr, "Current jobs", str(currentJobs) + ", max jobs", str(maxJobs) + ", submitted jobs", submitCount

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
    
def batch(runDir, jobDir, resultPath, experiments, projects, classifiers, features,
          limit=1, sleepTime=15, dummy=False, rerun=None, hideFinished=False, 
          clearCache=False, icgcDB=None, cgiDB=None, connection=None, metric=None):
    global ANALYZE, CLASSIFIER_ARGS
    if sleepTime == None:
        sleepTime = 15
    submitCount = 0
    jobs = getJobs(resultPath, experiments, projects, classifiers, features)
    for index, job in enumerate(jobs):
        waitForJobs(limit, submitCount, connection, sleepTime)
        print "Processing job", str(index+1) + "/" + str(len(jobs)), job
        script = ""
        if runDir != None:
            script = "cd " + runDir + "\n"
        featureScript = ""
        if "features" in job and job["features"] != None:
            featureScript = ",features=" + job["features"]
        script += "python learn.py"
        script += " -e " + job["experiment"] + " -o \"project=" + job["project"] + ",include=both" + featureScript + "\""
        script += " -c " + job["classifier"] + " -a \"" + CLASSIFIER_ARGS[job["classifier"]] + "\""
        script += " --metric \"" + metric + "\""
        script += " -r " + job["result"]
        script += " --cacheDir " + os.path.join(tempfile.gettempdir(), "CAMDA2015", os.path.basename(job["result"]))
        if job["classifier"] in ANALYZE:
            script += " --analyze"
        if clearCache:
            script += " --clearCache"
        if icgcDB != None:
            script += " --database " + icgcDB
        if cgiDB != None:
            script += " --databaseCGI " + cgiDB
        jobName = os.path.basename(job["result"])
        if submitJob(script, connection, jobDir, jobName, dummy, rerun, hideFinished):
            submitCount += 1

def getConnection(slurm=False, debug=False):
    if slurm:
        return SLURMConnection(debug=debug)
    else:
        return UnixConnection(debug=debug)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-e','--experiments', help='', default=None)
    parser.add_argument('-p','--projects', help='', default=None)
    parser.add_argument('-c','--classifiers', help='', default=None)
    parser.add_argument('-f','--features', help='', default=None)
    parser.add_argument('-r','--results', help='Output directory', default=None)
    parser.add_argument('--slurm', help='', default=False, action="store_true")
    #parser.add_argument('--cacheDir', help='Cache directory (optional)', default=os.path.join(tempfile.gettempdir(), "CAMDA2014"))
    parser.add_argument("--debug", default=False, action="store_true", dest="debug", help="Print jobs on screen")
    parser.add_argument("--dummy", default=False, action="store_true", dest="dummy", help="Don't submit jobs")
    parser.add_argument("--rerun", default=None, dest="rerun", help="Rerun jobs which have one of these states (comma-separated list)")
    parser.add_argument("-l", "--limit", default=None, type=int, dest="limit", help="Maximum number of jobs in queue/running")
    parser.add_argument("--hideFinished", default=False, action="store_true", dest="hideFinished", help="")
    parser.add_argument("--runDir", default=None, dest="runDir", help="")
    parser.add_argument("--jobDir", default="/tmp/jobs", dest="jobDir", help="")
    parser.add_argument('--clearCache', default=False, action="store_true")
    ####
    parser.add_argument('--icgcDB', default=settings.DB_PATH, dest="icgcDB")
    parser.add_argument('--cgiDB', default=settings.CGI_DB_PATH, dest="cgiDB")
    options = parser.parse_args()
    
    connection = getConnection(options.slurm)
    if not os.path.exists(options.jobDir):
        os.makedirs(options.jobDir)
    connection.debug = options.debug
    batch(runDir=options.runDir, jobDir=options.jobDir, resultPath=options.results, 
          experiments=options.experiments, projects=options.projects, features=options.features,
          classifiers=options.classifiers, limit=options.limit, sleepTime=15, rerun=options.rerun,
          hideFinished=options.hideFinished, dummy=options.dummy, clearCache=options.clearCache,
          icgcDB=options.icgcDB, cgiDB=options.cgiDB, connection=connection)