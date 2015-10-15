import itertools
from numbers import Number
import math
import hidden
import sqlite3

def connect(con):
    if isinstance(con, basestring):
        con = sqlite3.connect(con) # @UndefinedVariable
        con.row_factory = sqlite3.Row # @UndefinedVariable
        con.create_function("log", 1, math.log)
    return con

class Project:
    def getExampleFields(self):
        return "icgc_donor_id,icgc_specimen_id,project_code,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup"
    
    def getExampleTable(self):
        return "clinical"
    
    def getExampleConditions(self):
        return """
        length(specimen_type) > 0 AND 
        length(disease_status_last_followup) > 0 AND
        ((disease_status_last_followup LIKE '%remission%') OR
        (donor_vital_status IS 'deceased')) AND
        specimen_type NOT LIKE '%Normal%'
        """
    
    def getExamples(self):
        query = "SELECT " + self.getExampleFields() + "\n"
        query += "FROM " + self.getExampleTable() + "\n"
        query += "WHERE "
        if self.projects != None:
            query += " project_code IN " + self.projects + " AND" + "\n"
        query += self.getExampleConditions()
        return [x for x in self.getConnection().execute(query)]
    
    def getLabel(self, example):
        return 'remission' in example['disease_status_last_followup']
    
    def getConnection(self):
        if self._connection == None:
            self._connection = sqlite3.connect(con) # @UndefinedVariable
            self._connection.row_factory = sqlite3.Row # @UndefinedVariable
            self._connection.create_function("log", 1, math.log)
        return self._connection
    
    def __init__(self):
        # Database
        self.databaseName = None
        self._connection = None
        # Id sets
        self._featureIds = {}
        # General
        self.name = None
        self.projects = None
        self.classes = {'True':1, 'False':-1},
        self.featureGroups = [SSM_GENE_CONSEQUENCE],
        self.filter = SSM_FILTER
        self.hiddenCutoff = 0.3
        self.meta = META
        self.includeHiddenSet = True
        self.includeTrainingSet = True
    
    def generateOrNot(self, example, verbose=True):
        if not self.includeHiddenSet and example["hidden"] < self.hiddenCutoff:
            if verbose:
                print "Skipping example from hidden donor", example["icgc_donor_id"]
            return False
        elif not self.includeTrainingSet and example["hidden"] >= self.hiddenCutoff:
            if verbose:
                print "Skipping example " + str(example) + " from non-hidden donor", example["icgc_donor_id"]
            return False
        else:
            return True
    
    def getFeatureId(self, featureName):
        if featureName not in self._featureIds:
            self._featureIds[featureName] = len(self._featureIds)
        return self._featureIds[featureName]
        
    def _buildFeatures(self, example):
        features = {}
        for featureGroup in self.featureGroups:
            groupIndex = self.featureGroups.index(featureGroup)
            for row in featureGroup(con=self.getConnection(), example=example):
                for key, value in itertools.izip(*[iter(row)] * 2): # iterate over each consecutive key,value columns pair
                    if not isinstance(key, basestring):
                        raise Exception("Non-string feature key '" + str(key) + "' in feature group " + str(groupIndex))
                    if not isinstance(value, Number):
                        raise Exception("Non-number feature value '" + str(value) + "' in feature group " + str(groupIndex))
                    features[self.getFeatureId(key)] = value
        if len(features) == 0:
            print "WARNING: example has no features"
        return features
    
    def process(self, experimentName, callback, callbackArgs, metaDataFileName=None, options=None, experimentMeta=None):
        print "Template:", self.name
        examples = self.getExamples()
        numHidden = hidden.setHiddenValuesByFraction(examples, self.hidden)
        numExamples = len(examples)
        print "Examples " +  str(numExamples) + ", hidden " + str(numHidden)
        count = 0
        clsIds = compiled.get("classes", None)
        hiddenRule = compiled.get("include", "train")
        featureIds = {}
        meta = []
        featureGroups = compiled.get("features", [])
        sampleRandom = MTwister()
        sampleRandom.set_seed(2)
        for example in examples:
            count += 1
            if not self.generateOrNot(example):
                continue
            hidden.setSet(example, compiled.get("hidden", None))
            example["set"] = "hidden" if example["hidden"] < self.hiddenCutoff else "train"

            print "Processing example", example,
            cls = getIdOrValue(compiled["label"](con=con, example=example, **lambdaArgs), clsIds)
            print cls, str(count) + "/" + str(numExamples)
            strCls = str(cls)
            if "sample" in compiled and strCls in compiled["sample"] and sampleRandom.random() > compiled["sample"][strCls]:
                print "NOTE: Downsampled example"
                continue
            if "filter" in compiled and compiled["filter"] != None and len([x for x in compiled["filter"](con=con, example=example, **lambdaArgs)]) == 0:
                print "NOTE: Filtered example"
                continue
            
            features = self._buildFeatures(example)

            if "meta" in compiled:
                meta.append(compiled["meta"](label=cls, features=features, example=example, **lambdaArgs))
        
        saveMetaData(metaDataFileName, con, template, experimentName, options, clsIds, featureIds, meta, experimentMeta)
        return featureIds