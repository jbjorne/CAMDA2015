# Loading the data
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import settings
from data.buildExamples import *

def getSpecimens(dbName, projectCode, mutatedGeneId):
    con = connect(dbName)
    specimenIds = set()
    for row in con.execute("SELECT DISTINCT icgc_specimen_id FROM simple_somatic_mutation_open WHERE project_code='"+projectCode+"' AND gene_affected='"+mutatedGeneId+"';"):
        specimenIds.add(row[0])
    return sorted(list(specimenIds))

def execute(dbName, sql):
    con = connect(dbName)
    con.row_factory = sqlite3.Row
    return con.execute(sql)

def getExpressionLevels(dbName, specimenIds):
    con = connect(dbName)
    con.row_factory = sqlite3.Row
    specimenMatch = "('" + "','".join(specimenIds) + "')"
    currentSpecimen = None
    currentVector = {}
    featureVectors = [currentVector]
    featureIds = {}
    for row in con.execute("SELECT * FROM gene_expression WHERE icgc_specimen_id IN " + specimenMatch):
        if currentSpecimen != row["icgc_specimen_id"]:
            if currentSpecimen != None:
                currentVector = {}
                featureVectors.append(currentVector)
            currentSpecimen = row["icgc_specimen_id"]
        if row["gene_stable_id"] not in featureIds:
            featureIds[row["gene_stable_id"]] = len(featureIds)
        currentVector[featureIds[row["gene_stable_id"]]] = row["normalized_expression_level"]
    #con = connect(dbName)

def getMutations(dbName, specimenIds, aaForGenes):
    specimenMatch = "('" + "','".join(specimenIds) + "')"
    mutatedGenes = {}
    mutatedAAs = {}
    for row in execute(dbName, "SELECT icgc_specimen_id,aa_mutation,gene_affected FROM simple_somatic_mutation_open WHERE aa_mutation != '' AND icgc_specimen_id IN " + specimenMatch):
        specimenId = row["icgc_specimen_id"]
        if specimenId not in mutatedGenes:
            mutatedGenes[specimenId] = set()
        mutatedGenes[specimenId].add(row["gene_affected"])
        
        gene = row["gene_affected"]
        if gene in aaForGenes:
            if specimenId not in mutatedAAs:
                mutatedAAs[specimenId] = {}
            if gene not in mutatedAAs[specimenId]:
                mutatedAAs[specimenId][gene] = set()
            mutatedAAs[specimenId][gene].add(row["aa_mutation"])
    return mutatedGenes, mutatedAAs

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

def getCrossSpecimenMutationCounts(mutatedGenes, cutoff=2):
    geneMutations = {}
    for specimenId in mutatedGenes:
        for gene in mutatedGenes[specimenId]:
            if gene not in geneMutations:
                geneMutations[gene] = 0
            geneMutations[gene] += 1
    for gene in geneMutations.keys():
        if geneMutations[gene] < cutoff:
            del geneMutations[gene]
    return geneMutations

dbPath = os.path.join(settings.DATA_PATH, settings.DB_NAME)
specimenIds = getSpecimens(dbPath, "SKCM-US", "ENSG00000178568")
print specimenIds
#getExpressionLevels(dbPath, specimenIds)
mutatedGenes, mutatedAAs = getMutations(dbPath, specimenIds, set(["ENSG00000178568"]))
print mutatedAAs
print "Cross-specimen mutations:", getCrossSpecimenMutationCounts(mutatedGenes, 20)
allMutatedGenes = set()
for specimenId in mutatedGenes:
    for gene in mutatedGenes[specimenId]:
        allMutatedGenes.add(gene)
    mutatedGenes[specimenId] = len(mutatedGenes[specimenId])
print mutatedGenes, len(allMutatedGenes)