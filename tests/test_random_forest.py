import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn import cross_validation
from sklearn import datasets
from sklearn import svm

#digits = load_digits(n_class=2)
iris = datasets.load_iris()
#X_train, X_test, y_train, y_test = cross_validation.train_test_split(iris.data, iris.target, test_size=0.4, random_state=0)

clf = svm.SVC(kernel='linear', C=1)
scores = cross_validation.cross_val_score(clf, iris.data, iris.target, cv=5, scoring='f1')
print scores
print("Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))

# forest = RandomForestClassifier(n_estimators = 100)
# forest = forest.fit(digits.data[:-1], digits.target[:-1])
# output = forest.predict(digits.data[-1])
#print output