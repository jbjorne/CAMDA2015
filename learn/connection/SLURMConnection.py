import sys
from ClusterConnection import ClusterConnection

SLURMJobTemplate = """#!/bin/bash -l 
##execution shell environment 

## name of your job
#SBATCH -J %job
## system error message output file
#SBATCH -e %stderr
## system message output file
#SBATCH -o %stdout
## a per-process (soft) memory limit
## limit is specified in MB
## example: 1 GB is 1000
#SBATCH --mem-per-cpu=%memory
## how long a job takes, wallclock time hh:mm:ss
#SBATCH -t %wallTime
## number of processes
#SBATCH -n %cores

module load python-env
mkdir -p %stderrDir
mkdir -p %stdoutDir

%commands"""

class SLURMConnection(ClusterConnection):
    """
    For using the Simple Linux Utility for Resource Management (https://computing.llnl.gov/linux/slurm/).
    """
    def __init__(self, account=None, workdir=None, settings=None, wallTime=None, memory=None, cores=None, modules=None, preamble=None, debug=False):
        if wallTime == None:
            wallTime = "48:00:00"
        if memory == None:
            memory = 64000
        if cores == None:
            cores = 1
        #if modules == None:
        #    modules = ["python", "ruby"]
        ClusterConnection.__init__(self, account=account, workdir=workdir, settings=settings, memory=memory, cores=cores, modules=modules, wallTime=wallTime, preamble=preamble, debug=debug)
        self.submitCommand = "sbatch"
        self.jobListCommand = "squeue"
        self.jobTemplate = SLURMJobTemplate
    
    def submit(self, script=None, jobDir=None, jobName=None, stdout=None, stderr=None):
        pstdout, pstderr = ClusterConnection.submit(self, script, jobDir, jobName, stdout, stderr)
        if pstderr != None:
            print >> sys.stderr, pstderr
        print >> sys.stderr, pstdout
        assert pstdout.startswith("Submitted batch job"), pstdout
        jobId = int(pstdout.split()[-1])
        return self._writeJobFile(jobDir, jobName, {"SLURMID":jobId}, append=True)
    
    def getJobStatus(self, job):
        jobAttr = self._readJobFile(job)
        # Check whether job exists
        if jobAttr == None:
            return None
        if "SLURMID" not in jobAttr:
            return "FAILED" # submitting the job failed
        for line in self.run("sacct -u " + self.getUserName() + " -j " + jobAttr["SLURMID"]):
            line = line.strip()
            splits = line.split()
            #if self.debug:
            #    print >> sys.stderr, "sacct line:", line
            #print splits
            if splits[0] == jobAttr["SLURMID"]:
                if self.debug:
                    print >> sys.stderr, "sacct:", line
                jobStatus = splits[5]
                jobStatus = jobStatus.rstrip("+")
                if jobStatus in ["RUNNING", "COMPLETING"]:
                    return "RUNNING"
                elif jobStatus == "COMPLETED":
                    if "retcode" not in jobAttr: # file hasn't had the time to be updated?
                        return "RUNNING"
                    elif jobAttr["retcode"] == "0":
                        return "FINISHED"
                    else:
                        return "FAILED"
                elif jobStatus in ["FAILED", "CANCELLED", "NODE_FAIL", "PREEMPTED", "TIMEOUT"]:
                    return "FAILED"
                elif jobStatus in ["PENDING", "RESIZING", "SUSPENDED"]:
                    return "QUEUED"
                else:
                    assert False, jobStatus
        return "QUEUED"