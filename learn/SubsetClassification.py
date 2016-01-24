import sys, os
from learn.analyse.ProjectAnalysis import ProjectAnalysis
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Classification import Classification
import traceback

class SubsetClassification(Classification):
    def __init__(self, classifierName, classifierArgs, numFolds=10, parallel=1, metric='roc_auc', getCV=None, preDispatch='2*n_jobs', classifyHidden=False):
        super(SubsetClassification, self).__init__(classifierName, classifierArgs, numFolds, parallel, metric, getCV, preDispatch, classifyHidden)
        self.analysis = None
        self.resultCutoff = 0.6
    
    def _getTag(self, projects):
        return ",".join(sorted(projects))
    
    def classifyProjects(self, projects):
        print "----------------------", "Classifying projects", projects, "----------------------"
        self.meta.dropTables(["result", "prediction", "importance"], 100000)
        setNames = []
        for example in self.meta.db["example"].all():
            if example["project_code"] in projects:
                setNames.append(example["set"])
            else:
                setNames.append(None)
        try:
            self.indices, X_train, X_hidden, y_train, y_hidden = self._splitData(setNames=setNames)
            search = self._crossValidate(y_train, X_train, self.classifyHidden and (X_hidden.shape[0] > 0))
            if self.classifyHidden:
                self._predictHidden(y_hidden, X_hidden, search, y_train.shape[0])
            print "Analysing project performance"
            self.analysis.analyse(self.inDir, None, X_hidden.shape[0] > 0, tag=self._getTag(projects), clear=False, projects=projects)
        except ValueError, err:
            print(traceback.format_exc())
    
    def readExamples(self, inDir, fileStem=None, exampleIO=None, preserveTables=None):
        super(SubsetClassification, self).readExamples(inDir=inDir, fileStem=fileStem, exampleIO=exampleIO, preserveTables=preserveTables)
        self.analysis = ProjectAnalysis(inDir)
        self.inDir = inDir
        
    def classify(self):
        examples = self.meta.db["example"].all()
        projects = sorted(set([x["project_code"] for x in examples]))
        self.classifyGrow([], projects)
    
    def getCombinationResults(self, projects):
        if self.meta.exists("project_analysis"):
            rows = self.meta.db.query("SELECT * FROM project_analysis WHERE setName=='train' AND project is not 'all projects' AND tag='{TAG}'".replace("{TAG}", self._getTag(projects)))
            results = {row["project"]:row["auc"] for row in rows}
        else:
            print "WARNING, table project_analysis does not exist" 
            results = {}
        return results
        
    def classifyGrow(self, combination, allProjects, prevResults=None, seenTags=None):
        if prevResults == None:
            prevResults = {}
        if seenTags == None:
            seenTags = set()
        for project in allProjects:
            if project in combination:
                continue
            extended = combination + [project]
            if len(extended) == 1:
                print "================", "Processing project", project, "(" + str(allProjects.index(project) + 1) + "/" + str(len(allProjects)) + ")", "================"
            tag = self._getTag(extended)
            if tag not in seenTags:
                self.classifyProjects(extended)
                seenTags.add(tag)
            else:
                print "Skipping seen combination", tag
            results = self.getCombinationResults(extended)
            allAreNone = True
            lowerPerformance = None
            belowCutoff = None
            for key in results:
                if key == "all projects":
                    continue
                if results[key] != None:
                    allAreNone = False
                    if results[key] < prevResults.get(key, -1):
                        lowerPerformance = key
                        break
                    if results[key] < self.resultCutoff:
                        belowCutoff = key
                        break
            # Report the status
            statusString = tag, results, "/", prevResults
            if allAreNone:
                print "No results for any projects in combination", statusString
            elif belowCutoff:
                print "Project", belowCutoff, "is below the cutoff", self.resultCutoff, "in combination", statusString
            elif lowerPerformance:
                print "Lower performance for project", lowerPerformance, "in combination", statusString
            else:
                print "Better performance for all projects in combination", statusString
            # Continue if needed
            if not (allAreNone or lowerPerformance != None or belowCutoff != None):
                self.classifyGrow(extended, allProjects, results, seenTags)