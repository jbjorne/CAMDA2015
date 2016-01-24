import sys, os
from learn.analyse.Analysis import Analysis
from collections import OrderedDict

class SubsetAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(SubsetAnalysis, self).__init__(dataPath=dataPath)
    
    def getHiddenByTag(self, meta):
        hiddenByTag = {}
        for result in meta.db["project_analysis"].all():
            project = result["project"]
            assert result["tag"] != None # Check this is for SubsetClassification
            if result["setName"] == "hidden" and result["tag"] != "all projects":
                key = project + ":" + result["tag"]
                assert key not in hiddenByTag
                hiddenByTag[key] = result
        return hiddenByTag
    
    def getRatio(self, result):
        if result:
            pos = result.get("pos", 0)
            neg = result.get("neg", 0)
            return str(pos) + ":" + str(neg)
        return None
        
    def analyse(self, inDir, fileStem=None, hidden=False):
        meta = self._getMeta(inDir, fileStem)
        meta.drop("best_combinations")
        results = [x for x in meta.db["project_analysis"].all()]
        baselines = {}
        for result in results:
            if result["setName"] == "train" and result["tag"].count(",") == 0 and result["project"] != "all projects":
                assert result["project"] not in baselines, (result, baselines)
                baselines[result["project"]] = result
        resultsByTag = {}
        currentTag = None
        for result in results:
            assert result["tag"] != None # Check this is for SubsetClassification
            tag = result["tag"]
            if result["setName"] == "train" and result["project"] != "all projects":
                if tag != currentTag:
                    resultsByTag[tag] = {}
                    currentTag = tag
                if result["project"] not in resultsByTag[tag]:
                    resultsByTag[tag][result["project"]] = result
        kept = []
        print "Baselines", [{"p":x["project"], "a":x["auc"]} for x in baselines.values()]
        for tag in sorted(resultsByTag.keys()):
            keep = True
            for project in resultsByTag[tag]:
                if resultsByTag[tag][project].get("auc", -1) <= baselines.get(project, {}).get("auc", -1):
                    keep = False
                    break
            if keep:
                kept.extend(resultsByTag[tag].values())
            print tag, keep, [{"p":x["project"], "a":x["auc"]} for x in resultsByTag[tag].values()]
        
        hiddenByTag = self.getHiddenByTag(meta)
        rows = []
        for result in kept:
            row = OrderedDict()
            project = result["project"]
            row["project"] = project
            row["auc"] = result["auc"]
            row["single"] = baselines[project]["auc"]
            row["delta"] = row["auc"] - row["single"] if (row["auc"] != None and row["single"] != None) else None
            row["ratio"] = self.getRatio(result)
            row["combination"] = result["tag"]
            row["auc_hidden"] = hiddenByTag.get(project + ":" + result["tag"], {}).get("auc")
            row["single_hidden"] = hiddenByTag.get(project + ":" + project, {}).get("auc")
            row["delta_hidden"] = row["auc_hidden"] - row["single_hidden"] if (row["auc_hidden"] != None and row["single_hidden"] != None) else None
            row["ratio_hidden"] = self.getRatio(hiddenByTag.get(project + ":" + result["tag"]))
            rows.append(row)
        meta.insert_many("best_combinations", rows, True)

#         best = {}
#         single = {}
#         hiddenByTag = {}
#         for result in meta.db["project_analysis"].all():
#             project = result["project"]
#             assert result["tag"] != None # Check this is for SubsetClassification
#             if result["setName"] == "train":
#                 if project not in best or result.get("auc", -1) > best[project].get("auc", -1):
#                     best[project] = result
#                 if result["tag"].count(",") == 0:
#                     if project not in single or result.get("auc", -1) > single[project].get("auc", -1):
#                         single[project] = result
#             else:
#                 key = project + ":" + result["tag"]
#                 assert key not in hiddenByTag
#                 hiddenByTag[key] = result
#         rows = []
#         for project in best:
#             row = OrderedDict()
#             row["project"] = project
#             row["auc"] = best[project]["auc"]
#             row["single"] = single[project]["auc"] if project in single else None
#             row["delta"] = row["auc"] - row["single"] if (row["auc"] != None and row["single"] != None) else None
#             row["combination"] = best[project]["tag"]
#             key = project + ":" + best[project]["tag"]
#             row["auc_hidden"] = hiddenByTag.get(project + ":" + best[project]["tag"], {}).get("auc")
#             row["single_hidden"] = hiddenByTag.get(project + ":" + project, {}).get("auc")
#             row["delta_hidden"] = row["auc_hidden"] - row["single_hidden"] if (row["auc_hidden"] != None and row["single_hidden"] != None) else None
#             rows.append(row)
#        meta.insert_many("best_combinations", rows, True)