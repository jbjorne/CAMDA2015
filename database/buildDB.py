import sys, os
import json
import gzip
import csv
from test import getProjectFiles

def loadCSV(csvFileName, delimiter='\t'):
    if csvFileName.endswith(".gz"):
        csvFile = gzip.open(csvFileName, 'rb')
    else:
        csvFile = open(csvFileName, 'rb')
    reader = csv.DictReader(csvFile, delimiter=delimiter)
    for row in reader:
        print reader.fieldnames
        print(row)
        sys.exit()
    csvFile.close()

def importProjects(downloadDir, skipTypes, clear=False):
    with open(os.path.join(downloadDir, 'projects.json')) as f:    
        projects = json.load(f)["hits"]
    
    count = 0
    for project in projects:
        count += 1
        print "Processing project",  project["id"], "(" + str(count) + "/" + str(len(projects)) + ")"
        projectFiles = getProjectFiles(project)
        for dataType, downloadURL in projectFiles:
            dataFile = os.path.join(downloadDir, os.path.basename(downloadURL))
            print "Importing '" + dataType + "' from", dataFile
            loadCSV(dataFile)
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i','--input', default=None, help="Download directory")
    parser.add_argument('-o','--output', default=None, help="Path to database")
    parser.add_argument('-s','--skipTypes', default="meth_array,meth_exp", help="Do not download these dataTypes")
    parser.add_argument('-c','--clear', help='Delete existing database', action='store_true', default=False)
    options = parser.parse_args()
    
    importProjects(options.input, options.skipTypes.split(","), options.clear)