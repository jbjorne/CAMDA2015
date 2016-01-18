import os
from learn.analyse.Analysis import Analysis
from collections import OrderedDict
from learn.evaluation import majorityBaseline, aucForPredictions,\
    getMajorityPredictions
from learn.skext.metrics import balanced_accuracy_score

class ProjectAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(ProjectAnalysis, self).__init__(dataPath=dataPath)
        self.predictions = None
        self.grouped = None
    
    def _addToProject(self, example, project):
        if project not in self.grouped:
            self.grouped[project] = {"train":{"labels":[], "predictions":[], "groups":[]}, 
                                     "hidden":{"labels":[], "predictions":[], "groups":[]}}
        projectGroup = self.grouped[project][example["set"]]
        projectGroup["labels"].append(float(example["label"]))
        projectGroup["groups"].append(example["project_code"])
        if self.predictions:
            projectGroup["predictions"].append(self.predictions[example["id"]])
        
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
                groups = self.grouped[project][setName]["groups"]
                predictions = self.grouped[project][setName]["predictions"]
                row = OrderedDict([("project",project), ("setName", setName)])
                row["examples"] = len(labels)
                row["pos"] = len([x for x in labels if x > 0])
                row["neg"] = len([x for x in labels if x < 0])
                row["majority"] = None
                if row["pos"] > 0 or row["neg"] > 0:
                    row["majority"] = max(set(labels), key=labels.count)
                row["auc_baseline"] = None
                row["auc"] = None
                row["bas_baseline"] = None
                row["bas"] = None
                if row["pos"] > 0 and row["neg"] > 0:
                    majorityPredictions = getMajorityPredictions(labels, groups)
                    row["auc_baseline"] = aucForPredictions(labels, majorityPredictions)
                    row["bas_baseline"] = majorityBaseline(labels, [(-1.0 if x < 0 else 1.0) for x in majorityPredictions])
                    row["auc"] = aucForPredictions(labels, self.grouped[project][setName]["predictions"])
                    row["bas"] = balanced_accuracy_score(labels, [(-1.0 if x < 0 else 1.0) for x in predictions])
                rows.append(row)
        meta.insert_many("project_analysis", rows, True)