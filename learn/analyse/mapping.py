import os
try:
    import ujson as json
except:
    import json

DATA_PATH = None
ENSEMBL_TO_NAME = None
GENE_MAP = None

def _loadEnsemblToName(filePath = None):
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
        mapping[splits[0]] = splits[1]
    return mapping

def ensemblToName(ensemblId):
    global ENSEMBL_TO_NAME
    if not ENSEMBL_TO_NAME:
        ENSEMBL_TO_NAME = _loadEnsemblToName()
    return ENSEMBL_TO_NAME.get(ensemblId)

# def _loadPanther(filePath = None):
#     global DATA_PATH
#     if filePath == None:
#         filePath = os.path.join(DATA_PATH, "panther", "PTHR10.0_human")
#     print "Reading PANTHER from", filePath
#     f = open(filePath, "rt")
#     lines = f.readlines()
#     f.close()
#     for line in lines:
#         splits = line.strip().split("\t")
#         identifiers = {[x.split(":") for x in splits[0].split("|")]}

def _loadGeneNames(filePath = None):
    global DATA_PATH
    if filePath == None:
        filePath = os.path.join(DATA_PATH, "genenames.org", "hgnc_complete_set.json")
    with open(filePath, "rt") as data_file:    
        data = json.load(data_file)
    keys = ["ensembl_gene_id", "refseq", "hgnc_id"]
    mapping = {key:{} for key in keys}
    for item in data["response"]["docs"]:
        for key in mapping:
            if key in item:
                values = item[key]
                if isinstance(values, basestring):
                    values = [values]
                for value in values:
                    if value not in mapping[key] or item["_version_"] > mapping[key]["_version_"]:
                        #assert value not in mapping[key], (key, value, item, mapping[key][value])
                        mapping[key][value] = item
    return mapping
                

if __name__ == "__main__":
    DATA_PATH = os.path.expanduser("~/data/CAMDA2015-data-local/")
    _loadGeneNames()