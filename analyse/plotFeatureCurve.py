import sys, os
import json
import matplotlib.pyplot as plt
from collections import OrderedDict

def loadData(sourcePath):
    print "Loading results from", sourcePath
    f = open(sourcePath, "rt")
    results = json.load(f, object_pairs_hook=OrderedDict)
    f.close()
    return [x["score"] for x in results]

def process(inPath):
    data = loadData(inPath) 
    x = range(0, len(data))
    print x, data
    plt.plot(x, data, linestyle="--", color="black", label="HSNC-US")
    plt.xlabel("#features")
    plt.ylabel("AUC")
    plt.legend()
    plt.ylim([min(data) - 0.1, max(data) + 0.1])
    plt.show()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Learning with examples')
    parser.add_argument('-i','--input', help='Feature curve JSON file', default=None)
    options = parser.parse_args()
    
    process(options.input)
