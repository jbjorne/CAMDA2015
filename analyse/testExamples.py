import json
import sklearn.metrics

print "Loading JSON"
#f = open("/home/jari/Dropbox/CAMDA2015-exp/learn-REMISSION_MUT_ALL-ETC-150520/example-ETC.json", "rt")
f = open("/tmp/tmp-examples.json", "rt")
results = json.load(f)
f.close()

y_true = []
y_score = []
projects = {}
classDist = {}

print "Processing examples"

for example in results["examples"]:
    if example["set"] == "hidden":
        y_true.append(float(example["label"]))
        y_score.append(float(example["classification"]["prediction"]))
        if example["project_code"] not in projects:
            projects[example["project_code"]] = [[],[]]
            classDist[example["project_code"]] = [0, 0]
        if float(example["label"]) > 0:
            classDist[example["project_code"]][0] += 1
        else:
            classDist[example["project_code"]][1] += 1
        projects[example["project_code"]][0].append(float(example["label"]))
        projects[example["project_code"]][1].append(float(example["classification"]["prediction"]))

print

from collections import defaultdict
counts = defaultdict(int)
for i in range(len(y_true)):
    counts[(y_true[i], y_score[i])] += 1
print counts
print (len([x for x in y_true if x > 0]), len([x for x in y_true if x < 0]))

#print sklearn.metrics.auc(y_true, y_score, reorder=True)
print "AUC", sklearn.metrics.roc_auc_score(y_true, y_score)
#print "APB F1", sklearn.metrics.f1_score(y_true, len(y_true) * [1])
#print "F1", sklearn.metrics.f1_score(y_true, y_score)
#print sklearn.metrics.accuracy_score(y_true, y_score)
#print sklearn.metrics.average_precision_score(y_true, y_score)
#print sklearn.metrics.precision_score(y_true, y_score)
#print sklearn.metrics.recall_score(y_true, y_score)

print
sizes = []
for project in sorted(projects.keys()):
    sizes.append((len(projects[project][0]), project))
for size, project in sorted(sizes):
    counts = None #(len(projects[project][0]), len([x for x in projects[project][1] if x > 1]))
    if len(set(projects[project][0])) > 1 and len(set(projects[project][1])) > 1:
        print project, size, classDist[project], sklearn.metrics.roc_auc_score(projects[project][0], projects[project][1])
    else:
        print project, size, classDist[project], sklearn.metrics.accuracy_score(projects[project][0], projects[project][1])
