import sys, os
import json
import gzip
import csv
from test import getProjectFiles
import dataset

TABLE_FORMAT = {
"exp_array":{
    "columns":["icgc_donor_id", "project_code", "icgc_specimen_id", "gene_id", "normalized_expression_value", "fold_change"],
    "types":{"normalized_expression_value":float, "fold_change":float}},
"exp_seq":{
    "columns":["icgc_donor_id", "project_code", "icgc_specimen_id", "gene_id", "normalized_read_count", "fold_change"],
    "types":{"normalized_read_count":float, "fold_change":float}},
}

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
        print "Inserting", len(rows), "rows to", str(table) + "... ",
        if chunkSize < 1000:
            chunkSize = 1000
        table.insert_many(rows, chunk_size=chunkSize)
        rows[:] = []
        print "done"

def loadCSV(dataType, csvFileName, db, delimiter='\t'):
    if csvFileName.endswith(".gz"):
        csvFile = gzip.open(csvFileName, 'rb')
    else:
        csvFile = open(csvFileName, 'rb')
    reader = csv.DictReader(csvFile, delimiter=delimiter)
    fieldNames = reader.fieldnames
    fieldTypes = None
    hasFormat = dataType in TABLE_FORMAT
    if hasFormat:
        for fieldName in TABLE_FORMAT[dataType]["columns"]:
            assert fieldName in fieldNames
        fieldNames = TABLE_FORMAT[dataType]["columns"]
        fieldTypes = TABLE_FORMAT[dataType]["types"]
    rows = []
    for row in reader:
        if hasFormat:
            row = {key: row[key] for key in fieldNames}
        #print(row)
        for key in fieldNames:
            stringValue = row[key]
            if stringValue == "":
                row[key] = None
            elif fieldTypes:
                if key in fieldTypes:
                    row[key] = fieldTypes[key](stringValue)
            else: # no predefined types
                if stringValue.isdigit():
                    row[key] = int(stringValue)
                else:
                    try: row[key] = float(stringValue)
                    except ValueError: pass
        rows.append(row)
        insertRows(db, dataType, fieldNames, rows, 500000)
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
            dataFilePath = os.path.join(downloadDir, os.path.basename(downloadURL))
            if os.path.exists(dataFilePath):
                print "Importing '" + dataType + "' from", dataFilePath
                loadCSV(dataType, dataFilePath, db)
            else:
                print "Data type '" + dataType + "' does not have file", dataFilePath
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i','--input', default=None, help="Download directory")
    parser.add_argument('-o','--output', default=None, help="Path to database")
    parser.add_argument('-s','--skipTypes', default="meth_array,meth_exp", help="Do not download these dataTypes")
    parser.add_argument('-c','--clear', help='Delete existing database', action='store_true', default=False)
    options = parser.parse_args()
    
    importProjects(options.input, options.output, options.skipTypes.split(","), options.clear)