import sys, os
import json
import matplotlib.pyplot as plt
from collections import OrderedDict

def loadData(sourcePath, filter=None):
    print "Loading results from", sourcePath
    projects = {}
    for filename in os.listdir(sourcePath):
        if filter and filter not in filename:
            continue
        if filename.endswith("json"):
            print "Reading result file", filename
            f = open(os.path.join(sourcePath, filename), "rt")
            meta = json.load(f, object_pairs_hook=OrderedDict)
            f.close()
            
            projectName = meta["template"]["project"]
            classifierName = meta["results"]["hidden"]["classifier"]
            if classifierName not in projects:
                projects[classifierName] = {}
            if projectName not in projects[classifierName]:
                project = {}
                projects[classifierName][projectName] = project
            else:
                project = projects[classifierName][projectName]
            
            pointIndex = meta["curve"]["count"]
            pointValue = meta["results"]["hidden"]["score"]
            assert pointIndex not in project
            project[pointIndex] = pointValue
    
    for classifierName in projects:
        for projectName in projects[classifierName]:
            project = projects[classifierName][projectName]
            vector = []
            for i in range(max(project.keys())):
                if i in project:
                    vector.append(project[i])
                else:
                    vector.append(None)
            projects[classifierName][projectName] = vector
    return projects

def process(inPath, filter=None):
    projects = loadData(inPath, filter)
    outPath = os.path.join(os.path.dirname(inPath), "figures")
    if not os.path.exists(outPath):
        os.makedirs(outPath)
    
    colors = {"HNSC-US":"black", "KIRC-US":"blue", "LUAD-US":"red"}
    styles = {"HNSC-US":"--", "KIRC-US":"-", "LUAD-US":":"}
         
    for classifierName in projects:
        minY = 1.0
        maxY = 0.0
        minX = 1.0
        maxX = 0.0
        for projectName in projects[classifierName]:
            points = projects[classifierName][projectName]
            x = range(2, len(points) + 2)
            plt.plot(x, points, linestyle=styles[projectName], color=colors[projectName], label=projectName)
            plt.xlabel("#features")
            plt.ylabel("AUC")
            plt.legend(loc=4)
            minY = min([minY] + [value for value in points if value != None])
            maxY = max([maxY] + [value for value in points if value != None])
            minX = min([minX] + x)
            maxX = max([maxX] + x)
            plt.ylim([minY - 0.01, maxY + 0.01])
            plt.xlim([minX, maxX])
        plt.savefig(os.path.join(outPath, classifierName + ".png"))
        plt.cla()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Learning with examples')
    parser.add_argument('-i','--input', help='Feature curve JSON file', default=None)
    parser.add_argument('-f','--filter', help='', default=None)
    options = parser.parse_args()
    
    process(options.input, options.filter)
