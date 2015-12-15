import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
import math
import time
#import json
#import inspect
#from collections import OrderedDict
import data.hidden as hidden
from Meta import DatabaseConnection
#from ExampleIO import SVMLightExampleIO

class Experiment(object):
    def _queryExamples(self):
        if self.query:
            query = self.query
        else:
            query = "SELECT " + self.exampleFields + "\n"
            query += "FROM " + self.exampleTable + "\n"
            query += "WHERE "
            if self.projects != None:
                query += "      project_code IN ('" + "','".join(self.projects) + "') AND"
            query += self.exampleWhere
        self.query = query
        print "=========================== Example generation query ==========================="
        print query
        print "================================================================================"
        return [dict(x) for x in self.getConnection().execute(query)]
    
    def getLabel(self, example):
        raise NotImplementedError
    
    def getConnection(self):
        if self._connection == None:
            if not os.path.exists(self.databasePath):
                raise Exception("No database at " + str(self.databasePath))
            print "Using database at", self.databasePath
            self._connection = sqlite3.connect(self.databasePath) # @UndefinedVariable
            self._connection.row_factory = sqlite3.Row # @UndefinedVariable
            self._connection.create_function("log", 1, math.log)
        return self._connection
    
    def __init__(self):
        # Processing
        self.debug = False
        # Database
        self.databasePath = None
        self._connection = None
        # Id sets
        self.featureIds = {}
        self.classIds = {'True':1, 'False':-1}
        # General
        self.projects = None
        
        self.query = None
        self.exampleTable = "clinical"
        self.exampleFields = "icgc_donor_id,icgc_specimen_id,project_code,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup"
        self.exampleWhere = None
        self.featureGroups = None
        #self.filter = None
        self.hiddenCutoff = 0.3
        self.includeHiddenSet = True
        self.includeTrainingSet = True
        # Generated data
        self.examples = None
        self.db = None
        self.unique = None
    
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
    
    def getClassId(self, value):
        if self.classIds != None:
            value = str(value)
            if value not in self.classIds:
                self.classIds[value] = len(self.classIds)
            return self.classIds[value]
        else:
            return value
    
#     def getFeatureId(self, featureName):
#         if featureName not in self.featureIds:
#             self.featureIds[featureName] = len(self.featureIds)
#             self.meta.insert("feature", {"name":featureName, "id":self.featureIds[featureName]})
#         return self.featureIds[featureName]
        
    def _buildFeatures(self, example):
        features = {}
        connection = self.getConnection()
        for featureGroup in self.featureGroups:
            featureGroup.processExample(connection, example, features, self.featureIds, self.db)
#         for groupIndex in range(len(self.featureGroups)):
#             featureGroup = self.featureGroups[groupIndex]
#             for row in self._queryFeatures(featureGroup, example): #featureGroup(con=self.getConnection(), example=example):
#                 for key, value in itertools.izip(*[iter(row)] * 2): # iterate over each consecutive key,value columns pair
#                     if not isinstance(key, basestring):
#                         raise Exception("Non-string feature key '" + str(key) + "' in feature group " + str(groupIndex))
#                     if not isinstance(value, Number):
#                         raise Exception("Non-number feature value '" + str(value) + "' in feature group " + str(groupIndex))
#                     features[self.getFeatureId(key)] = value
        #if len(features) == 0:
        #    print "WARNING: example has no features"
        return features
    
#     def _queryFeatures(self, featureGroup, example):
#         return self.getConnection().execute(featureGroup, (example['icgc_specimen_id'], ) )
    
#     def _filterExample(self, example):
#         if self.filter != None:
#             return len([x for x in self.getConnection().execute(self.filter, (example['icgc_specimen_id'], ) )]) == 0
#         return False

    def filter(self, example, features):
        if len(features) == 0:
            print "Filtered example with 0 features"
            return True
        return False
    
#     def getExampleMeta(self, example, classId, features):
#         return dict(example, label=str(classId), features=len(features))
    
    def buildExamples(self, metaDataFileName=None): #, exampleWriter=None):
        print "Experiment:", self.__class__.__name__
        self.db = DatabaseConnection(metaDataFileName, clear=True)
        self.db.insert("experiment", {"name":self.__class__.__name__, "query":self.query, "time":time.strftime("%c"), "dbFile":self.databasePath, "dbModified":time.strftime("%c", time.localtime(os.path.getmtime(self.databasePath)))})
        for classId in self.classIds:
            self.db.insert("class", {"label":classId, "value":self.classIds[classId]})
        self.db.initCache("feature_vectors", 100000)
        self.db.db.query("CREATE TABLE feature_vectors (example INTEGER NOT NULL, feature_id INTEGER NOT NULL, feature_value REAL NOT NULL, PRIMARY KEY (example, feature_id));")
        self.db.initCache("feature", 10000)
        self.db.flush()
        self.examples = self._queryExamples()
        numHidden = hidden.setHiddenValuesByFraction(self.examples, self.hiddenCutoff)
        numExamples = len(self.examples)
        uniqueValues = set()
        print "Examples " +  str(numExamples) + ", hidden " + str(numHidden)
        count = 0
        built = 0
        for example in self.examples:
            count += 1
            if not self.generateOrNot(example):
                continue
            example["set"] = "hidden" if example["hidden"] < self.hiddenCutoff else "train"

            print "Processing example", example,
            example["label"] = self.getClassId(self.getLabel(example))
            #if self._filterExample(example):
            #    print "NOTE: Filtered example"
            #    continue
            if self.unique:
                assert example[self.unique] not in uniqueValues
                uniqueValues.add(example[self.unique])
            
            features = self._buildFeatures(example)
            print example["label"], str(len(features)), str(count) + "/" + str(numExamples)
            if self.filter(example, features):
                continue
            example["id"] = built
            #self.exampleMeta.append(self.getExampleMeta(example, classId, features))
            example["features"] = len(features)
            self.db.insert("example", example)
            self._saveFeatures(features, example["id"])
            #exampleWriter.writeExample(classId, features)
            built += 1
        
        self.db.flush()
        print "Built", built, "examples with", len(self.featureIds), "unique features"
        #self.saveMetaData(metaDataFileName)
    
    def _saveFeatures(self, features, exampleId):
        rows = []
        for key in features:
            rows.append({"example":exampleId, "feature_id":key, "feature_value":features[key]})
        self.db.insert_many("feature_vectors", rows)
    
#     def _writeExamples(self, classIds, featureVectors, exampleWriter):
#         if exampleWriter != None:
#             for classId, features in zip(classIds, featureVectors):
#                 exampleWriter.writeExample(classId, features)
    
#     def getFingerprint(self):
#         return inspect.getsource(self.__class__)
    
#     def saveMetaData(self, metaDataFileName):
#         if metaDataFileName != None:
#             print "Writing metadata to", metaDataFileName
#             if not os.path.exists(os.path.dirname(metaDataFileName)):
#                 os.makedirs(os.path.dirname(metaDataFileName))
#             f = open(metaDataFileName, "wt")
#             output = OrderedDict((("experiment", self.meta), ("source", inspect.getsource(self.__class__)), ("classes", self.classIds), ("features", self.featureIds)))
#             if len(self.exampleMeta) > 0:
#                 output["examples"] = self.exampleMeta
#             json.dump(output, f, indent=4)#, separators=(',\n', ':'))
#             f.close()
#         else:
#             print "Experiment metadata not saved"
    
    def writeExamples(self, outDir, fileStem=None, exampleIO=None):
        if fileStem == None:
            fileStem = "examples"
        #if exampleIO == None:
        #    exampleIO = SVMLightExampleIO(os.path.join(outDir, fileStem))
        
        #exampleIO.newFiles()
        self.buildExamples(os.path.join(outDir, fileStem + ".sqlite")) #, exampleIO)
        #exampleIO.closeFiles()  