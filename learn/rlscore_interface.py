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
        if self.fcount == None:
            learner = rls.RLS(**keyw)
        else:
            keyw["subsetsize"] = self.subsetsize
            learner = greedy_rls.GreedyRLS(**keyw)
        learner.solve(self.alpha)
        self.model = learner.getModel()
        if self.subsetsize != None:
            self.selected = learner.selected
    
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


