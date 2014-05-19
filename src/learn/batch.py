import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.example import exampleOptions, readAuto
from data.template import parseOptionString
from data.cache import getExperiment
import settings
import learn
import time
from connection.UnixConnection import UnixConnection
from connection.SLURMConnection import SLURMConnection

CLASSIFIER_ARGS = {
    #'ensemble.RandomForest':{'n_estimators':[10,100],'max_features':['auto',None]},
    'ensemble.ExtraTreesClassifier':"n_estimators=[10000]",
    'svm.LinearSVC':"C=logrange(-10, 10)"}

ANALYZE = ['ensemble.ExtraTreesClassifier']
ALL_CAMDA_PROJECTS = ["KIRC-US", "LUAD-US", "HNSC-US"]
ALL_PROJECTS = ["BLCA-US","BOCA-UK","BRCA-UK","BRCA-US","CESC-US","CLLE-ES",
                "CMDI-UK","COAD-US","EOPC-DE","ESAD-UK","GBM-US","HNSC-US",
                "KIRC-US","KIRP-US","LAML-US","LGG-US","LICA-FR","LIHC-US",
                "LINC-JP","LIRI-JP","LUAD-US","LUSC-US","MALY-DE","NBL-US",
                "ORCA-IN","OV-AU","OV-US","PAAD-US","PACA-AU","PACA-CA",
                "PAEN-AU","PBCA-DE","PRAD-CA","PRAD-US","READ-US","RECA-CN",
                "RECA-EU","SKCM-US","STAD-US","THCA-SA","THCA-US","UCEC-US"]


def getJobs(resultPath, experiments=None, projects=None, classifiers=None):
    global ALL_CAMDA_PROJECTS, ALL_PROJECTS
    if experiments == None:
        experiments = "ALL"
    if isinstance(experiments, basestring):
        experiments = experiments.replace("ALL", "CANCER_OR_CONTROL,REMISSION")
        experiments = experiments.split(",")
    if projects == None:
        projects = "ALL_CAMDA"
    if isinstance(projects, basestring):
        experiments = experiments.replace("ALL_CAMDA", ",".join(ALL_CAMDA_PROJECTS))
        experiments = experiments.replace("ALL", ALL_PROJECTS)
        projects = projects.split(",")
    if classifiers == None:
        classifiers = 'ensemble.ExtraTreesClassifier'
    if isinstance(experiments, basestring):
        classifiers = classifiers.split(",")
    
    jobs = []
    for experiment in experiments:
        for project in projects:
            for classifier in classifiers:
                resultFileName = experiment + "-" + project + "-" + classifier + ".json"
                job = {"result":os.path.join(resultPath, resultFileName),
                       "experiment":experiment,
                       "project":project,
                       "classifier":classifier
                       }
                jobs.append(job)
    return jobs

def run(resultPath, runDir):
    global ANALYZE, CLASSIFIER_ARGS
    jobs = getJobs(resultPath)
    for index, job in enumerate(jobs):
        print "Processing job", str(index+1) + "/" + str(len(jobs)), job
        script = "cd " + runDir + "\n"
        script += "python learn.py"
        script += " -e " + job["experiment"] + " -o \"project=" + job["project"] + ",include=both\""
        script += " -c " + job["classifier"] + " -a " + CLASSIFIER_ARGS[job["classifier"]]
        if job["classifier"] in ANALYZE:
            script += " --analyze"
        script += " --clearCache"
        connection.submit(script, jobDir, jobName, stdout, stderr)

def runImmediate(job):
    featureFilePath, labelFilePath, metaFilePath = getExperiment(experiment=job["experiment"], 
                                                                 experimentOptions="project="+job["experiment"]+",hidden=both")
    learn.test(featureFilePath, labelFilePath, metaFilePath, classifier=job["classifier"], 
               classifierArgs=CLASSIFIER_ARGS[job["classifier"]], 
               resultPath=job["result"], analyzeResults=job["classifier"] in ANALYZE)
    print "Removing cache files"
    for filename in [featureFilePath, labelFilePath, metaFilePath]:
        if os.path.exists(filename):
            os.remove(filename)

def waitForJobs(maxJobs, submitCount, connection, sleepTime=15):
    currentJobs = connection.getNumJobs()
    print >> sys.stderr, "Current jobs", str(currentJobs) + ", max jobs", str(maxJobs) + ", submitted jobs", submitCount
    if maxJobs != None:
        while(currentJobs >= maxJobs):
            time.sleep(sleepTime)
            currentJobs = connection.getNumJobs()
            print >> sys.stderr, "Current jobs", str(currentJobs) + ", max jobs", str(maxJobs) + ", submitted jobs", submitCount
    
def batch(experiments, projects, classifiers, database, hidden, writer, sleepTime=15):
    if sleepTime == None:
        sleepTime = 15
    if isinstance(experiments, basestring):
        experiments = experiments.split(",")
    if isinstance(projects, basestring):
        projects = projects.split(",")
    run = runImmediate
    for experiment in experiments:
        waitForJobs(limit, submitCount, connection, sleepTime)
        template = settings[experiment]
        if 'project' in template:
            projectsToProcess = projects
        else:
            projectsToProcess = [None]
        for project in projectsToProcess:
            for classifier in classifiers:
                print "Processing", experiment + "/" + str(project) + "/" + classifier
                run(experiment, project, classifier, CLASSIFIER_ARGS[classifier], database, hidden, writer)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(parents=[exampleOptions], description='')
    parser.add_argument('-e','--experiments', help='', default=None)
    parser.add_argument('-p','--projects', help='', default=None)
    parser.add_argument('-r','--results', help='Output directory', default=None)
    parser.add_argument('--slurm', help='', default=False, action="store_true")
    #parser.add_argument('--cacheDir', help='Cache directory (optional)', default=os.path.join(tempfile.gettempdir(), "CAMDA2014"))
    parser.add_argument("-l", "--limit", default=None, dest="limit", help="")
    parser.add_argument("--debug", default=False, action="store_true", dest="debug", help="Print jobs on screen")
    parser.add_argument("--dummy", default=False, action="store_true", dest="dummy", help="Don't submit jobs")
    parser.add_argument("--rerun", default=None, dest="rerun", help="Rerun jobs which have one of these states (comma-separated list)")
    parser.add_argument("--maxJobs", default=None, type="int", dest="maxJobs", help="Maximum number of jobs in queue/running")
    parser.add_argument("--hideFinished", default=False, action="store_true", dest="hideFinished", help="")
    options = parser.parse_args()
    
    if options.slurm:
        connection = SLURMConnection()
    else:
        connection = UnixConnection()
    connection.debug = options.debug