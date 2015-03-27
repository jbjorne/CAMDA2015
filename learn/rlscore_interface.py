import sys, os
basePath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(basePath, "rlscore"))
from rlscore.learner import rls
from rlscore.learner import greedy_rls

class RLScore(object):

    def __init__(self, alpha = 1.0, subsetsize=None):
        self.alpha = alpha
        self.subsetsize = subsetsize

    def fit(self, X, y):
        keyw = {"train_features":X, "train_labels":y}
        if self.subsetsize == None:
            learner = rls.RLS(**keyw)
            learner.solve(self.alpha)
        else:
            keyw["subsetsize"] = self.subsetsize
            learner = greedy_rls.GreedyRLS(regparam=1.0, **keyw)
            learner.solve_cython(self.alpha)
        self.model = learner.getModel()
        if self.subsetsize != None:
            self.numFeatures = X.shape[1]
            self.feature_importances_ = self._getImportances(learner.selected)
    
    def _getImportances(self, selected):
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
        return {"alpha":self.alpha, "subsetsize":self.subsetsize}

    def set_params(self, **parameters):
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self


