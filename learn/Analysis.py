import os
import csv
import matplotlib.pyplot as plt
from Meta import Meta

class COSMICAnalysis():
    def __init__(self, dataPath=None):
        self.censusPath = None
        self.mappingPath = None
        self.dataPath = dataPath
        self.cosmic = None
        self.mapping = None
        
    def getFeatureWeights(self, importances):
        hidden = {}
        train = {}
        for importance in importances:
            index = importance["feature"]
            if importance["set"] == "train":
                if index not in train:
                    train[index] = []
                train[index].append(importance["value"])
            elif importance["set"] == "hidden":
                assert index not in hidden
                hidden[index] = importance["value"]
            else:
                raise Exception("Unknown set for importance")
        for key in train:
            train[key] = sum(train[key]) / float(len(train[key]))
        return train, hidden
        
    def analyse(self, inDir, fileStem=None, hidden=False):
        if fileStem == None:
            fileStem = "examples"
        self._loadCOSMIC()
        self._loadMapping()
        meta = Meta(os.path.join(inDir, fileStem + ".meta.sqlite"))
        print "Loading features"
        features = meta.db["feature"].all()
        importances = meta.db["importance"].all()
        print "Calculating weights:",
        trainWeights, hiddenWeights = self.getFeatureWeights(importances)
        print len(trainWeights), len(hiddenWeights)
        weights = hiddenWeights if hidden else trainWeights
        exampleSet = "hidden" if hidden else "train"
        meta.drop("cosmic", 100000)
        featureCount = 0
        hitCount = 0
        rows = []
        hits = []
        print "Detecting hits"
        for feature in features:
            featureCount += 1
            featureId = feature["id"]
            if feature["id"] not in weights:
                continue
            featureType, geneId, mutationType = feature["name"].split(":")
            geneName = self.mapping.get(geneId, "")
            hit = self.cosmic.get(geneName)
            if hit:
                hitCount += 1
                hits.append(featureCount)
            rows.append({"id":featureId, "weight":weights[featureId], "hit":hit, "set":exampleSet})
        rows = sorted(rows, key=lambda k: k['weight'])
        meta.insert_many("cosmic", rows)
        print "Detected", hitCount, "hits among", featureCount, "features"
        self._visualize(hits, os.path.join(inDir, fileStem + "-cosmic-hist.png"))
        self._visualize(hits, os.path.join(inDir, fileStem + "-cosmic-hist.pdf"))

    def _visualize(self, hits, outPath):
        num_bins = 100
        # the histogram of the data
        n, bins, patches = plt.hist(hits, bins=num_bins, facecolor='blue')#, facecolor='green', alpha=0.5, normed=1)
        plt.xlabel('Feature Importance Rank')
        plt.ylabel('Cancer Census Genes / ' + str(num_bins) +  ' features')
        plt.title(r'COSMIC Cancer Gene Census Frequency')
        #plt.show()
        if outPath != None:
            plt.savefig(outPath)
    
    def _loadMapping(self):
        self.mapping = {}
        filePath = self.censusPath
        if filePath == None:
            filePath = os.path.join(self.dataPath, "ensembl-gene-to-name.tsv")
        print "Reading ENSEMBL to gene name mapping from", filePath
        f = open(filePath, "rt")
        f.readline() # skip headers
        lines = f.readlines()
        f.close()
        for line in lines:
            splits = line.split()
            self.mapping[splits[0]] = splits[1]
        return self.mapping
    
    def _loadCOSMIC(self):
        self.cosmic = {}
        filePath = self.censusPath
        if filePath == None:
            filePath = os.path.join(self.dataPath, "cancer_gene_census.csv")
        print "Reading COSMIC cancer gene census from", filePath
        with open(filePath, "rU") as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            reader.next() # skip headers
            for row in reader:
                assert row[0] not in self.cosmic
                self.cosmic[row[0]] = row
        return self.cosmic