import sys, os
basePath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(basePath, "lib"))
from rlscore.learner import rls

class RLSInterface(object):

    def __init__(self, alpha = 1.0):
        self.alpha = alpha

    def fit(self, X, y):
        keyw = {"train_features":X, "train_labels":y}
        learner = rls.RLS(**keyw)
        learner.solve(self.alpha)
        self.model = learner.getModel()
    
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
        return {"alpha": self.alpha}

    def set_params(self, **parameters):
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self