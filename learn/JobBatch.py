from connection.UnixConnection import UnixConnection
from connection.SLURMConnection import SLURMConnection
import itertools
import sys, os
import time

class JobBatch():
    def __init__(self):
        self.runDir = None
        self.program = None
        self.options = {}
        self.sleepTime = 15
        # Jobs
        self.maxJobs = 1
        self.connection = None
        self.submitCount = 0
    
    def getConnection(self, slurm=False, debug=False):
        if slurm:
            return SLURMConnection(debug=debug)
        else:
            return UnixConnection(debug=debug)
    
    def defineCombinations(self):
        self.optionKeys = sorted(self.options.keys())
        self.optionValues = [self.options[key] for key in self.optionKeys]
        self.combinations = [x for x in itertools.product(self.optionValues)]
    
    def buildScript(self, combination):
        script = ""
        if self.runDir != None:
            script += "cd " + self.runDir + "\n"
        script = "python " + self.program
        for i in range(len(self.optionKeys)):
            script += " -" + self.optionKeys[i] + " " + combination[self.optionKeys[i]]
        return script

    def _waitForJobs(self):
        currentJobs = self.connection.getNumJobs()
        print >> sys.stderr, "Current jobs", str(currentJobs) + ", max jobs", str(self.maxJobs) + ", submitted jobs", self.submitCount
        if self.maxJobs != None:
            while(currentJobs >= self.maxJobs):
                time.sleep(self.sleepTime)
                currentJobs = self.connection.getNumJobs()
                print >> sys.stderr, "Current jobs", str(currentJobs) + ", max jobs", str(self.maxJobs) + ", submitted jobs", self.submitCount
    
    def submitJobs(self):
        self.defineCombinations()
        submitCount = 0
        for combination in self.combinations:
            self._waitForJobs()
            script = self.buildScript(combination)
            if submitJob(script, connection, jobDir, jobName, dummy, rerun, hideFinished):
                submitCount += 1

    def _submitJob(self, script, connection, jobDir, jobName, dummy=False, rerun=None, hideFinished=False):
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
            connection.submit(script, jobDir, jobName, 
                              os.path.join(jobDir, jobName + ".stdout"),
                              os.path.join(jobDir, jobName + ".stderr"))
        else:
            print >> sys.stderr, "Dummy mode"
            if connection.debug:
                print >> sys.stderr, "------- Job script -------"
                print >> sys.stderr, connection.makeJobScript(script, jobDir, jobName)
                print >> sys.stderr, "--------------------------"
        return True
                
    
    def batch(runDir, jobDir, resultPath, experiments, projects, classifiers, features,
          limit=1, sleepTime=15, dummy=False, rerun=None, hideFinished=False, 
          clearCache=False, icgcDB=None, cgiDB=None, connection=None, metric=None):
        global ANALYZE, CLASSIFIER_ARGS
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