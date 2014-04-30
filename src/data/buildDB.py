import csv, sqlite3
import re
import gzip
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
import downloadICGC
#dataPath = os.path.expanduser("~/data/CAMDA2014-data/ICGC/Breast_Invasive_Carcinoma-TCGA-US/")
#dataPath = settings.DATA_PATH
#dbName = settings.DB_NAME
#dbPath = os.path.join(settings.DATA_PATH, settings.DB_NAME)

def compileRegExKeys(dictionary):
    newDict = {}
    if dictionary != None:
        for key in dictionary:
            if key is not int:
                newDict[re.compile(key)] = dictionary[key]
            else:
                newDict[key] = dictionary[key]
    return newDict

def defineColumns(header, selectedColumns=None, columnTypes=None, defaultType="text"):
    columns = []
    columnTypes = compileRegExKeys(columnTypes)
    for i in range(len(header)):
        if selectedColumns and header[i] not in selectedColumns: # filter
            continue
        if i in columnTypes:
            columns.append((header[i].replace(" ", "_"), columnTypes[i]))
        else:
            matched = False
            for key in columnTypes:
                if key is not int and key.match(header[i]):
                    columns.append((header[i].replace(" ", "_"), columnTypes[key]))
                    matched = True
                    break
            if not matched:
                columns.append((header[i].replace(" ", "_"), defaultType))
    return columns

def defineSQLTable(tableName, columns, primaryKey = None, foreignKeys=None):
    s = "CREATE TABLE IF NOT EXISTS " + tableName + "(" + ",".join([x[0] + " " + x[1] for x in columns])
    if primaryKey != None:
        s += ", PRIMARY KEY (" + ",".join(primaryKey) + ")"
    if foreignKeys != None:
        for key in sorted(foreignKeys.keys()):
            if isinstance(foreignKeys[key], basestring):
                foreignTable = foreignKeys[key]
                foreignColumn = key
            else:
                foreignTable = foreignKeys[key][0]
                foreignColumn = foreignKeys[key][1]
            s += ", FOREIGN KEY(" + key + ") REFERENCES " + foreignTable + "(" + foreignColumn + ")"
    s += ");"
    #print s
    return s

def defineSQLInsert(tableName, columns, ignoreExisting=True):
    if ignoreExisting:
        s = "INSERT OR IGNORE INTO "
    else:
        s = "INSERT INTO "
    return s + tableName + "(" + ",".join([x[0] for x in columns]) + ")" + " values (" + ",".join(["?"]*len(columns)) + ")"

def processLine(csvReader):
    for line in csvReader:
        print line
        yield line

def tableFromCSV(dbName, tableName, csvFileName, selectedColumns=None, columnTypes=None, primaryKey=None, foreignKeys=None, drop=False):  
    con = sqlite3.connect(dbName)
    if csvFileName.endswith(".gz"):
        csvFile = gzip.open(csvFileName, 'rb')
    else:
        csvFile = open(csvFileName, 'rb')
    data = csv.reader(csvFile, delimiter='\t')
    header = data.next()
    
    columns = defineColumns(header, selectedColumns, columnTypes)
    if drop:
        con.execute("DROP TABLE IF EXISTS " + tableName + ";")
    con.execute(defineSQLTable(tableName, columns, primaryKey, foreignKeys))
    insert = defineSQLInsert(tableName, columns)
    #print insert
    con.executemany(insert, processLine(data))
    
    csvFile.close()
    con.commit()
    con.close()

def initDB(dbName):
    tableFromCSV(dbName, "project_ftp_directory", 
                 os.path.join(os.path.dirname(os.path.abspath(__file__)), "project_codes.tsv"),
                 None, None,
                 ["Project_Code"])     
    tableFromCSV(dbName, "project", 
                 os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects_2014_04_28_05_58_25.tsv"),
                 None, {"SSM|CNSM|STSM|SGV|METH|EXP|PEXP|miRNA|JCN|Publications":"int"},
                 ["Project_Code"])

def addProject(dbName, projectCode):
    print "Adding project", projectCode, "to database", dbName
    downloadICGC.downloadProject(projectCode) # Update the local files
    for table in sorted(settings.TABLE_FILES.keys()):
        if table in settings.TABLE_FORMAT:
            format = settings.TABLE_FORMAT[table]
            tableFile = downloadICGC.getProjectPath(projectCode, table=table)
            if not os.path.exists(tableFile):
                continue
            print "Updating table", table, "from", tableFile
            tableFromCSV(dbName, table, tableFile, format.get("columns", None), format.get("types", None), format.get("primary_key", None), format.get("foreign_keys", None))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Import ICGC data')
    parser.add_argument('-p','--project', help='ICGC project code', default=None)
    parser.add_argument('-c','--clear', help='Delete existing database', action='store_true', default=False)
    parser.add_argument('-d','--database', help='Database location', default=None)
    args = parser.parse_args()
    
    if args.database == None:
        if not os.path.exists(settings.DB_CACHE):
            os.makedirs(settings.DB_CACHE)
        dbPath = os.path.join(settings.DB_CACHE, args.project + ".sqlite")
    else:
        dbPath = args.database
    if args.clear and os.path.exists(dbPath):
        os.remove(dbPath)
    if not os.path.exists(os.path.dirname(dbPath)):
        os.makedirs(os.path.dirname(dbPath))
    initDB(dbPath)
    if args.project != None:
        addProject(dbPath, args.project)
    
# tableFromCSV(dataPath + dbName, "clinical", dataPath + "clinical.BRCA-US.tsv",
#              {".*_age.*":"int", ".*_time.*":"int", ".*_interval.*":"int"},
#              ["icgc_specimen_id"])
# tableFromCSV(dataPath + dbName, "clinicalsample", dataPath + "clinicalsample.BRCA-US.tsv",
#              {".*_age.*":"int", ".*_time.*":"int", ".*_interval.*":"int"},
#              ["icgc_sample_id"], 
#              {"icgc_specimen_id":"clinical"})
# tableFromCSV(dataPath + dbName, "simple_somatic_mutation_open", dataPath + "simple_somatic_mutation.open.BRCA-US.tsv",
#              {"chromosome.*":"int"},
#              ["icgc_mutation_id"], 
#              {"icgc_specimen_id":"clinical"})