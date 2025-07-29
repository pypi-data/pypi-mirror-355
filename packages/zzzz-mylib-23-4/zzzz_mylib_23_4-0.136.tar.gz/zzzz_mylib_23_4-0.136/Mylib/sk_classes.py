from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.ensemble import BaggingClassifier
from sklearn.linear_model import LogisticRegression


class LRBaggingClassifier(BaseEstimator, ClassifierMixin):
    def __init__(
        self,
        penalty,
        solver,
        C,
        l1_ratio,
        max_iter,
        n_estimators,
        max_samples,
        max_features,
        warm_start=True,
    ):
        lr = LogisticRegression(
            penalty=penalty,
            solver=solver,
            C=C,
            l1_ratio=l1_ratio,
            max_iter=max_iter,
            warm_start=warm_start,
        )
        self.model = BaggingClassifier(
            base_estimator=lr,
            n_estimators=n_estimators,
            max_samples=max_samples,
            max_features=max_features,
        )

    def fit(self, X, y):
        self.model.fit(X, y)

        self.is_fitted_ = True
        return self

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)
