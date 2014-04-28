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
