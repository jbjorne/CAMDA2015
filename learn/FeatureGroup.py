import itertools
from numbers import Number

class FeatureGroup:
    def __init__(self):
        self.name = "SSM"
        self.query = "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"
        
    def fgh(self, example):
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
    
    def buildFeatures(self, connection, example):
        queryResult = connection.execute(self.query, (example['icgc_specimen_id'], ))
        featureName = self.buildFeatureName(queryResult)
        
    def buildFeatureName(self, queryResult):
        return self.name + ":" + queryResult['gene_affected'] + ":" + queryResult['consequence_type']
    
    def getFeatureId(self, featureName, queryResult):
        if featureName not in self.featureIds:
            self.featureIds[featureName] = len(self.featureIds)
        return self.featureIds[featureName]