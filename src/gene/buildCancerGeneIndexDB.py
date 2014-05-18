import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
import data.buildDB as DB
import utils.download as download
import xml.etree.cElementTree as ET
import zipfile
from collections import OrderedDict

def iterparse(xml, tag):
    for event, elem in ET.iterparse(xml): # get end events
        if elem.tag == tag:
            yield elem
            elem.clear()

def preprocessAliasValues(tableName, elem, valueLists):
    primaryName = elem.find("HUGOGeneSymbol").text
    return [[primaryName, primaryName]] + valueLists

def processGeneEntries(xmlFile, dbPath):
    con = DB.connect(dbPath)
    tableValuePaths = OrderedDict()
    inserts = {}
    for tableName in sorted(settings.CGI_TABLES.keys()):
        columns = getColumns(tableName)
        inserts[tableName] = DB.defineSQLInsert(tableName, columns)
        columnToElement = {v:k for k, v in settings.CGI_TABLES[tableName]["columns"].items()}
        valueElementPaths = []
        for i in range(len(columns)):
            valueElementPaths.append(columnToElement[columns[i][0]])
        tableValuePaths[tableName] = valueElementPaths
    for elem in iterparse(xmlFile, tag='GeneEntry'):
        for tableName in tableValuePaths:
            valuePaths = tableValuePaths[tableName]
            valueLists = []
            if "elements" in settings.CGI_TABLES[tableName]:
                listElemPath = settings.CGI_TABLES[tableName]["elements"]
                elemList = elem.findall(listElemPath)
            else:
                listElemPath = ""
                elemList = [elem]
            for listElem in elemList:
                values = []
                for valueElementPath in valuePaths:
                    valueElementPath = valueElementPath.replace(listElemPath, "").strip("/")
                    if len(valueElementPath) > 0:
                        if valueElementPath.startswith("../"):
                            valueElem = elem.find(valueElementPath.strip("../"))
                        else:
                            valueElem = listElem.find(valueElementPath)
                    else:
                        valueElem = listElem
                    if valueElem != None:
                        values.append(valueElem.text)
                    else:
                        values.append(None)
                #print inserts[tableName]
                #print values
                #con.execute(inserts[tableName], values)
                valueLists.append(values)
            if "preprocess" in settings.CGI_TABLES[tableName]:
                valueLists = settings.CGI_TABLES[tableName]["preprocess"](tableName, elem, valueLists)
            #print inserts[tableName]
            #print valueLists
            con.executemany(inserts[tableName], valueLists)
        print elem.find("HUGOGeneSymbol").text
    con.commit()
    con.close()

def getColumns(tableName):
    table = settings.CGI_TABLES[tableName]
    return DB.defineColumns([table["columns"][c] for c in table["columns"]])

def initDB(dbPath, clear=True):
    # Initialize the database
    if clear and os.path.exists(dbPath):
        print "Removing existing database", dbPath
        os.remove(dbPath)
    if not os.path.exists(os.path.dirname(dbPath)):
        os.makedirs(os.path.dirname(dbPath))
    con = DB.connect(dbPath)
    
    for tableName in sorted(settings.CGI_TABLES.keys()):
        columns = getColumns(tableName)
        table = settings.CGI_TABLES[tableName]
        con.execute(DB.defineSQLTable(tableName, columns, table.get("primary_key", None)))
        if "indices" in table:
            DB.addIndices(con, tableName, table["indices"])
    return con

def makeCountTables(filename):
    con = DB.connect(filename)
    con.execute("""
    CREATE TABLE disease AS
    SELECT hugo_gene_symbol, matched_disease_term, nci_disease_concept_code, organism, COUNT(*) 
    AS term_count
    FROM sentence
    GROUP BY hugo_gene_symbol, matched_disease_term, nci_disease_concept_code, organism 
    ORDER BY hugo_gene_symbol;
    """)
    DB.addIndices(con, "disease", ["hugo_gene_symbol"])
    con.commit()
    con.close()

def buildDB(filename, downloadDir):
    initDB(filename)
    
    if downloadDir == None:
        downloadDir = settings.CGI_DOWNLOAD_PATH
    diseaseFile = download.download(settings.CGI_GENE_DISEASE_FILE, downloadDir)
    zf = zipfile.ZipFile(diseaseFile, "r")
    #print zf.namelist()
    #sys.exit()
    
    item = os.path.basename(diseaseFile).split(".")[0] + ".xml"
    processGeneEntries(zf.open(item), filename)
    zf.close()
    makeCountTables(filename)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Import ICGC data')
    parser.add_argument('-d','--directory', default=settings.CGI_DOWNLOAD_PATH)
    parser.add_argument('-c','--clear', help='Delete existing database', action='store_true', default=False)
    parser.add_argument('-b','--database', help='Database location', default=settings.CGI_DB_PATH)
    options = parser.parse_args()
    
    #initDB(options.database)
    buildDB(options.database, options.directory)