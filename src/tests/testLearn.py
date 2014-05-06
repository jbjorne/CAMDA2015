import numpy
import json

def test(XPath, yPath, metaPath):
    y = numpy.loadtxt(yPath)
    X = numpy.loadtxt(XPath)
    meta = {}
    if metaPath != None:
        meta = json.load(metaPath)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Learning with examples')
    parser.add_argument('-x','--features', help='Input file for feature vectors (X)')
    parser.add_argument('-y','--labels', help='Input file for class labels (Y)')
    parser.add_argument('-m','--meta', help='Metadata input file name (optional)', default=None)
    options = parser.parse_args()
    
    test(options.features, options.labels, options.meta)