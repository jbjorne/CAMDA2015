import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
import data.buildDB as DB
import data.result as result

def getCancerGenes(con, geneName):
    geneSymbols = con.execute("SELECT DISTINCT(hugo_gene_symbol) FROM gene_alias WHERE alias = ?", (geneName,))
    analysis = {}
    terms = []
    count = 0
    for symbol in geneSymbols:
        symbol = symbol["hugo_gene_symbol"]
        for row in con.execute("SELECT * FROM disease WHERE hugo_gene_symbol = ?", (symbol,)):
            #mapping = {}
            #for key in row.keys():
            #    mapping[key] = row[key]
            count += row["term_count"]
            terms.append(str([x for x in row]))
    analysis["terms"] = terms
    analysis["term_count"] = count
    return analysis

def getCancerGeneCoverage(con, geneNames):
    foundCount = 0
    for geneName in geneNames:
        print geneName
        geneSymbols = con.execute("SELECT DISTINCT(hugo_gene_symbol) FROM gene_alias WHERE alias = ?", (geneName,))
        for symbol in geneSymbols:
            symbol = symbol["hugo_gene_symbol"]
            found = False
            for row in con.execute("SELECT * FROM disease WHERE hugo_gene_symbol = ?", (symbol,)):
                found = True
                break
            print symbol, found
            if found:
                foundCount += 1
    return foundCount / float(len(geneNames))

def analyzeTermCoverage(features):
    selected = {}
    for featureName in features:
        if not isinstance(features[featureName], int) and getGeneName(featureName) != None:
            selected[featureName] = features[featureName]
    bestByFold = {}
    bestByFold["sort"] = []
    for i in range(1,6):
        bestByFold["sort-" + str(i)] = []
    for featureName in selected:
        feature = selected[featureName]
        importances = feature["importances"]
        for fold in importances:
            if not fold in bestByFold:
                bestByFold[fold] = []
            bestByFold[fold].append((importances[fold], featureName))
        bestByFold["sort"].append((feature["sort"], featureName))
        for i in range(len(importances), 6, 1):
            bestByFold["sort-"+str(i)].append((feature["sort"], featureName))
    analysis = {}
    numSteps = 10
    for fold in bestByFold:
        bestByFold[fold] = sorted(bestByFold[fold], reverse=True)
        step = len(bestByFold[fold]) / numSteps
        analysis[fold] = []
        for i in range(numSteps):
            slice = bestByFold[fold][i*step:(i+1)*step]
            sumMapped = 0
            for featureName in [x[1] for x in slice]:
                #if "CancerGeneIndex" in selected[featureName] and "term_count" in selected[featureName]["CancerGeneIndex"]
                if selected[featureName]["CancerGeneIndex"]["term_count"] > 0:
                    sumMapped += 1
            if len(slice) > 0:
                fraction = float(sumMapped) / len(slice)
            else:
                fraction = 0
            s = str(i) + "=" + str(fraction) + " (" + str(len(slice)) + "/" + str(len(bestByFold[fold])) + ")"
            #s += str([x for x in slice])
            analysis[fold].append(s)
    return analysis

def getGeneName(featureName):
    geneName = None
    if featureName.startswith("EXP:"):
        featureBody = featureName.split(":")[1]
        if not featureBody.startswith("ENSG"):
            geneName = featureBody
    return geneName

def analyze(meta, dbPath, resultPath):
    meta = result.getMeta(meta)
    con = DB.connect(dbPath)
    result.sortFeatures(meta)
    features = meta["features"]
    count = 1
    numFeatures = len(features)
    nonSelected = []
    for featureName in features:
        if not isinstance(features[featureName], int):
            print "Processing feature", featureName, str(count) + "/" + str(numFeatures)
            geneName = getGeneName(featureName)
            if geneName != None:
                mappings = getCancerGenes(con, geneName)
                result.setValue(features[featureName], "CancerGeneIndex", mappings)
        else:
            geneName = getGeneName(featureName)
            if geneName != None:
                nonSelected.append(geneName)
        count += 1
    result.setValue(meta, "CancerGeneIndex", analyzeTermCoverage(features), "analysis")
    result.setValue(meta["analysis"], "non-selected", getCancerGeneCoverage(con, nonSelected), "CancerGeneIndex")
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