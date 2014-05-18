import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
import data.buildDB as DB
import utils.download as download
import lxml.etree as ET
import zipfile

def fast_iter(context, func, *args, **kwargs):
    """
    From http://stackoverflow.com/questions/7171140/using-python-iterparse-for-large-xml-files
    by user unutbu
    
    http://lxml.de/parsing.html#modifying-the-tree
    Based on Liza Daly's fast_iter
    http://www.ibm.com/developerworks/xml/library/x-hiperfparse/
    See also http://effbot.org/zone/element-iterparse.htm
    """
    for event, elem in context:
        func(elem, *args, **kwargs)
        # It's safe to call clear() here because no descendants will be
        # accessed
        elem.clear()
        # Also eliminate now-empty references from the root node to elem
        for ancestor in elem.xpath('ancestor-or-self::*'):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]
    del context


def process_element(elem):
    print elem
    print elem.xpath( 'description/text( )' )

def buildDB(filename, downloadDir):
    if downloadDir == None:
        downloadDir = settings.CGI_DOWNLOAD_PATH
    diseaseFile = download.download(settings.CGI_GENE_DISEASE_FILE, downloadDir)
    zf = zipfile.ZipFile(diseaseFile, "r")
    #print zf.namelist()
    #sys.exit()
    
    item = os.path.basename(diseaseFile).split(".")[0] + ".xml"
    context = ET.iterparse(zf.open(item), tag='GeneEntry' )
    fast_iter(context,process_element)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Import ICGC data')
    parser.add_argument('-d','--directory', default=settings.CGI_DOWNLOAD_PATH)
    parser.add_argument('-c','--clear', help='Delete existing database', action='store_true', default=False)
    parser.add_argument('-b','--database', help='Database location', default=settings.CGI_DB_PATH)
    options = parser.parse_args()
    
    buildDB(options.database, options.directory)