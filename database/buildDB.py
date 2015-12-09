import sys, os
import json
import gzip
import csv
from test import getProjectFiles, basicDataTypes
import dataset
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils.Stream as Stream
import time

# import subprocess
# import cStringIO
# io_method = cStringIO.StringIO

TABLE_FORMAT = {
"exp_array":{
    "columns":["icgc_donor_id", "project_code", "icgc_specimen_id", "gene_id", 
                        "normalized_expression_value", "fold_change"]},
    #"types":{"normalized_expression_value":float, "fold_change":float}},
"exp_seq":{
    "columns":["icgc_donor_id", "project_code", "icgc_specimen_id", "gene_id", 
                      "normalized_read_count", "fold_change"]},
    #"types":{"normalized_read_count":float, "fold_change":float}},
"mirna_seq":{
    "columns":['icgc_donor_id', 'project_code', 'icgc_specimen_id', 'icgc_sample_id', 
               'analysis_id', 'mirna_id', 'normalized_read_count', 'raw_read_count', 
               'fold_change', 'is_isomir', 'chromosome', 'chromosome_start', 'chromosome_end', 
               'chromosome_strand', 'assembly_version', 'total_read_count']},
"ssm":{
    "columns":['icgc_mutation_id', 'icgc_donor_id', 'project_code', 'icgc_specimen_id', 'icgc_sample_id', 
                  'matched_icgc_sample_id', 'chromosome', 'chromosome_start', 'chromosome_end', 
                  'chromosome_strand', 'assembly_version', 'mutation_type', 'reference_genome_allele', 
                  'mutated_from_allele', 'mutated_to_allele', 'quality_score', 'probability', 
                  'total_read_count', 'mutant_allele_read_count', 'consequence_type', 'aa_mutation', 
                  'cds_mutation', 'gene_affected', 'transcript_affected', 'gene_build_version']},
"cnsm":{
    "skip":["experimental_protocol", "base_calling_algorithm", "alignment_algorithm", "variation_calling_algorithm", "other_analysis_algorithm"]},
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

def insertRows(db, dataType, fieldNames, rows, chunkSize=0, ensureLimit=100000):
    if len(rows) >= chunkSize and len(rows) >= 0:
        tableExists = dataType in db
        if not tableExists and len(rows) > ensureLimit and chunkSize > ensureLimit:
            ensureRows = rows[:ensureLimit]
            rows[:ensureLimit] = []
            insertRows(db, dataType, fieldNames, ensureRows, ensureLimit, ensureLimit)
            tableExists = dataType in db
        table = getTable(db, dataType, fieldNames)
        startTime = time.time()
        print "Inserting", len(rows), "rows to" + (" new" if not tableExists else ""), str(table) + "...",
        if chunkSize < 1000:
            chunkSize = 1000
        table.insert_many(rows, chunk_size=chunkSize, ensure=not tableExists)
        rows[:] = []
        print "done in %.2f" % (time.time() - startTime)

def loadCSV(dataType, csvFileName, db, batchSize=200000, delimiter='\t'):
    if csvFileName.endswith(".gz"):
        csvFile = gzip.open(csvFileName, 'rb')
        #p = subprocess.Popen(["zcat", csvFileName], stdout = subprocess.PIPE)
        #csvFile = io_method(p.communicate()[0])
    else:
        csvFile = open(csvFileName, 'rb')
    reader = csv.DictReader(csvFile, delimiter=delimiter)
    fieldNames = reader.fieldnames[:]
    #fieldTypes = None
    tableFormat = TABLE_FORMAT.get(dataType)
    if tableFormat:
        for fieldName in tableFormat["columns"]:
            assert fieldName in fieldNames
        if "columns" in tableFormat:
            fieldNames = tableFormat["columns"][:]
        if "skip" in tableFormat:
            for key in tableFormat["skip"]:
                if key in fieldNames:
                    fieldNames.remove(key)
        #fieldTypes = tableFormat["types"][:]
    rows = []
    for row in reader:
        if tableFormat:
            row = {key: row[key] for key in fieldNames}
        #print(row)
        for key in fieldNames:
            stringValue = row[key]
            if stringValue == "":
                row[key] = None
            #elif fieldTypes:
            #    if key in fieldTypes:
            #        row[key] = fieldTypes[key](stringValue)
            else: # no predefined types
                if stringValue.isdigit():
                    row[key] = int(stringValue)
                else:
                    try: row[key] = float(stringValue)
                    except ValueError: pass
        rows.append(row)
        insertRows(db, dataType, fieldNames, rows, batchSize)
    insertRows(db, dataType, fieldNames, rows)
    csvFile.close()

def importProjects(downloadDir, databaseDir, skipTypes, limitTypes, batchSize=200000, clear=False):
    with open(os.path.join(downloadDir, 'projects.json')) as f:    
        projects = json.load(f)["hits"]
    
    db = openDB(databaseDir, True)
    
    count = 0
    for project in projects:
        count += 1
        print "Processing project",  project["id"], "(" + str(count) + "/" + str(len(projects)) + ")"
        projectFiles = getProjectFiles(project)
        for dataType, downloadURL in projectFiles:
            if limitTypes and dataType not in limitTypes and dataType not in basicDataTypes:
                print "Skipping data type '" + dataType + "'"
                continue
            elif skipTypes and dataType in skipTypes:
                print "Skipping data type '" + dataType + "'"
                continue
            dataFilePath = os.path.join(downloadDir, os.path.basename(downloadURL))
            if os.path.exists(dataFilePath):
                print "Importing '" + dataType + "' from", dataFilePath
                loadCSV(dataType, dataFilePath, db, batchSize=batchSize)
            else:
                print "Data type '" + dataType + "' does not have file", dataFilePath
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i','--input', default=None, help="Download directory")
    parser.add_argument('-o','--output', default=None, help="Path to database")
    parser.add_argument('-s','--skipTypes', default="meth_array,meth_exp", help="Do not download these dataTypes")
    parser.add_argument('-l','--limitTypes', default=None, help="Use only these datatypes")
    parser.add_argument('-c','--clear', help='Delete existing database', action='store_true', default=False)
    parser.add_argument('-b','--batchSize', type=int, default=200000, help="SQL insert rows")
    options = parser.parse_args()
    
    Stream.openLog(options.output + ".log.txt", clear = True)
    importProjects(options.input, 
                   options.output, 
                   options.skipTypes.split(",") if options.skipTypes else None, 
                   options.limitTypes.split(",") if options.limitTypes else None,
                   options.batchSize,
                   options.clear)