import os
import wget
import requests
from urllib import urlopen
import json

dataTypes = {"ssm":"simple_somatic_mutation.open",
             "pexp":"protein_expression"}

#url = "https://dcc.icgc.org/api/v1/download?fn=/release_20/Projects/ALL-US/simple_somatic_mutation.open.ALL-US.tsv.gz"
downloadTemplate = "https://dcc.icgc.org/api/v1/download?fn=/release_20/Projects/PROJECT_CODE/DATA_TYPE.PROJECT_CODE.tsv.gz"
projectsURL = "https://dcc.icgc.org/api/v1/projects?size=100"


def download(project, dataType, outDir):
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    else:
        assert os.path.isdir(outDir)
    downloadURL = downloadTemplate.replace("PROJECT_CODE", project).replace("DATA_TYPE", dataTypes.get(dataType, dataType))
    filename = os.path.join(outDir, os.path.basename(downloadURL))
    if os.path.exists(filename):
        os.remove(filename)
    filename = wget.download(downloadURL, outDir)
    
def test(dataTypes):
    response = requests.get(projectsURL)
    response = response.json()
    for project in response["hits"]:
        print project["id"], project.get("availableDataTypes")
        if "ssm" in project.get("availableDataTypes"):
            download(project["id"], "ssm", "/tmp/download")

def downloadProjects(downloadDir):
    projects = requests.get(projectsURL)
    projects = projects.json()["hits"]
    basicData = ["donor", "sample", "specimen"]
    for project in projects:
        projectId = project["id"]
        availableDataTypes = project.get("availableDataTypes", [])
        for dataType in basicData + availableDataTypes:
            dataType = dataTypes.get(dataType, dataType)
            download(project["id"], dataType, downloadDir)
    
    #print r.text[0:1000]
    #filename = wget.download(url2, "/tmp/download/projects.json")
    #f = open(filename, "rt")
    #text = f.read()
    #f.close()
    
    #url = urlopen(url2)
    #print url
    #result = json.loads(url)
    
if __name__ == "__main__":
    test(["donor", "sample", "specimen", "ssm", "cnsm", "exp_seq", "exp_array"])