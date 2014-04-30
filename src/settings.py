import os

DATA_PATH = os.path.expanduser("~/data/CAMDA2014-data/ICGC/")
DB_STORAGE = os.path.expanduser("~/data/CAMDA2014-cache/ICGC/")
DB_CACHE = os.path.expanduser("/tmp/CAMDA2014-cache/ICGC/")
DB_NAME = "ICGC.sqlite"
ICGC_FTP = "data.dcc.icgc.org"
ICGC_VERSION = "version_15.1"

TABLE_FILES = {
    "clinical":"clinical.%c.tsv.gz",
    "clinicalsample":"clinicalsample.%c.tsv.gz",
    "copy_number_somatic_mutation":"copy_number_somatic_mutation.%c.tsv.gz",
    #"gene_expression":"gene_expression.%c.tsv.gz",
    "mirna_expression":"mirna_expression.%c.tsv.gz",
    "protein_expression":"protein_expression.%c.tsv.gz",
    "simple_somatic_mutation_open":"simple_somatic_mutation.open.%c.tsv.gz"
}

TABLE_FORMAT = {
    "clinical":{
        "types":{".*_age.*":"int", ".*_time.*":"int", ".*_interval.*":"int"},
        "primary_key":["icgc_specimen_id"],
        "foreign_keys":None},
    "clinicalsample":{
        "types":{".*_age.*":"int", ".*_time.*":"int", ".*_interval.*":"int"},
        "primary_key":["icgc_sample_id"],
        "foreign_keys":{"icgc_specimen_id":"clinical"}},
    "simple_somatic_mutation_open":{
        "types":{"chromosome.*":"int"},
        "primary_key":["icgc_mutation_id"], 
        "foreign_keys":{"icgc_specimen_id":"clinical"}},
    "gene_expression":{
        "types":{
            "analysis_id|gene_chromosome|gene_strand|gene_start|gene_end|normalized_read_count|raw_read_count":"int",
            "normalized_expression_level|fold_change|quality_score|probability":"REAL"},
        "primary_key":["icgc_sample_id","gene_stable_id"], 
        "foreign_keys":{"icgc_specimen_id":"clinical"}}
}
