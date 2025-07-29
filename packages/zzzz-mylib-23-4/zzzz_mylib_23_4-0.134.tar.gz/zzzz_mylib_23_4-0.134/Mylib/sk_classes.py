from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin


class LRBaggingClassifier(BaseEstimator, ClassifierMixin): 
    def __init__(self, ):
        ....

    def fit(self, X, y):
        return self

    def predict(self, X):
        .....

    def predict_proba(self, X):
        ....