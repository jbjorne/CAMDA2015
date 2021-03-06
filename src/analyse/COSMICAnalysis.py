import os
from src.analyse.Analysis import Analysis
import csv
import matplotlib.pyplot as plt

class COSMICAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(COSMICAnalysis, self).__init__(dataPath=dataPath)
        self.censusPath = None
        self.mappingPath = None
        self.cosmic = None
        self.mapping = None

    def getFeatureWeights(self, importances):
        hidden = {}
        train = {}
        for importance in importances:
            featureId = importance["feature"]
            if importance["set"] == "train":
                if featureId not in train:
                    train[featureId] = []
                train[featureId].append(importance["value"])
            elif importance["set"] == "hidden":
                assert featureId not in hidden
                hidden[featureId] = importance["value"]
            else:
                raise Exception("Unknown set for importance")
        for key in train:
            train[key] = sum(train[key]) / float(len(train[key]))
        return train, hidden
        
    def analyse(self, inDir, fileStem=None, hidden=False):
        meta = self._getMeta(inDir, fileStem)
        meta.drop("cosmic", 100000)
        self._loadCOSMIC()
        self._loadMapping()
        print "Loading features"
        features = meta.db["feature"].all()
        importances = meta.db["importance"].all()
        print "Calculating weights:",
        trainWeights, hiddenWeights = self.getFeatureWeights(importances)
        print len(trainWeights), len(hiddenWeights)
        weights = hiddenWeights if hidden else trainWeights
        exampleSet = "hidden" if hidden else "train"
        hitCount = 0
        rows = []
        hitRanks = []
        print "Detecting hits"
        for feature in features:
            featureId = feature["id"]
            if feature["id"] not in weights:
                continue
            splits = feature["name"].split(":")
            if len(splits) == 3:
                featureType, geneId, mutationType = feature["name"].split(":")
            else:
                expSeqTag, geneId = feature["name"].split(":")
                mutationType = None
            geneName = geneId
            if geneId.startswith("ENSG"):
                geneName = self.mapping.get(geneId, "")
            hit = self.cosmic.get(geneName)
            row = {"id":featureId, "gene_name":geneName, "gene_id":geneId, "weight":weights[featureId], "set":exampleSet, "mutation":mutationType, "hit":None, "description":None, "entrez":None}
            if hit:
                hitCount += 1
                row.update({"hit":hit["Gene Symbol"], "description":hit["Name"], "entrez":hit["Entrez GeneId"]})
            rows.append(row)
        print "Ranking features"
        rows = sorted(rows, key=lambda k: k['weight'], reverse=True)
        for i in range(len(rows)):
            if rows[i]["hit"] is not None:
                hitRanks.append(i)
        meta.insert_many("cosmic", rows, True)
        print "Detected", hitCount, "hits among", len(rows), "features"
        if fileStem == None:
            fileStem = "examples"
        self._visualize(hitRanks, os.path.join(inDir, fileStem + "-cosmic-hist.png"))
        self._visualize(hitRanks, os.path.join(inDir, fileStem + "-cosmic-hist.pdf"))

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
            reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
                assert row["Gene Symbol"] not in self.cosmic
                self.cosmic[row["Gene Symbol"]] = row
        return self.cosmic
    