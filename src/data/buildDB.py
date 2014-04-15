import csv, sqlite3
import os, sys

dataPath = os.path.expanduser("~/data/CAMDA2014/ICGC/Breast_Invasive_Carcinoma-TCGA-US/")

con = sqlite3.connect(":memory:")
cur = con.cursor()
cur.execute("CREATE TABLE t (col1, col2);")

with open(dataPath + 'clinical.BRCA-US.tsv','rb') as fin: # `with` statement available in 2.5+
    # csv.DictReader uses first line in file for column headings by default
    dr = csv.DictReader(fin) # comma is default delimiter
    print dr[0]
    sys.exit()
    to_db = [(i['col1'], i['col2']) for i in dr]

cur.executemany("INSERT INTO t (col1, col2) VALUES (?, ?);", to_db)
con.commit()

