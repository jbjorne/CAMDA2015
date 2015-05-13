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

def defineSQLTable(tableName, columns, primaryKey = None, foreignKeys=None):
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
    return s

def defineSQLInsert(tableName, columns, ignoreExisting=True):
    if ignoreExisting:
        s = "INSERT OR IGNORE INTO "
    else:
        s = "INSERT INTO "
    includedColumns = filter(lambda a: a != None, columns)
    return s + tableName + "(" + ",".join([x[0] for x in includedColumns]) + ")" + " values (" + ",".join(["?"]*len(includedColumns)) + ")"

def addIndices(con, tableName, indices):
    con = connect(con)
    if indices != None:
        for index in indices:
            con.execute("CREATE INDEX IF NOT EXISTS " + tableName + "_" + index + "_index ON " + tableName + "(" + index + ");")
    
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
        #print [x for x in enumerate(line)], len(line), indicesToDelete
        for targetIndex, function in indicesToPreprocess: 
            line[targetIndex] = function(line[targetIndex])
        for i in indicesToDelete:
            del line[i]
        #print line
        yield line

def connect(con):
    if isinstance(con, basestring):
        con = sqlite3.connect(con)
        con.row_factory = sqlite3.Row
    return con

def enumerateValues(con, table, column):
    con = connect(con)
    values = con.execute("SELECT DISTINCT " + column + " FROM " + table)
    return [x[0] for x in values]

def tableFromCSV(dbName, tableName, csvFileName, selectedColumns=None, columnTypes=None, primaryKey=None, foreignKeys=None, preprocess=None, indices=None, drop=False):  
    con = connect(dbName)
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
    con.execute(defineSQLTable(tableName, columns, primaryKey, foreignKeys))
    insert = defineSQLInsert(tableName, columns)
    addIndices(con, tableName, indices)
    #print insert
    con.executemany(insert, processLines(data, columns))
    
    csvFile.close()
    con.commit()
    con.close()

def tableFromDefinition(dbName, tableName, tableFormat, tableFile=None):
    if tableFile == None:
        tableFile = tableFormat["file"]
    print "Updating table", tableName, "from", tableFile
    tableFromCSV(dbName, tableName, tableFile, 
                 tableFormat.get("columns", None), 
                 tableFormat.get("types", None), 
                 tableFormat.get("primary_key", None), 
                 tableFormat.get("foreign_keys", None),
                 tableFormat.get("preprocess", None),
                 tableFormat.get("indices", None))

def initDB(dbName):
    tableFromCSV(dbName, "project_ftp_directory", 
                 os.path.join(os.path.dirname(os.path.abspath(__file__)), "project_codes.tsv"),
                 None, None,
                 ["Project_Code"])     
    tableFromCSV(dbName, "project", 
                 os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects_2014_04_28_05_58_25.tsv"),
                 None, {"SSM|CNSM|STSM|SGV|METH|EXP|PEXP|miRNA|JCN|Publications":"int"},
                 ["Project_Code"])
    #tableFromDefinition(dbName, "cosmic_gene_census", 
    #                    settings.TABLE_FORMAT["cosmic_gene_census"])

def addProject(dbName, projectCode, filePatterns, downloadDir=None, tables = None):
    print "Adding project", projectCode, "to database", dbName
    if downloadDir == None:
        downloadDir = os.path.dirname(dbName)
    downloadICGC.downloadProject(settings.ICGC_URL, projectCode, filePatterns, downloadDir) # Update the local files
    if tables != None:
        tables = set(tables.split(","))
    for table in sorted(settings.TABLE_FILES.keys()):
        if tables != None and table not in tables:
            continue
        if table in settings.TABLE_FORMAT:
            tableFormat = settings.TABLE_FORMAT[table]
            tableFilePath = os.path.join(downloadDir, projectCode, settings.TABLE_FILES[table].replace("%c", projectCode))
            if not os.path.exists(tableFilePath):
                continue
            tableFromDefinition(dbName, table, tableFormat, tableFilePath)

def buildICGCDatabase(dbPath=None, projects="ALL", clear=True, downloadDir=None, tables=None):
    if dbPath == None:
        dbPath = settings.DATA_PATH
    if downloadDir == None:
        downloadDir = os.path.join(settings.DATA_PATH, "download")
    
    print "Building ICGC database"
    # Define locations
    if downloadDir != None and not os.path.exists(downloadDir):
        os.makedirs(downloadDir)
    
    # Initialize the database
    if clear and os.path.exists(dbPath):
        print "Removing existing database", dbPath
        os.remove(dbPath)
    if not os.path.exists(os.path.dirname(dbPath)):
        os.makedirs(os.path.dirname(dbPath))
    initDB(dbPath)
    
    # Get projects
    allProjects, filePatterns = downloadICGC.parseReadme(settings.ICGC_URL, "README.txt", downloadDir)
    
    # Add projects
    if projects != None:
        if isinstance(projects, basestring):
            if projects == "ALL":
                projects = allProjects
            else:
                projects = projects.split(",")
        count = 1
        for project in projects:
            print "Processing project", project, "(" + str(count) + "/" + str(len(projects)) + ")"
            addProject(dbPath, project, filePatterns, downloadDir, tables)
            count += 1

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Import ICGC data')
    parser.add_argument('-d','--directory', default=None)
    parser.add_argument('-p','--project', help='ICGC project code(s) in a comma-separated list or ALL for all projects', default=None)
    parser.add_argument('-c','--clear', help='Delete existing database', action='store_true', default=False)
    parser.add_argument('-b','--database', help='Database location', default=settings.DB_PATH)
    parser.add_argument('-t','--tables', help='Add project data only from the tables in this comma-separated list (optional)', default=None)
    options = parser.parse_args()
    
    buildICGCDatabase(options.database, options.project, options.clear, options.directory)