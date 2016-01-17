import os
from learn.analyse.Analysis import Analysis
from collections import OrderedDict
from learn.evaluation import majorityBaseline, aucForPredictions

class ProjectAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(ProjectAnalysis, self).__init__(dataPath=dataPath)
        
    def analyse(self, inDir, fileStem=None, hidden=False):
        meta = self._getMeta(inDir, fileStem)
        meta.drop("project_analysis")
        predictions = None
        if "prediction" in meta.db:
            predictions = {x["example"]:x["predicted"] for x in meta.db["prediction"].all()}
        #print predictions
        grouped = {}
        for example in meta.db.query("SELECT * FROM example"):
            project = example["project_code"]
            if project not in grouped:
                grouped[project] = {"train":{"labels":[], "predictions":[]}, "hidden":{"labels":[], "predictions":[]}}
            grouped[project][example["set"]]["labels"].append(float(example["label"]))
            if predictions:
                grouped[project][example["set"]]["predictions"].append(predictions[example["id"]])
        rows = []
        for project in sorted(grouped.keys()):
            for setName in ("train", "hidden"):
                labels = grouped[project][setName]["labels"]
                row = OrderedDict([("project",project), ("setName", setName)])
                row["examples"] = len(labels)
                row["pos"] = len([x for x in labels if x > 0])
                row["neg"] = len([x for x in labels if x < 0])
                row["majority"] = None
                if row["pos"] > 0 or row["neg"] > 0:
                    row["majority"] = max(set(labels), key=labels.count)
                row["baseline"] = None
                row["auc"] = None
                if row["pos"] > 0 and row["neg"] > 0:
                    row["baseline"] = majorityBaseline(labels)
                    row["auc"] = aucForPredictions(labels, grouped[project][setName]["predictions"])
                rows.append(row)
        meta.insert_many("project_analysis", rows, True)