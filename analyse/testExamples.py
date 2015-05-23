import json
import sklearn.metrics

def listwisePerformance(correct, predicted):
    assert len(correct) == len(predicted)
    pos, neg = 0., 0.
    posindices = []
    negindices = []
    for i in range(len(correct)):
        if correct[i]>0:
            pos += 1.
            posindices.append(i)
        else:
            neg += 1
            negindices.append(i)
    auc = 0.
    for i in posindices:
        for j in negindices:
            if predicted[i] > predicted[j]:
                auc += 1.
            elif predicted[i] == predicted[j]:
                auc += 0.5
    auc /= pos * neg

    return auc 

def addToProject(example, project, projects, classDist, predDist, origPreds):
    predictions = example["classification"]["prediction"]
    prediction = predictions[1]
    if prediction > 0.5:
        prediction = 1.0
    else:
        prediction = -1.0
    cls = float(example["label"])
    if project == None:
        project = example["project_code"]
    if project not in projects:
        projects[project] = [[],[]]
        classDist[project] = [0, 0]
        predDist[project] = [0, 0]
        origPreds[project] = []
    origPreds[project].append(predictions)
    if prediction > 0.5:
        predDist[project][0] += 1
    else:
        predDist[project][1] += 1
    if float(example["label"]) > 0:
        classDist[project][0] += 1
    else:
        classDist[project][1] += 1
    projects[project][0].append(cls)
    projects[project][1].append(prediction)

def process(inPath, targetSet):
    print "Loading JSON"
    #f = open("/home/jari/Dropbox/CAMDA2015-exp/learn-REMISSION_MUT_ALL-ETC-150520/example-ETC.json", "rt")
    f = open(inPath, "rt")
    results = json.load(f)
    f.close()
    
    #y_true = []
    #y_score = []
    projects = {}
    classDist = {}
    predDist = {}
    origPreds = {}
    
    print "Processing examples"
    
    for example in results["examples"]:
        if example["set"] == targetSet:
            #if predictions[0] > predictions[1]:
            #    prediction = -predictions[0]
            #else:
            #    prediction = predictions[1]
            addToProject(example, None, projects, classDist, predDist, origPreds)
            addToProject(example, "<ALL>", projects, classDist, predDist, origPreds)
    
    print
    
#     from collections import defaultdict
#     counts = defaultdict(int)
#     for i in range(len(y_true)):
#         counts[(y_true[i], y_score[i])] += 1
#     print counts
#     print (len([x for x in y_true if x > 0]), len([x for x in y_true if x < 0]))
    
    #print sklearn.metrics.auc(y_true, y_score, reorder=True)
    #print "AUC", sklearn.metrics.roc_auc_score(y_true, y_score), listwisePerformance(y_true, y_score)
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
        #counts = None #(len(projects[project][0]), len([x for x in projects[project][1] if x > 1]))
        #print projects[project]
        if project == "THCA-SA":
            print projects[project], origPreds[project]
        print project, size, classDist[project], predDist[project],
        if classDist[project][0] > 0 and classDist[project][1] > 0:
            print sklearn.metrics.roc_auc_score(projects[project][0], projects[project][1]), listwisePerformance(projects[project][0], projects[project][1])
        else:
            print #, sklearn.metrics.accuracy_score(projects[project][0], projects[project][1])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Learning with examples')
    parser.add_argument('-i','--input', help='JSON file', default=None)
    parser.add_argument('-s','--set', help='', default="hidden")
    options = parser.parse_args()
    
    process(options.input, options.set)