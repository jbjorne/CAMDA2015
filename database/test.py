import os
import wget
import requests
from clint.textui import progress
from urllib import urlopen
import json
import shutil

dataTypes = {"ssm":"simple_somatic_mutation.open",
             "pexp":"protein_expression"}

#url = "https://dcc.icgc.org/api/v1/download?fn=/release_20/Projects/ALL-US/simple_somatic_mutation.open.ALL-US.tsv.gz"
downloadTemplate = "https://dcc.icgc.org/api/v1/download?fn=/release_20/Projects/PROJECT_CODE/DATA_TYPE.PROJECT_CODE.tsv.gz"
projectsURL = "https://dcc.icgc.org/api/v1/projects?size=100"


def download(project, dataType, outDir, clear=False):
    downloadURL = downloadTemplate.replace("PROJECT_CODE", project).replace("DATA_TYPE", dataTypes.get(dataType, dataType))
    downloadFile(downloadURL, outDir, clear=clear)
    #filename = wget.download(downloadURL, outDir)
    
def test(dataTypes):
    response = requests.get(projectsURL)
    response = response.json()
    for project in response["hits"]:
        print project["id"], project.get("availableDataTypes")
        if "ssm" in project.get("availableDataTypes"):
            download(project["id"], "ssm", "/tmp/download")

def downloadFile(url, outDir, clear=False):
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    assert os.path.isdir(outDir)
    filename = os.path.join(outDir, os.path.basename(url))
    if os.path.exists(filename):
        if clear:
            os.remove(filename)
        else:
            print "Skipping", filename
            return
    print "Downloading", filename
    r = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        total_length = int(r.headers.get('content-length'))
        for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1): 
            if chunk:
                f.write(chunk)
                f.flush()

def downloadProjects(downloadDir, skipTypes, clear=False):
    if clear and os.path.exists(downloadDir):
        shutil.rmtree(downloadDir)
    
    projects = requests.get(projectsURL)
    projects = projects.json()["hits"]
    basicData = ["donor", "sample", "specimen"]
    count = 0
    for project in projects:
        projectId = project["id"]
        print "Processing project", projectId, "(" + str(count) + "/" + str(len(projects)) + ")"
        availableDataTypes = project.get("availableDataTypes", [])
        for dataType in basicData + availableDataTypes:
            print "  Downloading", dataType
            dataType = dataTypes.get(dataType, dataType)
            download(projectId, dataType, downloadDir, clear=clear)
        count += 1
    
    #print r.text[0:1000]
    #filename = wget.download(url2, "/tmp/download/projects.json")
    #f = open(filename, "rt")
    #text = f.read()
    #f.close()
    
    #url = urlopen(url2)
    #print url
    #result = json.loads(url)
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o','--output', default=None, help="Output directory")
    parser.add_argument('-s','--skipTypes', default="meth_array", help="Do not download these dataTypes")
    parser.add_argument('-c','--clear', help='Delete existing downloads', action='store_true', default=False)
    options = parser.parse_args()
    
    downloadProjects(options.output, options.skipTypes.split(","), options.clear)