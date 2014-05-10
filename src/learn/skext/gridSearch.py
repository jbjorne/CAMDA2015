import numpy as np
from collections import Sized
import numbers
import time
from sklearn.grid_search import BaseSearchCV, _CVScoreTuple, is_classifier
from sklearn.utils.validation import _num_samples, check_arrays
from sklearn.metrics.scorer import _deprecate_loss_and_score_funcs
from sklearn.cross_validation import check_cv
from sklearn.base import clone
from sklearn.externals.joblib import Parallel, delayed, logger
from sklearn.utils import safe_mask

def fit_grid_point_extended(X, y, base_estimator, parameters, train, test, scorer,
                   verbose, loss_func=None, **fit_params):
    """Run fit on one set of parameters.

Parameters
----------
X : array-like, sparse matrix or list
Input data.

y : array-like or None
Targets for input data.

base_estimator : estimator object
This estimator will be cloned and then fitted.

parameters : dict
Parameters to be set on base_estimator clone for this grid point.

train : ndarray, dtype int or bool
Boolean mask or indices for training set.

test : ndarray, dtype int or bool
Boolean mask or indices for test set.

scorer : callable or None.
If provided must be a scorer callable object / function with signature
``scorer(estimator, X, y)``.

verbose : int
Verbosity level.

**fit_params : kwargs
Additional parameter passed to the fit function of the estimator.


Returns
-------
score : float
Score of this parameter setting on given training / test split.

parameters : dict
The parameters that have been evaluated.

n_samples_test : int
Number of test samples in this split.
"""
    if verbose > 1:
        start_time = time.time()
        msg = '%s' % (', '.join('%s=%s' % (k, v)
                      for k, v in parameters.items()))
        print("[GridSearchCV] %s %s" % (msg, (64 - len(msg)) * '.'))

    # update parameters of the classifier after a copy of its base structure
    clf = clone(base_estimator)
    clf.set_params(**parameters)

    if hasattr(base_estimator, 'kernel') and callable(base_estimator.kernel):
        # cannot compute the kernel values with custom function
        raise ValueError("Cannot use a custom kernel function. "
                         "Precompute the kernel matrix instead.")

    if not hasattr(X, "shape"):
        if getattr(base_estimator, "_pairwise", False):
            raise ValueError("Precomputed kernels or affinity matrices have "
                             "to be passed as arrays or sparse matrices.")
        X_train = [X[idx] for idx in train]
        X_test = [X[idx] for idx in test]
    else:
        if getattr(base_estimator, "_pairwise", False):
            # X is a precomputed square kernel matrix
            if X.shape[0] != X.shape[1]:
                raise ValueError("X should be a square kernel matrix")
            X_train = X[np.ix_(train, train)]
            X_test = X[np.ix_(test, train)]
        else:
            X_train = X[safe_mask(X, train)]
            X_test = X[safe_mask(X, test)]

    if y is not None:
        y_test = y[safe_mask(y, test)]
        y_train = y[safe_mask(y, train)]
        clf.fit(X_train, y_train, **fit_params)

        if scorer is not None:
            this_score = scorer(clf, X_test, y_test)
        else:
            this_score = clf.score(X_test, y_test)
    else:
        clf.fit(X_train, **fit_params)
        if scorer is not None:
            this_score = scorer(clf, X_test)
        else:
            this_score = clf.score(X_test)

    if not isinstance(this_score, numbers.Number):
        raise ValueError("scoring must return a number, got %s (%s)"
                         " instead." % (str(this_score), type(this_score)))

    if verbose > 2:
        msg += ", score=%f" % this_score
    if verbose > 1:
        end_msg = "%s -%s" % (msg,
                              logger.short_format_time(time.time() -
                                                       start_time))
        print("[GridSearchCV] %s %s" % ((64 - len(end_msg)) * '.', end_msg))
    return this_score, parameters, _num_samples(X_test)

class ExtendedBaseSearchCV(BaseSearchCV):
    """Base class for hyper parameter search with cross-validation."""

    def _fit(self, X, y, parameter_iterable):
        """Actual fitting, performing the search over parameters."""

        estimator = self.estimator
        cv = self.cv

        n_samples = _num_samples(X)
        X, y = check_arrays(X, y, allow_lists=True, sparse_format='csr')

        self.scorer_ = _deprecate_loss_and_score_funcs(
            self.loss_func, self.score_func, self.scoring)

        if y is not None:
            if len(y) != n_samples:
                raise ValueError('Target variable (y) has a different number '
                                 'of samples (%i) than data (X: %i samples)'
                                 % (len(y), n_samples))
            y = np.asarray(y)
        cv = check_cv(cv, X, y, classifier=is_classifier(estimator))

        if self.verbose > 0:
            if isinstance(parameter_iterable, Sized):
                n_candidates = len(parameter_iterable)
                print("Fitting {0} folds for each of {1} candidates, totalling"
                      " {2} fits".format(len(cv), n_candidates,
                                         n_candidates * len(cv)))

        base_estimator = clone(self.estimator)

        pre_dispatch = self.pre_dispatch

        out = Parallel(
            n_jobs=self.n_jobs, verbose=self.verbose,
            pre_dispatch=pre_dispatch)(
                delayed(fit_grid_point_extended)(
                    X, y, base_estimator, parameters, train, test,
                    self.scorer_, self.verbose, **self.fit_params)
                for parameters in parameter_iterable
                for train, test in cv)

        # Out is a list of triplet: score, estimator, n_test_samples
        n_fits = len(out)
        n_folds = len(cv)

        scores = list()
        grid_scores = list()
        for grid_start in range(0, n_fits, n_folds):
            n_test_samples = 0
            score = 0
            all_scores = []
            for this_score, parameters, this_n_test_samples in \
                    out[grid_start:grid_start + n_folds]:
                all_scores.append(this_score)
                if self.iid:
                    this_score *= this_n_test_samples
                    n_test_samples += this_n_test_samples
                score += this_score
            if self.iid:
                score /= float(n_test_samples)
            else:
                score /= float(n_folds)
            scores.append((score, parameters))
            # TODO: shall we also store the test_fold_sizes?
            grid_scores.append(_CVScoreTuple(
                parameters,
                score,
                np.array(all_scores)))
        # Store the computed scores
        self.grid_scores_ = grid_scores

        # Find the best parameters by comparing on the mean validation score:
        # note that `sorted` is deterministic in the way it breaks ties
        best = sorted(grid_scores, key=lambda x: x.mean_validation_score,
                      reverse=True)[0]
        self.best_params_ = best.parameters
        self.best_score_ = best.mean_validation_score

        if self.refit:
            # fit the best estimator using the entire dataset
            # clone first to work around broken estimators
            best_estimator = clone(base_estimator).set_params(
                **best.parameters)
            if y is not None:
                best_estimator.fit(X, y, **self.fit_params)
            else:
                best_estimator.fit(X, **self.fit_params)
            self.best_estimator_ = best_estimator
        return self

