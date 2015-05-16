import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.download import download

def parseReadme(url, filename, outDir):
    filePath = os.path.join(outDir, filename)
    download(url + filename, outDir, clear=False)
    f = open(filePath)
    lines = f.readlines()
    f.close()
    section = None
    projects = []
    filePatterns = []
    for line in lines:
        if line.startswith("##"):
            section = line[2:].strip()
        elif line.startswith("-"):
            if section == "Projects":
                projects.append(line[1:].strip().split()[0])
            elif section == "File Descriptions":
                filePatterns.append(line[1:].split(":")[0].strip())
    return projects, filePatterns


def downloadProject(url, projectCode, filePatterns, downloadDir):
    downloadDir = os.path.join(downloadDir, projectCode)
    if not os.path.exists(downloadDir):
        os.makedirs(downloadDir)
    for pattern in filePatterns:
        filePath = os.path.join(downloadDir, pattern.replace("[ICGC project code]", projectCode))
        if not os.path.exists(filePath):
            #wget.download("/".join([url, projectCode, pattern.replace("[ICGC project code]", projectCode)]), downloadDir)
            download("/".join([url, projectCode, pattern.replace("[ICGC project code]", projectCode)]), downloadDir, clear=False)
    