import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
import data.buildDB as DB
import data.result as result

def getCancerGenes(con, geneName):
    geneSymbols = con.execute("SELECT DISTINCT(hugo_gene_symbol) FROM gene_alias WHERE alias = ?", (geneName,))
    mappings = []
    for symbol in geneSymbols:
        symbol = symbol["hugo_gene_symbol"]
        for row in con.execute("SELECT * FROM disease WHERE hugo_gene_symbol = ?", (symbol,)):
            #mapping = {}
            #for key in row.keys():
            #    mapping[key] = row[key]
            mapping = str([x for x in row])
            mappings.append(mapping)
    return mappings

def analyze(meta, dbPath, resultPath):
    meta = result.getMeta(meta)
    con = DB.connect(dbPath)
    features = meta["features"]
    count = 1
    numFeatures = len(features)
    for featureName in features:
        if not isinstance(features[featureName], int):
            print "Processing feature", featureName, str(count) + "/" + str(numFeatures)
            geneName = None
            if featureName.startswith("EXP:"):
                geneName = featureName.split(":")[1]
            if geneName != None:
                mappings = getCancerGenes(con, geneName)
                result.setValue(features[featureName], "CancerGeneIndex", mappings)
        count += 1
    if resultPath != None:
        result.saveMeta(meta, resultPath)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-m','--meta', help='Metadata input file name (optional)', default=None)
    parser.add_argument('-b','--database', help='NCI Cancer Gene Index database location', default=settings.CGI_DB_PATH)
    parser.add_argument('-r', '--result', help='Output file for detailed results (optional)', default=None)
    options = parser.parse_args()
    
    analyze(options.meta, options.database, options.result)