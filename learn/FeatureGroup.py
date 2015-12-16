class FeatureGroup(object):
    def __init__(self, name, query=None, keys=None, required=True, dummy=False):
        self.name = name # "SSM"
        self.query = query # "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"
        self.keys = keys
        if self.query != None and self.keys != None:
            self.query = self.query.replace("KEYS", ",".join(self.keys))
        self.required = required
        self.dummy = dummy
    
    def processExample(self, connection, example, exampleFeatures, featureIds, meta):
        if self.query:
            queryResult = connection.execute(self.query, (example['icgc_specimen_id'], ))
        else:
            queryResult = [example]
        numFeatures = 0
        for row in [x for x in queryResult]:
            features, values = self.buildFeatures(row)
            numFeatures += len(features)
            if values == None:
                values = [1] * len(features) # Use default weight for all features
            assert len(features) == len(values)
            if not self.dummy:
                for feature, value in zip(features, values):
                    if not isinstance(feature, basestring):
                        feature = self._getFeatureNameAsString(feature)
                    exampleFeatures[self._getFeatureId(feature, featureIds, meta)] = value
        return numFeatures > 0 if self.required else True
    
    def buildFeatures(self, row):
        return [[row[key] for key in self.keys]], [1]
        #return self.name + ":" + queryResult['gene_affected'] + ":" + queryResult['consequence_type']
    
    def _getFeatureNameAsString(self, featureNameParts):
        return self.name + ":" + ":".join([str(x) for x in featureNameParts])        
    
    def _getFeatureId(self, featureName, featureIds, meta):
        if featureName not in featureIds:
            featureIds[featureName] = len(featureIds)
            meta.insert("feature", {"name":featureName, "id":featureIds[featureName]})
        return featureIds[featureName]