import os, sys
import ftplib
from ftplib import FTP
import csv
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

def downloadProjectCodes():    
    ftp = connectFTP(settings.ICGC_FTP)
    projectDirs = getProjectDirectories(ftp)
    projectCodes = getProjectCodes(ftp, projectDirs)
    ftp.quit()
    f = open("project_codes.tsv", "wt")
    f.write("Project_Code\tProject_FTP_Directory\n")
    for key in sorted(projectCodes.keys()):
        f.write(key + "\t" + projectCodes[key] + "\n")
    f.close()

def getCodeToDir():
    with open('project_codes.tsv', mode='rt') as infile:
        reader = csv.reader(infile, delimiter='\t')
        codeToDir = dict((rows[0],rows[1]) for rows in reader)
    return codeToDir

def getProjectPath(projectCode, directory, table=None, codeToDir=None):
    if codeToDir == None:
        codeToDir = getCodeToDir()
    path = os.path.join(directory, codeToDir[projectCode])
    if table != None:
        path = os.path.join(path, settings.TABLE_FILES[table].replace("%c", projectCode))
    return path

def downloadProject(projectCode, downloadDir):
    codeToDir = getCodeToDir()
    if projectCode not in codeToDir:
        print "Unknown project:", projectCode
        return
    ftp = connectFTP(settings.ICGC_FTP)
    for table in sorted(settings.TABLE_FILES.keys()):
        filenameFTP = getProjectPath(projectCode, settings.ICGC_VERSION, table, codeToDir)
        filenameLocal = getProjectPath(projectCode, downloadDir, table, codeToDir)
        if not os.path.exists(filenameLocal):
            if not os.path.exists(os.path.dirname(filenameLocal)):
                os.makedirs(os.path.dirname(filenameLocal))
            print "Downloading", filenameFTP
            try:
                ftp.retrbinary("RETR " + filenameFTP, open(filenameLocal, 'wb').write)
            except ftplib.error_perm:
                print "File", filenameFTP, "does not exist"
                os.remove(filenameLocal)
    ftp.quit()
    
#downloadProject("BOCA-UK")
    