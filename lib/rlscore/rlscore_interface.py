from rlscore.learner import rls

class RLSInterface(object):

    def __init__(self, alpha = 1.0):
        self.alpha = alpha

    def fit(self, X, y):
        keyw = {"train_features":X, "train_labels":y}
        learner = rls.RLS(**keyw)
        learner.solve(self.alpha)
        self.model = learner.getModel()

    def predict(self, X):
        p = self.model.predict(X)
        return p
    
    def get_params(self, deep=True):
        return {"alpha": self.alpha}

    def set_params(self, **parameters):
        for parameter, value in parameters.items():
            setattr(self, parameter, value)