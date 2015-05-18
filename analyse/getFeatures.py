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

def getGenes(inPath, outPath):
    features = getFeatures(inPath)
    mapping = getMapping()
    for feature in features:
        print feature, mapping.get(feature[1])
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