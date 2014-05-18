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

def processGeneEntries(xmlFile):
    for elem in iterparse(zf.open(item), tag='GeneEntry'):
        print elem

def initDB(dbPath, clear=True):
    # Initialize the database
    if clear and os.path.exists(dbPath):
        print "Removing existing database", dbPath
        os.remove(dbPath)
    if not os.path.exists(os.path.dirname(dbPath)):
        os.makedirs(os.path.dirname(dbPath))
    con = DB.connect(dbPath)
    
    for tableName in sorted(settings.CGI_TABLES.keys()):
        table = settings.CGI_TABLES[tableName]
        #columns = []
        #columnTypes = []
        #for column in table:
        #    if isinstance(table[column], basestring):
        #        columns.append(table[column])
        #        columnTypes.append({table[column]:""})
        columns = DB.defineColumns([table["columns"][c] for c in table["columns"]])
        print columns
        print DB.defineSQLTable(tableName, columns, table["primary_key"])
        con.execute(DB.defineSQLTable(tableName, columns, table["primary_key"]))
    return con

def buildDB(filename, downloadDir):
    if downloadDir == None:
        downloadDir = settings.CGI_DOWNLOAD_PATH
    diseaseFile = download.download(settings.CGI_GENE_DISEASE_FILE, downloadDir)
    zf = zipfile.ZipFile(diseaseFile, "r")
    #print zf.namelist()
    #sys.exit()
    
    item = os.path.basename(diseaseFile).split(".")[0] + ".xml"
    processGeneEntries(zf.open(item))
    zf.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Import ICGC data')
    parser.add_argument('-d','--directory', default=settings.CGI_DOWNLOAD_PATH)
    parser.add_argument('-c','--clear', help='Delete existing database', action='store_true', default=False)
    parser.add_argument('-b','--database', help='Database location', default=settings.CGI_DB_PATH)
    options = parser.parse_args()
    
    initDB(options.database)
    #buildDB(options.database, options.directory)