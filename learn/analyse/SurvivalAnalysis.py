from learn.analyse.Analysis import Analysis
from learn.evaluation import getMajorityPredictions

class SurvivalAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(SurvivalAnalysis, self).__init__(dataPath=dataPath)
    
    def analyse(self, inDir, fileStem=None, hidden=False):
        meta = self._getMeta(inDir, fileStem)
        #meta.drop("survival")
        examples = [x for x in meta.db["example"].all()]
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
        