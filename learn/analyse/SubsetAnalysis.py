import sys, os
from learn.analyse.Analysis import Analysis
from collections import OrderedDict

class SubsetAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(SubsetAnalysis, self).__init__(dataPath=dataPath)
        
    def analyse(self, inDir, fileStem=None, hidden=False):
        meta = self._getMeta(inDir, fileStem)
        meta.drop("best_combinations")
        best = {}
        single = {}
        hiddenByTag = {}
        for result in meta.db["project_analysis"].all():
            project = result["project"]
            assert result["tag"] != None # Check this is for SubsetClassification
            if result["setName"] == "train":
                if project not in best or result.get("auc", -1) > best[project].get("auc", -1):
                    best[project] = result
                if result["tag"].count(",") == 0:
                    if project not in single or result.get("auc", -1) > single[project].get("auc", -1):
                        single[project] = result
            else:
                key = project + ":" + result["tag"]
                assert key not in hiddenByTag
                hiddenByTag[key] = result
        rows = []
        for project in best:
            row = OrderedDict()
            row["project"] = project
            row["auc"] = best[project]["auc"]
            row["single"] = single[project]["auc"] if project in single else None
            row["delta"] = row["auc"] - row["single"] if (row["auc"] != None and row["single"] != None) else None
            row["combination"] = best[project]["tag"]
            key = project + ":" + best[project]["tag"]
            row["auc_hidden"] = hiddenByTag.get(project + ":" + best[project]["tag"], {}).get("auc")
            row["single_hidden"] = hiddenByTag.get(project + ":" + project, {}).get("auc")
            row["delta_hidden"] = row["auc_hidden"] - row["single_hidden"] if (row["auc_hidden"] != None and row["single_hidden"] != None) else None
            rows.append(row)
        meta.insert_many("best_combinations", rows, True)