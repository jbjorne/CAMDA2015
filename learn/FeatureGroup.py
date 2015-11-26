class FeatureGroup(object):
    def __init__(self, name, query=None, keys=None):
        self.name = name # "SSM"
        self.query = query # "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"
        self.keys = keys
        if self.query != None and self.keys != None:
            self.query = self.query.replace("KEYS", ",".join(self.keys))
    
    def processExample(self, connection, example, exampleFeatures, featureIds):
        queryResult = connection.execute(self.query, (example['icgc_specimen_id'], ))
        for row in queryResult:
            for feature in self.buildFeatures(row):
                if len(feature) > 1 and isinstance(feature[-1], int):
                    featureName, featureValue = feature[:-1], feature[-1]
                else:
                    featureName = feature
                    featureValue = 1 # Use default weight for feature
                featureName = self._getFeatureNameAsString(featureName)
                exampleFeatures[self._getFeatureId(featureName, featureIds)] = featureValue

    def buildFeatures(self, row):
        return [[row[key] for key in self.keys]]
        #return self.name + ":" + queryResult['gene_affected'] + ":" + queryResult['consequence_type']
    
    def _getFeatureNameAsString(self, featureNameParts):
        return self.name + ":" + ":".join([str(x) for x in featureNameParts])        
    
    def _getFeatureId(self, featureName, featureIds):
        if featureName not in featureIds:
            featureIds[featureName] = len(featureIds)
        return featureIds[featureName]