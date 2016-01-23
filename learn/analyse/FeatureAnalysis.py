import os
from learn.analyse.Analysis import Analysis
from collections import OrderedDict
from learn.evaluation import majorityBaseline, aucForPredictions,\
    getMajorityPredictions
from learn.skext.metrics import balanced_accuracy_score
from sklearn.metrics.classification import accuracy_score
from learn.ExampleIO import SVMLightExampleIO
from _collections import defaultdict

class FeatureAnalysis(Analysis): 
    def __init__(self, dataPath=None):
        super(FeatureAnalysis, self).__init__(dataPath=dataPath)
        self.predictions = None
        self.grouped = None
    
    def readExamples(self, inDir, fileStem=None, exampleIO=None):
        if fileStem == None:
            fileStem = "examples"
        # Read examples
        vectors = []
        f = open(os.path.join(inDir, fileStem), "rt")
        for line in f:
            vector = {}
            cls, features = line.strip().split(maxsplits=1)
            features = features.split()
            for feature in features:
                index, value = feature.split(":")
                vector[int(index)] = float(value)
            vectors.append(vector)
        f.close()
        return vectors
        
    def analyse(self, inDir, fileStem=None, hidden=False):
        print "Reading example files"
        vectors = self.readExamples(inDir, fileStem)
        meta = self._getMeta(inDir, fileStem)
        meta.drop("project_analysis")
        print "Reading features"
        examples = [x for x in meta.db["example"]]
        assert len(examples) == len(vectors)
        counts = {}
        for example, vector in zip(examples, vectors):
            project = example["project_code"]
            if project not in counts:
                counts[project] = defaultdict(int)
            projectCounts = counts[project]
            for index in vector:
                projectCounts[index] += 1
        
        
        
        
        
        
        
        
        
        
        
        
        
        
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
                row["accuracy"] = None
                row["accuracy_baseline"] = None
                if row["pos"] > 0 and row["neg"] > 0:
                    majorityPredictions = getMajorityPredictions(labels, groups)
                    row["auc"] = aucForPredictions(labels, self.grouped[project][setName]["predictions"])
                    row["auc_baseline"] = aucForPredictions(labels, majorityPredictions)
                    row["bas"] = balanced_accuracy_score(labels, [(-1.0 if x < 0 else 1.0) for x in predictions])
                    row["bas_baseline"] = majorityBaseline(labels, [(-1.0 if x < 0 else 1.0) for x in majorityPredictions])
                    row["accuracy"] = accuracy_score(labels, [(-1.0 if x < 0 else 1.0) for x in predictions])
                    row["accuracy_baseline"] = accuracy_score(labels, [(-1.0 if x < 0 else 1.0) for x in majorityPredictions])
                rows.append(row)
        meta.insert_many("project_analysis", rows, True)