from sklearn.svm import SVC
from sklearn.feature_selection import RFE

class RFEWrapper(object):

    def __init__(self, C = 1.0):
        self.C = C

    def fit(self, X, y):
        # fit SVC
        svc = SVC(kernel="linear", C=self.C)
        self.model = svc.fit(X, y)
        # do RFE
        svc = SVC(kernel="linear", C=self.C)
        rfe = RFE(estimator=svc, n_features_to_select=1, step=1)
        rfe.fit(X, y)
        self.feature_importances_ = self._getImportances(rfe.ranking_)
    
    def _getImportances(self, ranking):
        # Convert ranking to an ordered list of feature indices
        selected = [None] * len(ranking)
        for i in range(len(ranking)):
            selected[ranking[i] - 1] = i
        # Map selected features to their importances
        selectedImportances = {}
        for i in range(len(selected)): # 'selected' is assumed to be an ordered list of feature indices
            selectedImportances[selected[i]] = 1.0 / (i + 1) # use 1 / rank to get descending order
        # Make a list of importances for the whole feature space
        importances = []
        for i in range(self.numFeatures):
            if i in selectedImportances:
                importances.append(selectedImportances[i]) # This was a selected feature
            else:
                importances.append(0) # This was a non-selected feature
        return importances
    
    def decision_function(self, X):
        p = self.model.predict(X)
        return p

    def predict(self, X):
        p = self.model.predict(X)
        return p
    
#     def predict_proba(self, X):
#         p = self.model.predict(X)
#         return p
    
    def get_params(self, deep=True):
        return {"C":self.C}

    def set_params(self, **parameters):
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self


