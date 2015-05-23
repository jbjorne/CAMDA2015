import sys, os
import settings
from learn.connection.UnixConnection import UnixConnection
from learn.connection.SLURMConnection import SLURMConnection
import learn.batch

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run University of Turku experiments for CAMDA 2014')
    parser.add_argument('-o','--output', help='Output directory', default=None)
    #parser.add_argument('-r','--results', help='Output directory', default=None)
    parser.add_argument('--slurm', help='', default=False, action="store_true")
    #parser.add_argument('--cacheDir', help='Cache directory (optional)', default=os.path.join(tempfile.gettempdir(), "CAMDA2014"))
    parser.add_argument("--debug", default=False, action="store_true", dest="debug", help="Print jobs on screen")
    parser.add_argument("--dummy", default=False, action="store_true", dest="dummy", help="Don't submit jobs")
    parser.add_argument("--rerun", default=None, dest="rerun", help="Rerun jobs which have one of these states (comma-separated list)")
    parser.add_argument("-l", "--limit", default=None, type=int, dest="limit", help="Maximum number of jobs in queue/running")
    parser.add_argument("--hideFinished", default=False, action="store_true", dest="hideFinished", help="")
    #parser.add_argument("--jobDir", default="/tmp/jobs", dest="jobDir", help="")
    parser.add_argument('--clearCache', default=False, action="store_true")
    ####
    parser.add_argument('--icgcDB', default=settings.DB_PATH, dest="icgcDB")
    parser.add_argument('--cgiDB', default=settings.CGI_DB_PATH, dest="cgiDB")
    ####
    parser.add_argument('-e','--experiments', help='', default="ALL")
    parser.add_argument('-p','--projects', help='', default="REMISSION_MUT_ALL")
    parser.add_argument('-c','--classifiers', help='', default="default")
    parser.add_argument('-f','--features', help='', default=None)
    parser.add_argument('-m','--metric', help='', default="roc_auc")
    options = parser.parse_args()
    
    resultDir = os.path.join(options.output, "results")
    jobDir = os.path.join(options.output, "jobs")
    
    if options.slurm:
        connection = SLURMConnection()
    else:
        connection = UnixConnection()
    if not os.path.exists(jobDir):
        os.makedirs(jobDir)
    connection.debug = options.debug
    runDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "learn")
    
    if options.classifiers == "default":
        options.classifiers = "svm.LinearSVC,ensemble.ExtraTreesClassifier"
    
    learn.batch.batch(runDir=runDir, jobDir=jobDir, resultPath=resultDir, 
          experiments=options.experiments, projects=options.projects, features=options.features,
          classifiers=options.classifiers, 
          limit=options.limit, sleepTime=15, rerun=options.rerun,
          hideFinished=options.hideFinished, dummy=options.dummy, 
          clearCache=options.clearCache, icgcDB=options.icgcDB, cgiDB=options.cgiDB,
          connection=connection, metric=options.metric)