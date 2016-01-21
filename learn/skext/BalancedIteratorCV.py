from sklearn.cross_validation import StratifiedKFold
from _collections import defaultdict
class BalancedIteratorCV():
    def __init__(self, y_train, n_folds, shuffle, random_state, examples, groupBy):
        assert len(y_train) == len(examples)
        self.cv = StratifiedKFold(y_train=y_train, n_folds=n_folds, shuffle=shuffle, random_state=random_state)
        folds = [x for x in self.cv]
        
        exampleByIndex = {i:examples[i] for i in range(len(examples))}
        for fold in folds:    
            train_indices, test_indices = fold
            # Count examples grouped
            counts = defaultdict(lambda: defaultdict(int))
            indices = defaultdict(lambda: defaultdict(lambda: list))
            i = 0
            for i in train_indices:
                example = exampleByIndex[i]
                counts[example[groupBy]][y_train[i]] += 1
                indices[example[groupBy]][y_train[i]].append(i)
                i += 1
            # Determine per class sizes
            extra = defaultdict(lambda: defaultdict(int))
            for groupKey in counts:
                minorityClassSize = counts[groupKey][min(counts[groupKey], key=counts[groupKey].get)]
                for classId in counts[groupKey]:
                    extra[groupKey][classId] = counts[groupKey] - minorityClassSize
            # Oversample training data
        
    def _getClassDistribution(self, examples):
        counts = defaultdict(lambda: defaultdict(int))
        for example in examples:
            counts[example[groupBy]][example["label"]] += 1
        
    def __len__(self):
        return len(self.cv)
    
    def __iter__(self):
        self._iterIndex = 0
        return self

    def next(self):
        if self._iterIndex >= len(self.folds):
            raise StopIteration
        else:
            i = self._iterIndex
            self._iterIndex += 1
            test_indices = self.folds[i]
            train_indices = np.array([i for i in range(len(self.y)) if i not in set(test_indices)])
            #print (train_indices, test_indices)
            return (train_indices, test_indices)