class FeatureGroup:
    def __init__(self, name, query=None, keys=None):
        self.name = None # "SSM"
        self.query = None # "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"
        self.keys = None
        if self.query != None and self.keys != None:
            self.query = self.query.replace("KEYS", ",".join(self.keys))
    
    def buildFeatures(self, connection, example, features, featureIds):
        queryResult = connection.execute(self.query, (example['icgc_specimen_id'], ))
        featureName = self.buildFeatureName(queryResult)
        features[self.getFeatureId(featureName, queryResult)] = self.getFeatureValue(queryResult)
    
    def getFeatureValue(self, queryResult):
        return 1
        
    def getFeatureName(self, queryResult):
        return self.name + ":" + ":".join(queryResult[key] for key in self.keys)
        #return self.name + ":" + queryResult['gene_affected'] + ":" + queryResult['consequence_type']
    
    def getFeatureId(self, featureName, featureIds):
        if featureName not in self.featureIds:
            self.featureIds[featureName] = len(self.featureIds)
        return self.featureIds[featureName]