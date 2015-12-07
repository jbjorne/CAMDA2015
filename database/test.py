import os
import requests
from clint.textui import progress
import shutil
import tempfile

dataTypes = {"ssm":"simple_somatic_mutation.open",
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
    tempFile = tempfile.mkstemp() #filename + "-part"
    print tempFile
    with open(tempFile, 'wb') as f:
        total_length = int(r.headers.get('content-length'))
        for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1): 
            if chunk:
                f.write(chunk)
                f.flush()
    os.rename(tempFile, filename)

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
            if dataType in skipTypes:
                print "Skipping data type", dataType
                continue
            dataType = dataTypes.get(dataType, dataType)
            downloadURL = downloadTemplate.replace("PROJECT_CODE", projectId).replace("DATA_TYPE", dataTypes.get(dataType, dataType))
            downloadFile(downloadURL, downloadDir, clear=clear)
        count += 1
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o','--output', default=None, help="Output directory")
    parser.add_argument('-s','--skipTypes', default="meth_array", help="Do not download these dataTypes")
    parser.add_argument('-c','--clear', help='Delete existing downloads', action='store_true', default=False)
    options = parser.parse_args()
    
    downloadProjects(options.output, options.skipTypes.split(","), options.clear)