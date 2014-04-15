import csv, sqlite3
import re
import os, sys

dataPath = os.path.expanduser("~/data/CAMDA2014/ICGC/Breast_Invasive_Carcinoma-TCGA-US/")

def defineTable(name, header, columnTypes, defaultType=None):
    columns = []
    for i in range(len(header)):
        if i in columnTypes:
            columns += columnTypes[i]
        elif header[i] in columnTypes:
            columns += header[i] + " " + columnTypes[header[i]]
        else:
            columns += header[i] + " text"
    return "create table " + name + "(" + ", ".join(columns) + ")"

con = sqlite3.connect(":memory:")
data = csv.reader(open(dataPath + "clinical.BRCA-US.tsv"), delimiter='\t')
header = data.next()

defineTable("clinical", header, {re.compile("*age*"):"int"})

for x in data:
    print x
    break
#con.execute("create table person(firstname, lastname)")
#con.executemany("insert into person(firstname, lastname) values (?, ?)", persons)
