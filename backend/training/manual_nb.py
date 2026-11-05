"""Multinomial Naive Bayes implemented from counts and Bayes' rule."""
import numpy as np
from scipy.special import logsumexp
from sklearn.base import BaseEstimator, ClassifierMixin


class ManualMultinomialNB(ClassifierMixin, BaseEstimator):
    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def fit(self, X, y):
        if self.alpha <= 0:
            raise ValueError("Smoothing alpha must be positive.")
        y = np.asarray(y)
        self.classes_, counts = np.unique(y, return_counts=True)
        self.class_log_prior_ = np.log(counts / counts.sum())
        feature_counts = np.stack([np.asarray(X[y == label].sum(axis=0)).ravel() for label in self.classes_])
        smoothed = feature_counts + self.alpha
        self.feature_log_prob_ = np.log(smoothed / smoothed.sum(axis=1, keepdims=True))
        self.n_features_in_ = X.shape[1]
        return self

    def predict_proba(self, X):
        joint = np.asarray(X @ self.feature_log_prob_.T) + self.class_log_prior_
        return np.exp(joint - logsumexp(joint, axis=1, keepdims=True))

    def predict(self, X):
        return self.classes_[self.predict_proba(X).argmax(axis=1)]
