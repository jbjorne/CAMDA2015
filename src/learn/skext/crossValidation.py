import numpy as np
from sklearn.utils import check_random_state
from sklearn.cross_validation import _BaseKFold

class KFold(_BaseKFold):
    def __init__(self, n, n_folds=3, indices=True, shuffle=False,
                 random_state=None, k=None):
        super(KFold, self).__init__(n, n_folds, indices, k)
        random_state = check_random_state(random_state)
        self.idxs = np.arange(n)
        if shuffle:
            random_state.shuffle(self.idxs)

    def _iter_test_indices(self):
        n = self.n
        n_folds = self.n_folds
        fold_sizes = (n // n_folds) * np.ones(n_folds, dtype=np.int)
        fold_sizes[:n % n_folds] += 1
        current = 0
        for fold_size in fold_sizes:
            start, stop = current, current + fold_size
            yield self.idxs[start:stop]
            current = stop

    def __repr__(self):
        return '%s.%s(n=%i, n_folds=%i)' % (
            self.__class__.__module__,
            self.__class__.__name__,
            self.n,
            self.n_folds,
        )

    def __len__(self):
        return self.n_folds