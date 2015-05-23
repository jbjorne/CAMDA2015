import csv
import matplotlib.pyplot as plt

def visualize(hits, outPath):
    num_bins = 100
    # the histogram of the data
    n, bins, patches = plt.hist(hits, bins=num_bins, facecolor='blue')#, facecolor='green', alpha=0.5, normed=1)
    plt.xlabel('Feature Importance Rank')
    plt.ylabel('Cancer Census Genes / ' + str(num_bins) +  ' features')
    plt.title(r'COSMIC Cancer Gene Census Frequency')
    #plt.show()
    if outPath != None:
        plt.savefig(outPath)

def getFeatures(inPath, featureTags=["SSM", "code"], maxCount=None):
    f = open(inPath, "rt")
    section = None
    features = []
    for line in f:       
        line = line.strip()
        if line == "\"features\": {":
            section = "features"
        if section == "features":
            match = False
            for tag in featureTags:
                if tag in line and "{" in line:
                    feature = line.split("\"")[1]
                    feature = feature.split(":")
                    while len(feature) < 3:
                        feature += [""]
                    features.append(feature)
                    break
            if match and maxCount != None and len(features) >= maxCount:
                break
    f.close()
    return features

def getMapping():
    mapping = {}
    f = open("ensembl-gene-to-name.tsv")
    f.readline() # skip headers
    lines = f.readlines()
    f.close()
    for line in lines:
        splits = line.split()
        mapping[splits[0]] = splits[1]
    return mapping

def getCOSMIC(censusPath=None):
    cosmic = {}
    if censusPath == None:
        censusPath = "cancer_gene_census.csv"
    with open(censusPath, "rU") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        reader.next() # skip headers
        for row in reader:
            assert row[0] not in cosmic
            print row
            cosmic[row[0]] = row
            #for name in set([x for x in row[-1].split(",") if x != ""]):
            #    assert name not in cosmic, ("name", name)
            #    cosmic[name] = row
    return cosmic

def getGenes(inPath, outPath, censusPath=None):
    features = getFeatures(inPath)
    mapping = getMapping(censusPath)
    cosmic = getCOSMIC()
    if outPath:
        out = open(outPath, "wt")
    processed = []
    featureCount = 0
    hitCount = 0
    hits = []
    for feature in features:
        featureCount += 1
        name = mapping.get(feature[1], "")
        processed = [str(featureCount)] + [feature[1], name, feature[2].replace("_", " ")] 
        hit = cosmic.get(name)
        if hit != None:
            processed += ["\\bullet"]
            hitCount += 1
            hits.append(featureCount) #hits.append(1)
        else:
            processed += [""]
            #hits.append(0)
        #processed.append(str(float(hitCount) / featureCount))
        out.write(" & ".join(processed) + " \\\\" + "\n")
    visualize(hits, outPath + "-hist.png")
    visualize(hits, outPath + "-hist.pdf")
#     for feature in features:
#         if feature[1] in mapping:
#             print mapping[feature[1]]
#         else:
#             print feature
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i','--input', help='Input file in JSON format', default=None)
    parser.add_argument('-c','--census', help='COSMIC cancer gene census "cancer_gene_census.csv" file', default=None)
    parser.add_argument('-o','--output', help='Output file stem', default=None)
    options = parser.parse_args()
    
    getGenes(options.input, options.output, options.census)