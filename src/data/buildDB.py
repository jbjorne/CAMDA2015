import csv, sqlite3
import re
import gzip
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
import downloadICGC
import buildExamples
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

def prepareColumnSelection(selectedColumns, header):
    if selectedColumns != None and selectedColumns[0] == "REVERSE":
        selectedColumns = selectedColumns[1:]
        final = []
        for column in header:
            if column not in selectedColumns:
                final.append(column)
        return final
    else:
        return selectedColumns

def defineColumns(header, selectedColumns=None, columnTypes=None, preprocess=None, defaultType="text"):
    columns = []
    selectedColumns = prepareColumnSelection(selectedColumns, header)
    columnTypes = compileRegExKeys(columnTypes)
    preprocess = compileRegExKeys(preprocess)
    for i in range(len(header)):
        # Column types and selection
        column = None
        if selectedColumns and header[i] not in selectedColumns: # filter
            column = None
        elif i in columnTypes:
            column = (header[i].replace(" ", "_"), columnTypes[i], None)
        else:
            matched = False
            for key in columnTypes:
                if key is not int and key.match(header[i]):
                    column = (header[i].replace(" ", "_"), columnTypes[key], None)
                    matched = True
                    break
            if not matched:
                column = (header[i].replace(" ", "_"), defaultType, None)
        # Preprocessing
        for key in preprocess:
            if column != None and key.match(header[i]):
                column = (column[0], column[1], preprocess[key])
                matched = True
                break
        # add to list
        columns.append(column)
    return columns

def defineSQLTable(tableName, columns, primaryKey = None, foreignKeys=None, indices=None):
    includedColumns = filter(lambda a: a != None, columns)
    s = "CREATE TABLE IF NOT EXISTS " + tableName + "(" + ",".join([x[0] + " " + x[1] for x in includedColumns])
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
    if indices != None:
        for index in indices:
            s += "\nCREATE INDEX IF NOT EXISTS " + index + "_index ON " + tableName + "(" + index + ");"
    #print s
    return s

def defineSQLInsert(tableName, columns, ignoreExisting=True):
    if ignoreExisting:
        s = "INSERT OR IGNORE INTO "
    else:
        s = "INSERT INTO "
    includedColumns = filter(lambda a: a != None, columns)
    return s + tableName + "(" + ",".join([x[0] for x in includedColumns]) + ")" + " values (" + ",".join(["?"]*len(includedColumns)) + ")"

def processLines(csvReader, columns):
    indicesToDelete = []
    indicesToPreprocess = []
    #print columns
    if columns != None:
        for i in range(len(columns)):
            if columns[i] == None:
                indicesToDelete.append(i)
            elif columns[i][2]:
                indicesToPreprocess.append((i, columns[i][2]))
    indicesToDelete.sort(reverse=True) # remove from the end
    #print indicesToDelete
    for line in csvReader:
        for targetIndex, function in indicesToPreprocess: 
            line[targetIndex] = function(line[targetIndex])
        for i in indicesToDelete:
            del line[i]
        #print line
        yield line

def tableFromCSV(dbName, tableName, csvFileName, selectedColumns=None, columnTypes=None, primaryKey=None, foreignKeys=None, preprocess=None, indices=None, drop=False):  
    con = sqlite3.connect(dbName)
    con.row_factory = sqlite3.Row
    if csvFileName.endswith(".gz"):
        csvFile = gzip.open(csvFileName, 'rb')
    else:
        csvFile = open(csvFileName, 'rb')
    data = csv.reader(csvFile, delimiter='\t')
    header = data.next()
    
    columns = defineColumns(header, selectedColumns, columnTypes, preprocess)
    #print columns
    if drop:
        con.execute("DROP TABLE IF EXISTS " + tableName + ";")
    con.execute(defineSQLTable(tableName, columns, primaryKey, foreignKeys, indices))
    insert = defineSQLInsert(tableName, columns)
    #print insert
    con.executemany(insert, processLines(data, columns))
    
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

def addProject(dbName, projectCode, downloadDir=None):
    print "Adding project", projectCode, "to database", dbName
    if downloadDir == None:
        downloadDir = os.path.dirname(dbName)
    downloadICGC.downloadProject(projectCode, downloadDir) # Update the local files
    for table in sorted(settings.TABLE_FILES.keys()):
        if table in settings.TABLE_FORMAT:
            format = settings.TABLE_FORMAT[table]
            tableFile = downloadICGC.getProjectPath(projectCode, downloadDir, table)
            if not os.path.exists(tableFile):
                continue
            print "Updating table", table, "from", tableFile
            tableFromCSV(dbName, table, tableFile, 
                         format.get("columns", None), 
                         format.get("types", None), 
                         format.get("primary_key", None), 
                         format.get("foreign_keys", None),
                         format.get("preprocess", None),
                         format.get("indices", None))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Import ICGC data')
    parser.add_argument('-d','--directory', default=settings.DATA_PATH)
    parser.add_argument('-p','--project', help='ICGC project code', default=None)
    parser.add_argument('-c','--clear', help='Delete existing database', action='store_true', default=False)
    parser.add_argument('-b','--database', help='Database location', default=None)
    args = parser.parse_args()
    
    # Define locations
    if args.directory != None:
        args.directory = os.path.expanduser(args.directory)
    if args.database == None:
        args.database = os.path.join(args.directory, settings.DB_NAME)
    dbPath = args.database
    if args.directory != None and not os.path.exists(args.directory):
        os.makedirs(args.directory)
    
    # Initialize the database
    if args.clear and os.path.exists(dbPath):
        print "Removing existing database", dbPath
        os.remove(dbPath)
    if not os.path.exists(os.path.dirname(dbPath)):
        os.makedirs(os.path.dirname(dbPath))
    initDB(dbPath)
    
    # Add projects
    if args.project != None:
        if args.project == "ALL":
            projects = buildExamples.enumerateValues(dbPath, "project_ftp_directory", "Project_Code")
        else:
            projects = [args.project]
        count = 1
        for project in projects:
            print "Processing project", project, "(" + str(count) + "/" + str(len(projects)) + ")"
            addProject(dbPath, project)
            count += 1
    
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