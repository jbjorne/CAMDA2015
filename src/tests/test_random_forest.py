import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_digits

digits = load_digits(n_class=10)

forest = RandomForestClassifier(n_estimators = 100)
forest = forest.fit(digits.data[:-1], digits.target[:-1])
output = forest.predict(digits.data[-1])

print output