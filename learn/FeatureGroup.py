class FeatureGroup(object):
    def __init__(self, name, query=None, keys=None):
        self.name = name # "SSM"
        self.query = query # "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"
        self.keys = keys
        if self.query != None and self.keys != None:
            self.query = self.query.replace("KEYS", ",".join(self.keys))
    
    def processExample(self, connection, example, exampleFeatures, featureIds):
        queryResult = connection.execute(self.query, (example['icgc_specimen_id'], ))
        for row in [x for x in queryResult]:
            features, values = self.buildFeatures(row)
            if values == None:
                values = [1] * len(features) # Use default weight for all features
            assert len(features) == len(values)
            for feature, value in zip(features, values):
                if not isinstance(feature, basestring):
                    feature = self._getFeatureNameAsString(feature)
                exampleFeatures[self._getFeatureId(feature, featureIds)] = value
    
    def buildFeatures(self, row):
        return [[row[key] for key in self.keys]], [1]
        #return self.name + ":" + queryResult['gene_affected'] + ":" + queryResult['consequence_type']
    
    def _getFeatureNameAsString(self, featureNameParts):
        return self.name + ":" + ":".join([str(x) for x in featureNameParts])        
    
    def _getFeatureId(self, featureName, featureIds):
        if featureName not in featureIds:
            featureIds[featureName] = len(featureIds)
        return featureIds[featureName]