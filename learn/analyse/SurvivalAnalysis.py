from learn.analyse.Analysis import Analysis
from learn.evaluation import getMajorityPredictions
import matplotlib.pyplot as plt
import os
from utils.common import getOptions
from learn.analyse.threshold import optimalFThreshold

class SurvivalAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(SurvivalAnalysis, self).__init__(dataPath=dataPath)
    
    def getSet(self, meta, setName):
        examples = [x for x in meta.db["example"].all() if x["set"] == setName]
        probabilitiesDict = {x["example"]:x["predicted"] for x in meta.db["prediction"].all()}
        probabilities = [probabilitiesDict[x["id"]] for x in examples]
        return examples, probabilities
    
    def getThreshold(self, meta):
        examples, probabilities = self.getSet(meta, "train")
        labels = [x["label"] for x in examples]
        F, P, R, threshold = optimalFThreshold(probabilities, labels)
        print "optimal values: F:%f, P:%f, R:%f, threshold:%f" %(F,P,R,threshold)
        return threshold
    
    def analyse(self, inDir, fileStem=None, hidden=False):
        meta = self._getMeta(inDir, fileStem)
        for filename in os.listdir(inDir):
            if filename.startswith("survival-") and filename.endswith(".pdf"):
                os.remove(os.path.join(inDir, filename))
        
        experiment = [x for x in meta.db["experiment"].all()][0]
        experimentVars = getOptions(experiment["vars"])
        assert "days" in experimentVars
        days = experimentVars["days"]
        self.analyseSet(inDir, meta, "train", days, False)
        self.analyseSet(inDir, meta, "train", days, True)
        if hidden:
            self.analyseSet(inDir, meta, "hidden", days, False)
            self.analyseSet(inDir, meta, "hidden", days, True)
    
    def analyseSet(self, inDir, meta, setName, days, useThresholding=False):
        print "Analysing", setName, useThresholding
        threshold = 0   
        if useThresholding:
            threshold = self.getThreshold(meta)
        
        targetSet = "hidden" if setName else "train"
        examples, probabilities = self.getSet(meta, targetSet)
        predictions = [(-1 if x < threshold else 1) for x in probabilities]
        labels = [x["label"] for x in examples]
        groups = [x["project_code"] for x in examples]
        majorityPredictions = getMajorityPredictions(labels, groups)
        
        datasets = {"label":{1:[], -1:[]}, "majority":{1:[], -1:[]}, "classified":{1:[], -1:[]}}
        for results, category in zip((labels, majorityPredictions, predictions), ("label", "majority", "classified")):
            assert len(results) == len(examples)
            for result, example in zip(results, examples):
                cls = 1 if result > 0 else -1
                datasets[category][cls].append(example)
            print category, len(datasets[category][1]), len(datasets[category][-1])

        self._visualize(datasets, days, self._getOutFileName(inDir, setName, useThresholding))
    
    def _getOutFileName(self, inDir, setName, useThresholding):
        filename = "survival-" + setName
        if useThresholding:
            filename += "-threshold"
        filename += ".pdf"
        return os.path.join(inDir, filename)
    
    def _visualize(self, datasets, cutoff, outPath):
        colors = {1:"blue", -1:"red"}
        styles = {"classified":"-", "label":":", "majority":"--"}
        for category in datasets:
            for cls in (1, -1):
                donors = datasets[category][cls]
                if len(donors) < 1:
                    continue
                numDonors = float(len(donors))
                #maxTime = max([x["time_survival"] for x in donors])
                x = [0] + sorted([x["time_survival"] for x in donors if x["time_survival"] > 0])
                y = []
                for point in x:
                    alive = 0
                    for donor in donors:
                        if donor["time_survival"] == 0 or donor["time_survival"] > point:
                            alive += 1
                    y.append(alive / numDonors)
                #print category, cls, x, y
                plt.step(x, y, where='post', label=category[0] + ":" + str(cls), color=colors[cls], linestyle=styles[category])
        axes = plt.gca()
        axes.set_xlim([0, cutoff])
        axes.set_ylim([0, 1.01])
        plt.ylabel("Live donors")
        plt.xlabel("Days")
        plt.legend()
        if outPath != None:
            plt.savefig(outPath)
        plt.close()