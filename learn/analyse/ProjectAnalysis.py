import os
from learn.analyse.Analysis import Analysis
from collections import OrderedDict
from learn.evaluation import majorityBaseline

class ProjectAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(ProjectAnalysis, self).__init__(dataPath=dataPath)
        
    def analyse(self, inDir, fileStem=None, hidden=False):
        meta = self._getMeta(inDir, fileStem)
        meta.drop("project_analysis")
        grouped = []
        for example in self.meta.db.query("SELECT * FROM example"):
            project = example["project_code"]
            if project not in grouped:
                grouped[project] = {"train":[], "hidden":[]}
            grouped[project][example["set"]].append(example["label"])
        rows = []
        for project in sorted(grouped.keys()):
            for setName in ("train", "hidden"):
                labels = grouped[project][setName]
                row = OrderedDict([("project",project), ("setName", setName)])
                row["examples"] = len(labels)
                row["pos"] = len([x for x in labels if x > 0])
                row["neg"] = len([x for x in labels if x < 0])
                row["majority"] = max(set(labels), key=labels.count)
                row["baseline"] = majorityBaseline(labels)
                rows.append(row)
        meta.insert_many("project_analysis", rows, True)