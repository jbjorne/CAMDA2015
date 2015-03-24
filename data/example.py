import sys, os
import tempfile
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings

exampleOptions = argparse.ArgumentParser(add_help=False)
exampleOptions.add_argument('-e','--experiment', help='Experiment template', default=None)
exampleOptions.add_argument('-o','--options', help='Experiment template options', default=None)
exampleOptions.add_argument('-b','--database', help='Database location', default=settings.DB_PATH)
#exampleOptions.add_argument('--hidden', help='Inclusion of hidden examples: train,hidden,both (default=skip)', default="skip")
exampleOptions.add_argument('-w','--writer', help='Output writer function (optional)', default='writeNumpyText')

def openOutputFiles(featureFilePath, labelFilePath, writer=None, makeDirs=True):
    writerArgs = None
    opened = {}
    if featureFilePath != None or labelFilePath != None:
        writerArgs = {}
        outFiles = [("fX", featureFilePath), ("fY", labelFilePath)]
        for argName, filename in outFiles:
            if os.path.exists(filename):
                os.remove(filename)
        if writer == writeSVMLight:
            outFiles = [outFiles[0]]
        for argName, filename in outFiles:
            if filename != None:
                if makeDirs:
                    parentDir = os.path.dirname(filename)
                    if parentDir != None and not os.path.exists(parentDir):
                        os.makedirs(parentDir)
                filename = os.path.abspath(os.path.expanduser(filename))
                if filename not in opened:
                    opened[filename] = open(filename, "wt")
                writerArgs[argName] = opened[filename]
    return writerArgs, opened

def evalWriter(writerName):
    return eval(writerName)

def closeOutputFiles(opened, writer, featureFilePath, numFeatures):
    for outFile in opened.values():
        outFile.close()
    if writer == writeNumpyText and featureFilePath != None:
        padNumpyFeatureFile(featureFilePath, numFeatures)
        
def readAuto(featureFilePath, labelFilePath, useFeatures=None):
    if labelFilePath == None or featureFilePath == labelFilePath or not os.path.exists(labelFilePath):
        from sklearn.datasets import load_svmlight_file
        print "Loading SVM-light features and labels from", featureFilePath
        if useFeatures != None:
            raise Exception("useFeatures is not supported with the SVM-light format")
        X, y = load_svmlight_file(featureFilePath)
    else:
        import numpy
        print "Loading numpy txt labels from", labelFilePath
        y = numpy.loadtxt(labelFilePath)
        print "Loading numpy txt features from", featureFilePath
        X = numpy.loadtxt(featureFilePath, usecols=useFeatures)
    return X, y

def writeSVMLight(fX, example, cls, features):
    fX.write(str(cls) + " " + " ".join([str(key) + ":" + str(features[key]) for key in sorted(features.keys())]) + "\n")

def writeNumpyText(fX, fY, example, cls, features):
    if fY != None: # write class
        fY.write(str(cls))
        if fY != fX: # classes go to a separate file
            fY.write("\n")
        else: # classes go to the same file
            fY.write(" ")
    if fX != None: # write features
        index = 0
        line = ""
        for key in sorted(features.keys()):
            while index < key:
                line += "0 "
                index += 1
            line += str(features[key]) + " "
            index = key + 1
        fX.write(line[:-1] + "\n") # remove trailing space before writing the line

def padNumpyFeatureFile(filename, numFeatures):
    filename = os.path.abspath(os.path.expanduser(filename))
    temp = filename + "-tempfile"
    os.rename(filename, temp)
    fI = open(temp, "rt")
    fO = open(filename, "wt")
    for line in fI:
        line = line.strip()
        if line == "":
            line = " 0" * numFeatures
        else:
            line = line + ((numFeatures - line.count(" ") - 1) * " 0")
        line = line.strip()
        fO.write(line + "\n")
    fI.close()
    fO.close()
    os.remove(temp)