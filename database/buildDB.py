import sys, os
import json
import gzip
import csv
from test import getProjectFiles
import dataset

def openDB(dbPath, clear=False):
    if clear and os.path.exists(dbPath):
        os.remove(dbPath)
    dbPath = "sqlite:///" + os.path.abspath(dbPath)
    print "Opening DB at", dbPath, "(clear:" + str(clear) + ")"
    return dataset.connect(dbPath)

def getTable(db, dataType, fieldNames):
    icgcKey = "icgc_" + dataType + "_id"
    if icgcKey in fieldNames:
        return db.get_table(dataType, icgcKey, "String")
    else:
        return db.get_table(dataType)

def insertRows(db, dataType, fieldNames, rows, chunkSize=0):
    if len(rows) >= chunkSize and len(rows) >= 0:
        table = getTable(db, dataType, fieldNames)
        print "Inserting", len(rows), "rows to", table
        if chunkSize < 1000:
            chunkSize = 1000
        table.insert_many(rows, chunk_size=chunkSize)
        rows[:] = []

def loadCSV(dataType, csvFileName, db, delimiter='\t'):
    if csvFileName.endswith(".gz"):
        csvFile = gzip.open(csvFileName, 'rb')
    else:
        csvFile = open(csvFileName, 'rb')
    reader = csv.DictReader(csvFile, delimiter=delimiter)
    fieldNames = reader.fieldnames
    #fieldTypes = {}
    #for key in fieldNames:
    #    fieldTypes[key] = int
    rows = []
    for row in reader:
        #print(row)
        for key in fieldNames:
            stringValue = row[key]
            try:
                row[key] = float(stringValue)
                if stringValue.isdigit():
                    row[key] = int(stringValue)
            except ValueError:
                if stringValue.strip() == "":
                    row[key] = None
        rows.append(row)
        insertRows(db, dataType, fieldNames, rows, 100000)
    insertRows(db, dataType, fieldNames, rows)
    csvFile.close()

def importProjects(downloadDir, databaseDir, skipTypes, clear=False):
    with open(os.path.join(downloadDir, 'projects.json')) as f:    
        projects = json.load(f)["hits"]
    
    db = openDB(databaseDir, True)
    
    count = 0
    for project in projects:
        count += 1
        print "Processing project",  project["id"], "(" + str(count) + "/" + str(len(projects)) + ")"
        projectFiles = getProjectFiles(project)
        for dataType, downloadURL in projectFiles:
            dataFile = os.path.join(downloadDir, os.path.basename(downloadURL))
            print "Importing '" + dataType + "' from", dataFile
            loadCSV(dataType, dataFile, db)
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i','--input', default=None, help="Download directory")
    parser.add_argument('-o','--output', default=None, help="Path to database")
    parser.add_argument('-s','--skipTypes', default="meth_array,meth_exp", help="Do not download these dataTypes")
    parser.add_argument('-c','--clear', help='Delete existing database', action='store_true', default=False)
    options = parser.parse_args()
    
    importProjects(options.input, options.output, options.skipTypes.split(","), options.clear)