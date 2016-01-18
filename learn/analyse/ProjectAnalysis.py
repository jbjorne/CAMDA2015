import os
from learn.analyse.Analysis import Analysis
from collections import OrderedDict
from learn.evaluation import majorityBaseline, aucForPredictions

class ProjectAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(ProjectAnalysis, self).__init__(dataPath=dataPath)
        self.predictions = None
        self.grouped = None
    
    def _addToProject(self, example, project):
        if project not in self.grouped:
            self.grouped[project] = {"train":{"labels":[], "predictions":[]}, "hidden":{"labels":[], "predictions":[]}}
        self.grouped[project][example["set"]]["labels"].append(float(example["label"]))
        if self.predictions:
            self.grouped[project][example["set"]]["predictions"].append(self.predictions[example["id"]])
        
    def analyse(self, inDir, fileStem=None, hidden=False):
        meta = self._getMeta(inDir, fileStem)
        meta.drop("project_analysis")
        self.predictions = None
        if "prediction" in meta.db:
            self.predictions = {x["example"]:x["predicted"] for x in meta.db["prediction"].all()}
        #print predictions
        self.grouped = {}
        for example in meta.db.query("SELECT * FROM example"):
            self._addToProject(example, example["project_code"])
            self._addToProject(example, "all projects")
        rows = []
        for project in sorted(self.grouped.keys()):
            for setName in ("train", "hidden"):
                labels = self.grouped[project][setName]["labels"]
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
                    row["auc"] = aucForPredictions(labels, self.grouped[project][setName]["predictions"])
                rows.append(row)
        meta.insert_many("project_analysis", rows, True)