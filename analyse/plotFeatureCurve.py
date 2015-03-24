import sys, os
import json
import matplotlib.pyplot as plt
from collections import OrderedDict

def loadData(sourcePath):
    print "Loading results from", sourcePath
    projects = {}
    for filename in os.listdir(sourcePath):
        if filename.endswith("json"):
            print "Reading result file", filename
            f = open(os.path.join(sourcePath, filename), "rt")
            meta = json.load(f, object_pairs_hook=OrderedDict)
            f.close()
            
            projectName = meta["template"]["project"]
            if projectName not in projects:
                projects[projectName] = {}
            pointIndex = meta["curve"]["count"]
            pointValue = meta["results"]["hidden"]["score"]
            assert pointIndex not in projects[projectName]
            projects[projectName][pointIndex] = pointValue
    for projectName in projects:
        project = projects[projectName]
        vector = []
        for i in range(max(project.keys())):
            if i in project:
                vector.append(project[i])
            else:
                vector.append(None)
        projects[projectName] = vector
    return projects

def process(inPath):
    projects = loadData(inPath)
    colors = ["black", "blue", "red"]
    styles = ["--", "-", ":"]
    minY = 0.0
    maxY = 1.0
    minX = 0.0
    maxX = 1.0
    for project, color, style in zip(sorted(projects.keys()), colors, styles):
        x = range(2, len(projects[project]) + 2)
        points = projects[project]
        plt.plot(x, points, linestyle=style, color=color, label=project)
        minY = min([value for value in points if value != None])
        maxY = max([value for value in points if value != None])
        minX = min(x)
        maxX = max(x)
    plt.xlabel("#features")
    plt.ylabel("AUC")
    plt.legend(loc=4)
    plt.ylim([minY - 0.1, maxY + 0.1])
    plt.xlim([minX, maxX])
    plt.show()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Learning with examples')
    parser.add_argument('-i','--input', help='Feature curve JSON file', default=None)
    options = parser.parse_args()
    
    process(options.input)
