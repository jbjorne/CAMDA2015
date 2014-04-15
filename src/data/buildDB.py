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

def defineTable(tableName, columns):
    return "create table " + tableName + "(" + ",".join([x[0] + " " + x[1] for x in columns]) + ")"

def defineInsert(tableName, columns):
    return "insert into " + tableName + "(" + ",".join([x[0] for x in columns]) + ")" + " values (" + ",".join(["?"]*len(columns)) + ")"

def tableFromCSV(dbName, tableName, csvFileName, columnTypes):  
    con = sqlite3.connect(dbName)
    data = csv.reader(open(csvFileName), delimiter='\t')
    header = data.next()
    
    columns = defineColumns(header, columnTypes)
    con.execute("DROP TABLE IF EXISTS " + tableName + ";")
    con.execute(defineTable(tableName, columns))
    insert = defineInsert(tableName, columns)
    #print insert
    con.executemany(insert, data)
    
    con.commit()
    con.close()
    
tableFromCSV(dataPath + "BRCA-US.sqlite", "clinical", dataPath + "clinical.BRCA-US.tsv",
             {re.compile(".*_age.*"):"int", re.compile(".*_time.*"):"int", re.compile(".*_interval.*"):"int"})
tableFromCSV(dataPath + "BRCA-US.sqlite", "clinicalsample", dataPath + "clinicalsample.BRCA-US.tsv",
             {re.compile(".*_age.*"):"int", re.compile(".*_time.*"):"int", re.compile(".*_interval.*"):"int"})