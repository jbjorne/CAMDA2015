import os
DATA_PATH = None
ENSEMBL_TO_NAME = None

def _loadEnsemblToName(self, filePath):
    global DATA_PATH
    mapping = {}
    if filePath == None:
        filePath = os.path.join(DATA_PATH, "ensembl-gene-to-name.tsv")
    print "Reading ENSEMBL to gene name mapping from", filePath
    f = open(filePath, "rt")
    f.readline() # skip headers
    lines = f.readlines()
    f.close()
    for line in lines:
        splits = line.split()
        self.mapping[splits[0]] = splits[1]
    return mapping

def getName(ensemblId):
    global ENSEMBL_TO_NAME
    if not ENSEMBL_TO_NAME:
        ENSEMBL_TO_NAME = _loadEnsemblToName()
    return ENSEMBL_TO_NAME.get(ensemblId)
    