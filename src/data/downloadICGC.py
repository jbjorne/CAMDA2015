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

def getProjectPath(projectCode, local=True, codeToDir=None, table=None):
    if codeToDir == None:
        with open('project_codes.tsv', mode='rt') as infile:
            reader = csv.reader(infile, delimiter='\t')
            codeToDir = dict((rows[0],rows[1]) for rows in reader)
    if local:
        path = os.path.join(settings.DATA_PATH, codeToDir[projectCode])
        if table != None:
            path = os.path.join(path, settings.TABLE_FILES[table].replace("%c", projectCode))
    else: # ftp
        path = settings.ICGC_VERSION + "/" + codeToDir[projectCode]
        if table != None:
            path += "/" + settings.TABLE_FILES[table].replace("%c", projectCode)
    return path

def downloadProject(projectCode):
    with open('project_codes.tsv', mode='rt') as infile:
        reader = csv.reader(infile, delimiter='\t')
        codeToDir = dict((rows[0],rows[1]) for rows in reader)
    if projectCode not in codeToDir:
        print "Unknown project:", projectCode
        return
    ftp = connectFTP(settings.ICGC_FTP)
    projectDirFTP = settings.ICGC_VERSION + "/" + codeToDir[projectCode]
    projectDirLocal = os.path.join(settings.DATA_PATH, codeToDir[projectCode])
    if not os.path.exists(projectDirLocal):
        os.makedirs(projectDirLocal)
    for table in sorted(settings.TABLE_FILES.keys()):
        filenameFTP = projectDirFTP + "/" + settings.TABLE_FILES[table].replace("%c", projectCode)
        filenameLocal = os.path.join(projectDirLocal, settings.TABLE_FILES[table].replace("%c", projectCode))
        if not os.path.exists(filenameLocal):
            print "Downloading", filenameFTP
            try:
                ftp.retrbinary("RETR " + filenameFTP, open(filenameLocal, 'wb').write)
            except ftplib.error_perm:
                print "File", filenameFTP, "does not exist"
                os.remove(filenameLocal)
    ftp.quit()
    
#downloadProject("BOCA-UK")
    