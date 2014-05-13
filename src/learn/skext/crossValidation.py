import numpy as np
from sklearn.utils import check_random_state
from sklearn.cross_validation import _BaseKFold
import itertools

class GroupedKFold(_BaseKFold):
    def __init__(self, groups, n_folds=3, indices=True, shuffle=False,
                 random_state=None, k=None):
        # Get unique groups
        seen = set()
        seen_add = seen.add
        uniqGroups = [x for x in groups if x not in seen and not seen_add(x)]
        # Map index of each unique group to example indices in that group
        self.groupIndices = []
        for groupId in uniqGroups:
            self.groupIndices.append([i for i, x in enumerate(groups) if x == groupId]) 
        # Initialize base classes with number of unique groups
        super(GroupedKFold, self).__init__(len(uniqGroups), n_folds, indices, k)
        random_state = check_random_state(random_state)
        self.idxs = np.arange(len(uniqGroups))
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
            yield itertools.chain([self.groupIndices[x] for x in self.idxs[start:stop]])
            #yield self.idxs[start:stop]
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