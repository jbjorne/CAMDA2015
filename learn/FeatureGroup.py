class FeatureGroup(object):
    def __init__(self, name, query=None, keys=None):
        self.name = name # "SSM"
        self.query = query # "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"
        self.keys = keys
        if self.query != None and self.keys != None:
            self.query = self.query.replace("KEYS", ",".join(self.keys))
    
    def buildFeatures(self, connection, example, features, featureIds):
        queryResult = connection.execute(self.query, (example['icgc_specimen_id'], ))
        for row in queryResult:
            featureName = self.getFeatureName(row)
            features[self.getFeatureId(featureName, featureIds)] = self.getFeatureValue(row)
    
    def getFeatureValue(self, row):
        return 1
        
    def getFeatureName(self, row):
        return self.name + ":" + ":".join([str(row[key]) for key in self.keys])
        #return self.name + ":" + queryResult['gene_affected'] + ":" + queryResult['consequence_type']
    
    def getFeatureId(self, featureName, featureIds):
        if featureName not in featureIds:
            featureIds[featureName] = len(featureIds)
        return featureIds[featureName]