import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
import data.buildDB as DB
import utils.download as download
import xml.etree.cElementTree as ET
import zipfile

def iterparse(xml, tag):
    for event, elem in ET.iterparse(xml): # get end events
        if elem.tag == tag:
            yield elem
            elem.clear()

# def process_element(elem):
#     print elem
#     #print elem.xpath( 'description/text( )' )

def buildDB(filename, downloadDir):
    if downloadDir == None:
        downloadDir = settings.CGI_DOWNLOAD_PATH
    diseaseFile = download.download(settings.CGI_GENE_DISEASE_FILE, downloadDir)
    zf = zipfile.ZipFile(diseaseFile, "r")
    #print zf.namelist()
    #sys.exit()
    
    item = os.path.basename(diseaseFile).split(".")[0] + ".xml"
    for elem in iterparse(zf.open(item), tag='GeneEntry'):
        print elem
    zf.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Import ICGC data')
    parser.add_argument('-d','--directory', default=settings.CGI_DOWNLOAD_PATH)
    parser.add_argument('-c','--clear', help='Delete existing database', action='store_true', default=False)
    parser.add_argument('-b','--database', help='Database location', default=settings.CGI_DB_PATH)
    options = parser.parse_args()
    
    buildDB(options.database, options.directory)