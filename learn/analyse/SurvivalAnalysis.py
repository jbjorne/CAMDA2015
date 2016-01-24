from learn.analyse.Analysis import Analysis
from learn.evaluation import getMajorityPredictions
import matplotlib.pyplot as plt
import os
from utils.common import getOptions

class SurvivalAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(SurvivalAnalysis, self).__init__(dataPath=dataPath)
    
    def analyse(self, inDir, fileStem=None, hidden=False):
        meta = self._getMeta(inDir, fileStem)
        
        experiment = [x for x in meta.db["experiment"].all()][0]
        experimentVars = getOptions(experiment["vars"])
        assert "days" in experimentVars
        days = experimentVars["days"]
        
        #meta.drop("survival")
        targetSet = "hidden" if hidden else "train"
        examples = [x for x in meta.db["example"].all() if x["set"] == targetSet]
        probabilities = {x["example"]:x["predicted"] for x in meta.db["prediction"].all()}
        predictions = [(-1 if probabilities[x["id"]] < 0 else 1) for x in examples]
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
        
        self._visualize(datasets, days, os.path.join(inDir, "survival.pdf"))
    
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