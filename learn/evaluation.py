def aucForPredictions(labels, predictions):
    return listwisePerformance(labels, predictions)

def getClassPredictions(probabilities, classes):
    predictions = []
    for prob in probabilities:
        assert len(prob) == len(classes)
        if prob[0] > prob[1]:
            predictions.append(prob[0] * classes[0])
        else:
            predictions.append(prob[1] * classes[1])
    return predictions

def aucForProbabilites(labels, probabilities, classes):
    return listwisePerformance(labels, getClassPredictions(probabilities, classes))

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