from rlscore.learner import rls

class RLSInterface(object):

    def __init__(self, alpha = 1.0):
        self.regparam = alpha

    def fit(self, X, y):
        keyw = {"train_features":X, "train_labels":y}
        learner = rls.RLS(**keyw)
        learner.solve(self.regparam)
        self.model = learner.getModel()

    def predict(self, X):
        p = self.model.predict(X)
        return p
