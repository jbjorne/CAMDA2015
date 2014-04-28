import os

DATA_PATH = os.path.expanduser("~/data/CAMDA2014-data/ICGC/")
DB_NAME = "ICGC.sqlite"
ICGC_FTP = "data.dcc.icgc.org"
ICGC_VERSION = "version_15.1"

TABLE_FILES = {
    "clinical":"clinical.%c.tsv.gz",
    "clinicalsample":"clinicalsample.%c.tsv.gz",
    "copy_number_somatic_mutation":"copy_number_somatic_mutation.%c.tsv.gz",
    "mirna_expression":"mirna_expression.%c.tsv.gz",
    "protein_expression":"protein_expression.%c.tsv.gz",
    "simple_somatic_mutation_open":"simple_somatic_mutation.open.%c.tsv.gz"
}

TABLE_FORMAT = {
    "clinical":{
        "columns":{".*_age.*":"int", ".*_time.*":"int", ".*_interval.*":"int"},
        "primary_key":["icgc_specimen_id"],
        "foreign_keys":None},
    "clinicalsample":{
        "columns":{".*_age.*":"int", ".*_time.*":"int", ".*_interval.*":"int"},
        "primary_key":["icgc_sample_id"],
        "foreign_keys":{"icgc_specimen_id":"clinical"}},
    "simple_somatic_mutation_open":{
        "columns":{"chromosome.*":"int"},
        "primary_key":["icgc_mutation_id"], 
        "foreign_keys":{"icgc_specimen_id":"clinical"}}
}
