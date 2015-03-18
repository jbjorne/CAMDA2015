import sys, os
import json
import matplotlib.pyplot as plt
from collections import OrderedDict

def loadData(sourcePath):
    print "Loading results from", sourcePath
    f = open(sourcePath, "rt")
    results = json.load(f, object_pairs_hook=OrderedDict)["results"]
    f.close()
    projects = {}
    for project in sorted(results.keys()):
        points = results[project]["REMISSION"]["ExtraTreesClassifier"]
        projects[project] = [x["score"] for x in points]  
    return projects

def process(inPath):
    projects = loadData(inPath)
    colors = ["red", "green", "blue"]
    styles = ["--", "-", ":"]
    minY = 0.0
    maxY = 1.0
    for project, color, style in zip(sorted(projects.keys()), colors, styles):
        x = range(0, len(projects[project]))
        points = projects[project]
        plt.plot(x, points, linestyle=style, color=color, label=project)
        minY = min(points)
        maxY = max(points)
    plt.xlabel("#features")
    plt.ylabel("AUC")
    plt.legend(loc=4)
    plt.ylim([minY - 0.1, maxY + 0.1])
    plt.show()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Learning with examples')
    parser.add_argument('-i','--input', help='Feature curve JSON file', default=None)
    options = parser.parse_args()
    
    process(options.input)
