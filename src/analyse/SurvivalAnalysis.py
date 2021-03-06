from src.analyse.Analysis import Analysis
from src.evaluation import getMajorityPredictions, getMajorityClasses,\
    getMajorityPredictionsPredefined, statistics, listwisePerformance
import matplotlib.pyplot as plt
import os
from src.utils.common import getOptions
from src.analyse.threshold import optimalFThreshold, balancedThreshold

class SurvivalAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(SurvivalAnalysis, self).__init__(dataPath=dataPath)
        self.days = None
        self.examples = None
    
    def getSet(self, meta, setName):
        if self.examples == None:
            self.examples = [x for x in meta.db["example"].all()]
            numExamples = len(self.examples)
            self.examples = [x for x in self.examples if (x["donor_vital_status"] == "deceased" or x["time_survival"] > self.days or x["time_followup"] > self.days)]
            print "Right censored", numExamples - len(self.examples), "examples"
        examples = [x for x in self.examples if x["set"] == setName]
        probabilitiesDict = {x["example"]:x["predicted"] for x in meta.db["prediction"].all()}
        probabilities = [probabilitiesDict[x["id"]] for x in examples]
        return examples, probabilities
    
    def getThreshold(self, meta):
        examples, probabilities = self.getSet(meta, "train")
        labels = [x["label"] for x in examples]
        F, P, R, threshold = optimalFThreshold(probabilities, labels)
        print "optimal values: F:%f, P:%f, R:%f, threshold:%f" %(F,P,R,threshold)
        return threshold
    
    def getMajority(self, meta):
        examples, probabilities = self.getSet(meta, "train")
        labels = [x["label"] for x in examples]
        groups = [x["project_code"] for x in examples]
        return getMajorityClasses(labels, groups)
    
    def analyse(self, inDir, fileStem=None, hidden=False, useThresholding=False):
        meta = self._getMeta(inDir, fileStem)
        for filename in os.listdir(inDir):
            if filename.startswith("survival-") and filename.endswith(".pdf"):
                os.remove(os.path.join(inDir, filename))
        
        experiment = [x for x in meta.db["experiment"].all()][0]
        experimentVars = getOptions(experiment["vars"])
        self.days = 5 * 365
        if "days" in experimentVars:
            self.days = experimentVars["days"]
        self.analyseSet(inDir, meta, "train", False)
        if useThresholding:
            self.analyseSet(inDir, meta, "train", True)
        if hidden:
            self.analyseSet(inDir, meta, "hidden", False)
            if useThresholding:
                self.analyseSet(inDir, meta, "hidden", True)
    
    def analyseSet(self, inDir, meta, setName, useThresholding=False):
        print "Analysing", setName, useThresholding
        threshold = 0   
        if useThresholding:
            threshold = self.getThreshold(meta)
        
        examples, probabilities = self.getSet(meta, setName)
        predictions = [(-1 if x < threshold else 1) for x in probabilities]
        labels = [x["label"] for x in examples]
        groups = [x["project_code"] for x in examples]
        
        majorityClasses = self.getMajority(meta)
        majorityPredictions = getMajorityPredictionsPredefined(groups, majorityClasses)
        
        datasets = {"label":{1:[], -1:[]}, "majority":{1:[], -1:[]}, "classified":{1:[], -1:[]}}
        for results, category in zip((labels, majorityPredictions, predictions), ("label", "majority", "classified")):
            assert len(results) == len(examples)
            for result, example in zip(results, examples):
                cls = 1 if result > 0 else -1
                datasets[category][cls].append(example)
            print category, (len(datasets[category][1]), len(datasets[category][-1])), statistics(labels, results)
            print listwisePerformance(labels, results)
            
        self._visualize(datasets, self.days, self._getOutFileName(inDir, setName, useThresholding))
    
    def _getOutFileName(self, inDir, setName, useThresholding):
        filename = "survival-" + setName
        if useThresholding:
            filename += "-threshold"
        filename += ".pdf"
        return os.path.join(inDir, filename)
    
    def _drawCurve(self, donors, cutoff, label, color, style):
        numDonors = float(len(donors))
        x = range(0, cutoff)
        y = []
        for point in x:
            alive = 0
            for donor in donors:
                if donor["time_survival"] == 0 or donor["time_survival"] > point:
                    alive += 1
            y.append(alive / numDonors)
        plt.step(x, y, where='post', label=label, color=color, linestyle=style) 
    
    def _visualize(self, datasets, cutoff, outPath):
        colors = {1:"blue", -1:"red"}
        styles = {"classified":"-", "label":":", "majority":"--"}
        for category in datasets:
            for cls in (1, -1):
                donors = datasets[category][cls]
                if len(donors) < 1:
                    continue
                self._drawCurve(donors, cutoff, category[0] + ("+" if cls > 0 else "-") + " (" + str(len(donors)) + ")", colors[cls], styles[category])
        allDonors = datasets["label"][1] + datasets["label"][-1]
        self._drawCurve(allDonors, cutoff, "all (" + str(len(allDonors)) + ")", "magenta", ":")
        axes = plt.gca()
        axes.set_xlim([0, cutoff])
        axes.set_ylim([0, 1.01])
        plt.ylabel("Live donors")
        plt.xlabel("Days")
        plt.legend(loc='lower left')
        if outPath != None:
            plt.savefig(outPath)
        plt.close()