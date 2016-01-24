from learn.analyse.Analysis import Analysis
from learn.evaluation import getMajorityPredictions
import matplotlib.pyplot as plt

class SurvivalAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(SurvivalAnalysis, self).__init__(dataPath=dataPath)
    
    def analyse(self, inDir, fileStem=None, hidden=False):
        meta = self._getMeta(inDir, fileStem)
        #meta.drop("survival")
        targetSet = "hidden" if hidden else "train"
        examples = [x for x in meta.db["example"].all() if x["setName"] == targetSet]
        probabilities = {x["example"]:x["predicted"] for x in meta.db["prediction"].all()}
        predictions = [(-1 if x < 0 else 1) for x in probabilities]
        labels = [x["label"] for x in examples]
        groups = [x["project_code"] for x in examples]
        majorityPredictions = getMajorityPredictions(labels, groups)
        
        datasets = {"label":{1:[], -1:[]}, "majority":{1:[], -1:[]}, "classified":{1:[], -1:[]}}
        for results, category in zip((labels, majorityPredictions, predictions), ("label", "majority", "classified")):
            assert len(results) == len(examples)
            for result, example in zip(results, examples):
                cls = 1 if result > 0 else -1
                datasets[category][cls].append(example)
    
    def _visualize(self, datasets, outPath):
        for category in datasets:
            for cls in (1, -1):
                donors = datasets[category][cls]
                if len(donors) < 1:
                    continue
                #maxTime = max([x["time_survival"] for x in donors])
                x = [0] + sorted([x["time_survival"] for x in donors if x["time_survival"] != None])
                y = []
                for point in x:
                    alive = 0
                    for donor in donors:
                        if donor["time_survival"] == None or donor["time_survival"] > point:
                            alive += 1
                    y.append(alive)
                plt.step(x, y, label=category + ":" + str(cls))
        plt.ylabel("Live donors")
        plt.xlabel("Days")
        if outPath != None:
            plt.savefig(outPath)