import os
import json
import requests
from clint.textui import progress
import shutil
import tempfile

dataTypes = {"ssm":"simple_somatic_mutation.open",
             "cnsm":"copy_number_somatic_mutation",
             "pexp":"protein_expression"}

downloadTemplate = "https://dcc.icgc.org/api/v1/download?fn=/release_20/Projects/PROJECT_CODE/DATA_TYPE.PROJECT_CODE.tsv.gz"
projectsURL = "https://dcc.icgc.org/api/v1/projects?size=100"

def downloadFile(url, outDir, clear=False):
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    assert os.path.isdir(outDir)
    filename = os.path.join(outDir, os.path.basename(url))
    if os.path.exists(filename):
        if clear:
            os.remove(filename)
        else:
            print "Not downloading existing", filename
            return
    print "Downloading", filename
    r = requests.get(url, stream=True)
    tempFile = tempfile.NamedTemporaryFile(delete=False)
    total_length = int(r.headers.get('content-length'))
    for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1): 
        if chunk:
            tempFile.write(chunk)
            tempFile.flush()
    os.rename(tempFile.name, filename)

def downloadProjects(downloadDir, skipTypes, clear=False):
    if clear and os.path.exists(downloadDir):
        shutil.rmtree(downloadDir)
    
    print "Reading ICGC project info from", projectsURL
    projects = requests.get(projectsURL)
    projectsFilePath = os.path.join(downloadDir, "projects.json") 
    with open(projectsFilePath, 'w') as outfile:
        json.dump(projects.json(), outfile, indent=4, sort_keys=True)
    print "Project info saved to", projectsFilePath
    projects = projects.json()["hits"]
    basicData = ["donor", "sample", "specimen"]
    count = 0
    for project in projects:
        count += 1
        projectId = project["id"]
        print "Processing project", projectId, "(" + str(count) + "/" + str(len(projects)) + ")"
        availableDataTypes = project.get("availableDataTypes", [])
        for dataType in basicData + availableDataTypes:
            if dataType in skipTypes:
                print "Skipping data type", dataType
                continue
            dataType = dataTypes.get(dataType, dataType)
            downloadURL = downloadTemplate.replace("PROJECT_CODE", projectId).replace("DATA_TYPE", dataTypes.get(dataType, dataType))
            downloadFile(downloadURL, downloadDir, clear=clear)
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o','--output', default=None, help="Output directory")
    parser.add_argument('-s','--skipTypes', default="meth_array", help="Do not download these dataTypes")
    parser.add_argument('-c','--clear', help='Delete existing downloads', action='store_true', default=False)
    options = parser.parse_args()
    
    downloadProjects(options.output, options.skipTypes.split(","), options.clear)