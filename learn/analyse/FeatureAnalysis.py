import os
from learn.analyse.Analysis import Analysis
from collections import defaultdict
import matplotlib.pyplot as plt

class FeatureAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(FeatureAnalysis, self).__init__(dataPath=dataPath)
        self.predictions = None
        self.grouped = None
    
    def readExamples(self, inDir, fileStem=None, exampleIO=None):
        if fileStem == None:
            fileStem = "examples.yX"
        # Read examples
        vectors = []
        f = open(os.path.join(inDir, fileStem), "rt")
        for line in f:
            vector = {}
            cls, features = line.strip().split(" ", 1)
            features = features.split()
            for feature in features:
                index, value = feature.split(":")
                vector[int(index)] = float(value)
            vectors.append(vector)
        f.close()
        return vectors
        
    def analyse(self, inDir, fileStem=None, hidden=False):
        print "Reading example files"
        vectors = self.readExamples(inDir, fileStem)
        meta = self._getMeta(inDir, fileStem)
        meta.drop("feature_distribution")
        print "Reading features"
        examples = [x for x in meta.db["example"]]
        assert len(examples) == len(vectors)
        counts = defaultdict(lambda: defaultdict(int))
        TOTAL = object()
        print "Processing examples"
        for example, vector in zip(examples, vectors):
            project = example["project_code"]
            if example["set"] == "hidden" and not hidden: # skip hidden set examples
                continue
            for index in vector:
                counts[index][project] += 1
                counts[index][TOTAL] += 1
        print "Sorting features"
        x = range(len(counts))
        y = sorted([counts[i][TOTAL] for i in counts], reverse=True)
        self._visualize(x, y, os.path.join(inDir, "features.pdf"))
        print "Saving features"
        rows = [{"id":i, "total":counts[i][TOTAL]} for i in sorted(counts.keys())]
        meta.insert_many("feature_distribution", rows, True)
        
    def _visualize(self, x, y, outPath):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.hist(y, 100, log=True)
#        ax.plot(x, y)
        #fig.subplots_adjust(left=0.5, bottom=0.2)
#         ylim = ax.get_ylim()
#         ax.set_ylim((ylim[0] - 0.01 * (ylim[1] - ylim[0]), ylim[1]))
#         xlim = ax.get_xlim()
#         ax.set_xlim((xlim[0] - 0.01 * (xlim[1] - xlim[0]), xlim[1]))
#        ax.set_yscale('log')
        plt.grid()
        if outPath != None:
            fig.savefig(outPath)
        
        
        
#         fig = plt.plot(x, y)#, facecolor='green', alpha=0.5, normed=1)
#         plt.xlabel('Feature')
#         plt.ylabel('Occurrences')
#         plt.title(r'Test')
#         fig.subplots_adjust(bottom=0.2)
#         #plt.yscale('log')
#         #plt.show()
        if outPath != None:
            plt.savefig(outPath)