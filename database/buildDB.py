import sys, os
import json
import gzip
import csv
from test import getProjectFiles, basicDataTypes
import dataset
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils.Stream as Stream
import time

COLUMNS = {
"exp_array":["icgc_donor_id", "project_code", "icgc_specimen_id", "gene_id", 
             "normalized_expression_value", "fold_change"],
"exp_seq":["icgc_donor_id", "project_code", "icgc_specimen_id", "gene_id", 
           "normalized_read_count", "fold_change"],
"mirna_seq":['icgc_donor_id', 'project_code', 'icgc_specimen_id', 'icgc_sample_id', 
             'analysis_id', 'mirna_id', 'normalized_read_count', 'raw_read_count', 
             'fold_change', 'is_isomir', 'chromosome', 'chromosome_start', 'chromosome_end', 
             'chromosome_strand', 'assembly_version', 'total_read_count'],
"ssm":['icgc_mutation_id', 'icgc_donor_id', 'project_code', 'icgc_specimen_id', 'icgc_sample_id', 
       'matched_icgc_sample_id', 'chromosome', 'chromosome_start', 'chromosome_end', 
       'chromosome_strand', 'assembly_version', 'mutation_type', 'reference_genome_allele', 
       'mutated_from_allele', 'mutated_to_allele', 'quality_score', 'probability', 
       'total_read_count', 'mutant_allele_read_count', 'consequence_type', 'aa_mutation', 
       'cds_mutation', 'gene_affected', 'transcript_affected', 'gene_build_version'],
"cnsm":['icgc_donor_id', 'project_code', 'icgc_specimen_id', 'icgc_sample_id', 
        'matched_icgc_sample_id', 'mutation_type', 'copy_number', 'segment_mean', 
        'segment_median', 'chromosome', 'chromosome_start', 'chromosome_end', 
        'assembly_version', 'chromosome_start_range', 'chromosome_end_range', 
        'start_probe_id', 'end_probe_id', 'sequencing_strategy', 'quality_score', 
        'probability', 'is_annotated', 'gene_affected', 'transcript_affected', 
        'gene_build_version', 'seq_coverage'],
"pexp":['icgc_donor_id', 'project_code', 'icgc_specimen_id', 'icgc_sample_id', 
        'analysis_id', 'antibody_id', 'gene_name', 'gene_stable_id', 
        'gene_build_version', 'normalized_expression_level'],
}

def openDB(dbPath, clear=False):
    if clear and os.path.exists(dbPath):
        print "Removing existing database at", dbPath
        os.remove(dbPath)
    dbPath = "sqlite:///" + os.path.abspath(dbPath)
    print "Opening DB at", dbPath
    return dataset.connect(dbPath)

def getTable(db, dataType, fieldNames):
    icgcKey = "icgc_" + dataType + "_id" # for donor, specimen and sample the id is the primary key
    if icgcKey in fieldNames:
        return db.get_table(dataType, icgcKey, "String")
    else:
        return db.get_table(dataType)

def insertRows(db, dataType, fieldNames, rows, chunkSize=0):
    if chunkSize == 0: # insert all available rows
        chunkSize = len(rows)
    # Insert rows if enough are available
    if len(rows) >= chunkSize and len(rows) >= 0:
        tableExists = dataType in db
        table = getTable(db, dataType, fieldNames)
        if not tableExists:
            print "Initializing table", table
            table.insert(rows[0], ensure=True)
            rows[:1] = [] # remove first row
        startTime = time.time()
        print "Inserting", len(rows), "rows to", str(table) + "...",
        table.insert_many(rows, chunk_size=chunkSize, ensure=False)
        rows[:] = [] # clear the cache
        print "done in %.2f" % (time.time() - startTime)

def loadCSV(dataType, csvFileName, db, batchSize=200000, delimiter='\t'):
    # Open the CSV file and read the column headers
    if csvFileName.endswith(".gz"):
        csvFile = gzip.open(csvFileName, 'rb')
    else:
        csvFile = open(csvFileName, 'rb')
    reader = csv.DictReader(csvFile, delimiter=delimiter)
    fieldNames = reader.fieldnames[:] # read column names
    # Determine which columns to include
    columnsToInclude = COLUMNS.get(dataType)
    if columnsToInclude:
        for fieldName in columnsToInclude:
            assert fieldName in fieldNames
        fieldNames = columnsToInclude[:] # redefine column names
    rows = []
    # Read rows from the CSV file
    for row in reader:
        if columnsToInclude:
            row = {key: row[key] for key in fieldNames}
        # Determine data types (all values come from the CSV as strings)
        for key in fieldNames:
            stringValue = row[key]
            if stringValue == "": # check for NULL
                row[key] = None
            elif stringValue.isdigit(): # check for INTEGER
                row[key] = int(stringValue)
            else: # check for REAL
                try: row[key] = float(stringValue)
                except ValueError: pass
        rows.append(row)
        insertRows(db, dataType, fieldNames, rows, batchSize) # When batch size is exceeded, insert the rows to the db
    insertRows(db, dataType, fieldNames, rows) # Insert the last rows
    csvFile.close()

def importProjects(downloadDir, databaseDir, skipTypes, limitTypes, batchSize=200000):
    with open(os.path.join(downloadDir, 'projects.json')) as f:    
        projects = json.load(f)["hits"]
    
    print "*** Initializing the database ***"
    db = openDB(databaseDir, True)
    
    print "*** Importing ICGC projects to the database ***"
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
    
    print "*** Indexing the database ***"
    indexDB(db)
    
def indexDB(db):
    indexKey = "icgc_specimen_id"
    for tableName in db.tables:
        print "Processing table", tableName
        if tableName not in basicDataTypes:
            columns = db[tableName].columns
            if "icgc_specimen_id" in columns:
                indexName = "index_" + tableName + "_" + indexKey
                print "Adding index", indexName, "for table", tableName + "...",
                startTime = time.time()
                db[tableName].create_index([indexKey], indexName)
                print "done in %.2f" % (time.time() - startTime)
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i','--input', default=None, help="Download directory")
    parser.add_argument('-o','--output', default=None, help="Path to database")
    parser.add_argument('-s','--skipTypes', default="meth_array,meth_exp", help="Do not download these dataTypes")
    parser.add_argument('-l','--limitTypes', default=None, help="Use only these datatypes")
    parser.add_argument('-b','--batchSize', type=int, default=200000, help="SQL insert rows")
    options = parser.parse_args()
    
    Stream.openLog(options.output + ".log.txt", clear = True)
    importProjects(options.input, 
                   options.output, 
                   options.skipTypes.split(",") if options.skipTypes else None, 
                   options.limitTypes.split(",") if options.limitTypes else None,
                   options.batchSize)