import os, sys
from ftplib import FTP
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings

def connectFTP(server):
    ftp = FTP(server)
    ftp.login()
    return ftp

def getProjectDirectories(ftp):
    dirs = []
    ftp.dir(settings.ICGC_VERSION, dirs.append)
    dirs = [x.split()[-1] for x in dirs]
    return dirs

def getProjectCodes(ftp, projectDirs):
    codeToDir = {}
    for projectDir in projectDirs:
        print "Processing directory", projectDir + ",",
        projectFiles = []
        ftp.dir(settings.ICGC_VERSION + "/" + projectDir, projectFiles.append)
        projectFiles = [x.split()[-1] for x in projectFiles]
        for filename in projectFiles:
            projectCode = None
            if filename.startswith("clinical."):
                projectCode = filename.split(".")[1]
                codeToDir[projectCode] = projectDir
                print "found project code", projectCode
                break
        if projectCode == None:
            print "no project code found"
    return codeToDir
    
ftp = connectFTP(settings.ICGC_FTP)
projectDirs = getProjectDirectories(ftp)
projectCodes = getProjectCodes(ftp, projectDirs)
f = open("project_codes.tsv", "wt")
f.write("Project_Code\tProject_FTP_Directory\n")
for key in sorted(projectCodes.keys()):
    f.write(key + "\t" + projectCodes[key] + "\n")
f.close()
    