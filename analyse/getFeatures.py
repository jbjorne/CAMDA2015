import csv

def getFeatures(inPath, featureTag="SSM", maxCount=50):
    f = open(inPath)
    section = None
    features = []
    for line in f:
        line = line.strip()
        if line == "\"features\": {":
            section = "features"
        
        if section == "features" and featureTag in line:
            feature = line.split("\"")[1]
            feature = feature.split(":")
            features.append(feature)
            if len(features) >= maxCount:
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

def getCOSMIC():
    cosmic = {}
    with open("cancer_gene_census.csv", "rU") as csvfile:
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

def getGenes(inPath, outPath):
    features = getFeatures(inPath)
    mapping = getMapping()
    cosmic = getCOSMIC()
    for feature in features:
        name = mapping.get(feature[1])
        print feature, name, cosmic.get(name)
    for feature in features:
        if feature[1] in mapping:
            print mapping[feature[1]]
        else:
            print feature
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i','--input', help='', default=None)
    parser.add_argument('-o','--output', help='', default=None)
    options = parser.parse_args()
    
    getGenes(options.input, options.output)