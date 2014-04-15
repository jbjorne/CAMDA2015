import csv, sqlite3
import re
import os, sys

dataPath = os.path.expanduser("~/data/CAMDA2014/ICGC/Breast_Invasive_Carcinoma-TCGA-US/")

def defineColumns(header, columnTypes, defaultType="text"):
    columns = []
    for i in range(len(header)):
        if i in columnTypes:
            columns += columnTypes[i]
        else:
            matched = False
            for key in columnTypes:
                if key is not int and key.match(header[i]):
                    columns.append((header[i], columnTypes[key]))
                    matched = True
                    break
            if not matched:
                columns.append((header[i], defaultType))
    return columns

def defineTable(tableName, columns, primaryKey = None):
    s = "CREATE TABLE IF NOT EXISTS " + tableName + "(" + ",".join([x[0] + " " + x[1] for x in columns])
    if primaryKey != None:
        s += ", PRIMARY KEY (" + ",".join(primaryKey) + ")"
    s += ");"
    #print s
    return s

def defineInsert(tableName, columns, ignoreExisting=True):
    if ignoreExisting:
        s = "INSERT OR IGNORE INTO "
    else:
        s = "INSERT INTO "
    return s + tableName + "(" + ",".join([x[0] for x in columns]) + ")" + " values (" + ",".join(["?"]*len(columns)) + ")"

def tableFromCSV(dbName, tableName, csvFileName, columnTypes, primaryKey=None, drop=False):  
    con = sqlite3.connect(dbName)
    data = csv.reader(open(csvFileName), delimiter='\t')
    header = data.next()
    
    columns = defineColumns(header, columnTypes)
    if drop:
        con.execute("DROP TABLE IF EXISTS " + tableName + ";")
    con.execute(defineTable(tableName, columns, primaryKey))
    insert = defineInsert(tableName, columns)
    #print insert
    con.executemany(insert, data)
    
    con.commit()
    con.close()
    
tableFromCSV(dataPath + "BRCA-US.sqlite", "clinical", dataPath + "clinical.BRCA-US.tsv",
             {re.compile(".*_age.*"):"int", re.compile(".*_time.*"):"int", re.compile(".*_interval.*"):"int"},
             ["icgc_specimen_id"])
tableFromCSV(dataPath + "BRCA-US.sqlite", "clinicalsample", dataPath + "clinicalsample.BRCA-US.tsv",
             {re.compile(".*_age.*"):"int", re.compile(".*_time.*"):"int", re.compile(".*_interval.*"):"int"},
             ["icgc_sample_id"])
tableFromCSV(dataPath + "BRCA-US.sqlite", "simple_somatic_mutation_open", dataPath + "simple_somatic_mutation.open.BRCA-US.tsv",
             {re.compile("chromosome.*"):"int"},
             ["icgc_mutation_id"])