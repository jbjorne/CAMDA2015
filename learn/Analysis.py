import os
import csv
import matplotlib.pyplot as plt
from Meta import Meta

class COSMICAnalysis():
    def __init__(self, meta=None, dataPath=None):
        self.censusPath = None
        self.mappingPath = None
        self.dataPath = dataPath
        self.cosmic = None
        self.mapping = None
        self.loadMeta(meta)
    
    def loadMeta(self, source):
        if source == None:
            self.meta = None
        elif isinstance(source, basestring):
            self.meta = Meta(source)
        elif isinstance(source, Meta):
            self.meta = source
        else:
            raise Exception("Unknown format for metadata source")
        
    def analyse(self, outPath, fileStem="COSMIC"):
        self._loadCOSMIC()
        self._loadMapping()
        features = self.meta.getFeaturesSorted()
        processed = []
        featureCount = 0
        hitCount = 0
        hits = []
        outFile = open(os.path.join(outPath, fileStem + "-table.tex"), "wt")
        for featureName in features.keys():
            featureCount += 1
            featureType, geneId, mutationType = featureName.split(":")
            geneName = self.mapping.get(geneId, "")
            processed = [str(featureCount)] + [featureType, geneName, mutationType.replace("_", " ")] 
            hit = self.cosmic.get(geneName)
            if hit != None:
                processed += ["\\bullet"]
                hitCount += 1
                hits.append(featureCount) #hits.append(1)
            else:
                processed += [""]
                #hits.append(0)
            #processed.append(str(float(hitCount) / featureCount))
            outFile.write(" & ".join(processed) + " \\\\" + "\n")
        outFile.close()
        print "Detected", hitCount, "hits among", featureCount, "features"
        self._visualize(hits, os.path.join(outPath, fileStem + "-hist.png"))
        self._visualize(hits, os.path.join(outPath, fileStem + "-hist.pdf"))

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