# Loading the data
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import settings
from data.buildExamples import *

def getSamples(dbName, projectCode, mutatedGeneId):
    con = connect(dbName)
    sampleIds = set()
    for row in con.execute("SELECT DISTINCT icgc_sample_id FROM simple_somatic_mutation_open WHERE project_code='"+projectCode+"' AND gene_affected='"+mutatedGeneId+"';"):
        sampleIds.add(row[0])
    return sorted(list(sampleIds))

def getExpressionLevels(dbName, sampleIds):
    con = connect(dbName)

def getExpression(dbName, sql, classColumn, featureColumns, classIds, featureIds):
    con = connect(dbName)
    con.row_factory = sqlite3.Row
    classes = []
    features = []
    for row in con.execute(sql):
        if classColumn != None:
            classes.append(classIds[row[classColumn]])
        featureVector = {}
        for column in featureColumns:
            value = row[column]
            featureVector[featureIds[(column, value)]] = 1
        features.append(featureVector)
    return classes, features

dbPath = os.path.join(settings.DATA_PATH, settings.DB_NAME)
sampleIds = getSamples(dbPath, "SKCM-US", "ENSG00000178568")
print sampleIds