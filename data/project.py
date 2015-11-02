import os
import itertools
from numbers import Number
import sqlite3
import math
import time
import json
import inspect
from collections import OrderedDict
import hidden
import writer

class Experiment:
    def _queryExamples(self):
        query = "SELECT " + self.exampleFields + "\n"
        query += "FROM " + self.exampleTable + "\n"
        query += "WHERE "
        if self.projects != None:
            query += "      project_code IN ('" + "','".join(self.projects) + "') AND"
        query += self.exampleWhere
        self.meta["query"] = query
        print "=========================== Example generation query ==========================="
        print query
        print "================================================================================"
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
        
        self.exampleTable = "clinical"
        self.exampleFields = "icgc_donor_id,icgc_specimen_id,project_code,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup"
        self.exampleWhere = None
        self.featureGroups = None
        self.filter = None
        self.hiddenCutoff = 0.3
        self.includeHiddenSet = True
        self.includeTrainingSet = True
        # Generated data
        self.examples = None
        self.meta = None
        # Delayed writing
        self.delayWriting = False
        self.features = None
        self.classIds = None
    
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
        self.meta = {"name":self.__class__.__name__, "time":time.strftime("%c"), "dbFile":self.databasePath, "dbModified":time.strftime("%c", time.localtime(os.path.getmtime(self.databasePath)))}
        self.exampleMeta = []
        if self.delayWriting:
            self.features = []
            self.classIds = []
        self.examples = self._queryExamples()
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
            classId = self.getClassId(self.getLabel(example))
            print classId, str(count) + "/" + str(numExamples)
            if self._filterExample(example):
                print "NOTE: Filtered example"
                continue
            
            features = self._buildFeatures(example)
            self.exampleMeta.append(self.getExampleMeta(example, classId, features))
            if self.delayWriting:
                self.features.append(features)
                self.classIds.append(classId)
            elif exampleWriter != None:
                exampleWriter.writeExamples([classId], [features])
        
        if self.delayWriting:
            self.postBuild()
            self.writeExamples(self.examples, self.features)
        
        self.saveMetaData(metaDataFileName)
    
    def postBuild(self):
        pass
    
    def writeExamples(self, classIds, featureVectors, exampleWriter):
        if exampleWriter != None:
            for classId, features in zip(classIds, featureVectors):
                exampleWriter.writeExample(classId, features)
    
    def getFingerprint(self):
        return inspect.getsource(self.__class__)
    
    def saveMetaData(self, metaDataFileName):
        if metaDataFileName != None:
            print "Writing metadata to", metaDataFileName
            if not os.path.exists(os.path.dirname(metaDataFileName)):
                os.makedirs(os.path.dirname(metaDataFileName))
            f = open(metaDataFileName, "wt")
            output = OrderedDict((("experiment", self.meta), ("source", inspect.getsource(self.__class__)), ("classes", self.classIds), ("features", self.featureIds)))
            if len(self.exampleMeta) > 0:
                output["examples"] = self.exampleMeta
            json.dump(output, f, indent=4)#, separators=(',\n', ':'))
            f.close()
        else:
            print "Experiment metadata not saved"
    
    def writeExamples(self, outDir, fileStem=None, exampleIO=None):
        if fileStem == None:
            fileStem = "examples"
        if exampleIO == None:
            exampleIO = writer.SVMLightExampleIO(os.path.join(outDir, fileStem))
        
        exampleIO.newFiles()
        self.buildExamples(os.path.join(outDir, fileStem + ".meta.json"), exampleIO)
        exampleIO.closeFiles()  