import sys, os
import tempfile

def writeSVMLight(fX, fY, example, cls, features):
    fX.write(str(cls) + " " + " ".join([str(key) + ":" + '{0:f}'.format(features[key]) for key in sorted(features.keys())]) + "\n")

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
    temp = tempfile.mktemp()
    filename = os.path.abspath(os.path.expanduser(filename))
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