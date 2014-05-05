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
        for key in sorted(features.keys()):
            while index < key:
                fX.write("0 ")
                index += 1
            fX.write(str(features[key]) + " ")
            index = key + 1
        fX.write("\n")

def padNumpyFeatureFile(filename, numFeatures):
    temp = tempfile.mktemp()
    filename = os.path.abspath(os.path.expanduser(filename))
    os.rename(filename, temp)
    fI = open(temp, "rt")
    fO = open(filename, "wt")
    for line in fI:
        line = line.rstrip()
        fO.write(line + max(0, numFeatures - line.count(" ")) * " 0" + "\n")
    fI.close()
    fO.close()
    os.remove(temp)