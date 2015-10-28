import os
import itertools
from numbers import Number
import math
import hidden
import sqlite3
import example
import time
import json
import inspect
from collections import OrderedDict

def connect(con):
    if isinstance(con, basestring):
        con = sqlite3.connect(con) # @UndefinedVariable
        con.row_factory = sqlite3.Row # @UndefinedVariable
        con.create_function("log", 1, math.log)
    return con

class Experiment:
    def _queryExamples(self):
        query = "SELECT " + self.exampleFields + "\n"
        query += "FROM " + self.exampleTable + "\n"
        query += "WHERE "
        if self.projects != None:
            query += " project_code IN " + self.projects + " AND" + "\n"
        query += self.exampleWhere
        return [dict(x) for x in self.getConnection().execute(query)]
    
    def getLabel(self, example):
        return 'remission' in example['disease_status_last_followup']
    
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
        # Database
        self.databasePath = None
        self._connection = None
        # Id sets
        self.featureIds = {}
        self.classIds = {'True':1, 'False':-1}
        # General
        self.projects = None
        
        self.exampleTable = "clinical"
        self.exampleFields = "icgc_donor_id,icgc_specimen_id,project_code,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup"
        self.exampleWhere = None
        self.featureGroups = None
        self.filter = None
        self.hiddenCutoff = 0.3
        self.includeHiddenSet = True
        self.includeTrainingSet = True
        # Generated data
        self.examples = []
        self.meta = []
        # Output files
        self.metaDataFileName = None
        self.writer = None
    
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
    
    def getFeatureId(self, featureName):
        if featureName not in self.featureIds:
            self.featureIds[featureName] = len(self.featureIds)
        return self.featureIds[featureName]
        
    def _buildFeatures(self, example):
        features = {}
        for groupIndex in range(len(self.featureGroups)):
            featureGroup = self.featureGroups[groupIndex]
            for row in self._queryFeatures(featureGroup, example): #featureGroup(con=self.getConnection(), example=example):
                for key, value in itertools.izip(*[iter(row)] * 2): # iterate over each consecutive key,value columns pair
                    if not isinstance(key, basestring):
                        raise Exception("Non-string feature key '" + str(key) + "' in feature group " + str(groupIndex))
                    if not isinstance(value, Number):
                        raise Exception("Non-number feature value '" + str(value) + "' in feature group " + str(groupIndex))
                    features[self.getFeatureId(key)] = value
        if len(features) == 0:
            print "WARNING: example has no features"
        return features
    
    def _queryFeatures(self, featureGroup, example):
        return self.getConnection().execute(featureGroup, (example['icgc_specimen_id'], ) )
    
    def _filterExample(self, example):
        if self.filter != None:
            return len([x for x in self.getConnection().execute(self.filter, (example['icgc_specimen_id'], ) )]) == 0
        return False
    
    def getExampleMeta(self, example, classId, features):
        return dict(example, label=str(classId), features=len(features))
    
    def buildExamples(self, metaDataFileName=None, exampleWriter=None):
        print "Template:", self.__class__.__name__
        self.examples = self._queryExamples()
        self.meta = []
        numHidden = hidden.setHiddenValuesByFraction(self.examples, self.hiddenCutoff)
        numExamples = len(self.examples)
        print "Examples " +  str(numExamples) + ", hidden " + str(numHidden)
        count = 0
        for example in self.examples:
            count += 1
            if not self.generateOrNot(example):
                continue
            example["set"] = "hidden" if example["hidden"] < self.hiddenCutoff else "train"

            print "Processing example", example,
            classId = self.getClassId(example)
            print classId, str(count) + "/" + str(numExamples)
            if self._filterExample(example):
                print "NOTE: Filtered example"
                continue
            
            features = self._buildFeatures(example)
            self.meta.append(self.getExampleMeta(example, classId, features))
            if exampleWriter != None:
                exampleWriter.writeExample(classId, features)
        
        self.saveMetaData()
    
    def getFingerprint(self):
        return inspect.getsource(self.__class__)
    
    def saveMetaData(self):
        if self.metaDataFileName != None:
            if not os.path.exists(os.path.dirname(self.metaDataFileName)):
                os.makedirs(os.path.dirname(self.metaDataFileName))
            f = open(self.metaDataFileName, "wt")
            experimentMeta = {"name":self.name, "time":time.strftime("%c"), "dbFile":self.databasePath,
                              "dbModified":time.strftime("%c", time.localtime(os.path.getmtime(self.databasePath)))}
            output = OrderedDict((("experiment", experimentMeta), ("source", inspect.getsource(self.__class__)), ("classes", self.classIds), ("features", self.featureIds)))
            if len(self.meta) > 0:
                output["examples"] = self.meta
            json.dump(output, f, indent=4)#, separators=(',\n', ':'))
            f.close()
        
#     def writeExample(self, example, classId, features):
#         self.writer()
#     
#     def writeExamples(self, exampleIO, metaFilePath): 
#         con = self.getConnection()
#         writerArgs, opened = example.openOutputFiles(featureFilePath, labelFilePath, writer)
#         experimentMeta = {"X":featureFilePath, "y":labelFilePath, "writer":self.writer.__name__}
#         if "fY" not in writerArgs:
#             del experimentMeta["y"]
#         featureIds = getExamples(con, experimentName, writer, writerArgs, metaFilePath, experimentOptions, experimentMeta)
#         example.closeOutputFiles(opened, writer, featureFilePath, len(featureIds))
    