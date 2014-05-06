import os
import hashlib, base64

DATA_PATH = os.path.expanduser("~/data/CAMDA2014-data/ICGC/")
DB_STORAGE = os.path.expanduser("~/data/CAMDA2014-cache/ICGC/")
DB_CACHE = os.path.expanduser("/tmp/CAMDA2014-cache/ICGC/")
DB_NAME = "ICGC.sqlite"
ICGC_FTP = "data.dcc.icgc.org"
ICGC_VERSION = "version_15.1"

# ICGC data files
TABLE_FILES = {
    "clinical":"clinical.%c.tsv.gz",
    "clinicalsample":"clinicalsample.%c.tsv.gz",
    "copy_number_somatic_mutation":"copy_number_somatic_mutation.%c.tsv.gz",
    "gene_expression":"gene_expression.%c.tsv.gz",
    "mirna_expression":"mirna_expression.%c.tsv.gz",
    "protein_expression":"protein_expression.%c.tsv.gz",
    "simple_somatic_mutation_open":"simple_somatic_mutation.open.%c.tsv.gz"
}

# #reCode = re.compile("icgc_.*_id")
# def preprocessICGCCode(cell):
#     return int(cell[2:])

def preprocessMicroRNA(cell):
    # From http://stackoverflow.com/questions/11095408/python-shortest-unique-id-from-strings
    return base64.b64encode(hashlib.md5(cell).digest())

# How ICGC data files are imported to the database
TABLE_FORMAT = {
    "clinical":{
        #"columns":["REVERSE", "digital_image_of_stained_section"],
        "types":{".*_age.*":"int", ".*_time.*":"int", ".*_interval.*":"int"},
        #"preprocess":{"icgc_.*_id":preprocessICGCCode},
        "primary_key":["icgc_specimen_id"],
        "foreign_keys":None},
    "clinicalsample":{
        #"columns":["REVERSE", "submitted_sample_id", "submitted_specimen_id"],
        "types":{".*_age.*":"int", ".*_time.*":"int", ".*_interval.*":"int"},
        #"preprocess":{"icgc_.*_id":preprocessICGCCode},
        "primary_key":["icgc_sample_id"],
        "foreign_keys":{"icgc_specimen_id":"clinical"}},
    "copy_number_somatic_mutation":{
        "columns":["icgc_donor_id","project_code","icgc_specimen_id","icgc_sample_id",
                   "mutation_type","copy_number","segment_mean","segment_median","chromosome",
                   "chromosome_start","chromosome_end","chromosome_start_range",
                   "chromosome_end_range","sequencing_strategy","quality_score","probability",
                   "gene_affected","transcript_affected"],
        "types":{".*_number":"int",".*_mean":"REAL",".*_median":"REAL",".*_start_.*":"int",".*_end_.*":"int","quality_score":"REAL","probability":"REAL"},
        "foreign_keys":{"icgc_specimen_id":"clinical"},
        "indices":["icgc_specimen_id"]},
    "gene_expression":{
        "columns":["icgc_donor_id", "project_code", "icgc_specimen_id", "icgc_sample_id", "gene_stable_id", "normalized_expression_level"],
        "types":{
            "analysis_id|gene_chromosome|gene_strand|gene_start|gene_end|normalized_read_count|raw_read_count":"int",
            "normalized_expression_level|fold_change|quality_score|probability":"REAL"},
        "primary_key":["icgc_sample_id","gene_stable_id"], 
        "foreign_keys":{"icgc_specimen_id":"clinical"},
        "indices":["icgc_specimen_id"]},
    "mirna_expression":{
        "columns":['icgc_donor_id','project_code','icgc_specimen_id','icgc_sample_id',"mirna_seq",
                   'normalized_read_count','raw_read_count','normalized_expression_level',
                   'fold_change','quality_score','probability','chromosome','chromosome_start',
                   'chromosome_end','chromosome_strand','xref_mirbase_id'],
        "types":{".*_count":"int",".*_level":"REAL","fold_change":"int","quality_score":"REAL",
                 "probability":"REAL",".*_start_.*":"int",".*_end_.*":"int"},
        "preprocess":{"mirna_seq":preprocessMicroRNA},
        "foreign_keys":{"icgc_specimen_id":"clinical"},
        "indices":["icgc_specimen_id"]},
    "protein_expression":{
        "columns":['icgc_donor_id','project_code','icgc_specimen_id','icgc_sample_id','antibody_id','gene_name','normalized_expression_level'],
        "types":{"normalized_expression_level":"REAL"},
        "primary_key":["icgc_sample_id","antibody_id"], 
        "foreign_keys":{"icgc_specimen_id":"clinical"},
        "indices":["icgc_specimen_id"]},
    "simple_somatic_mutation_open":{
        "columns":["icgc_mutation_id", "icgc_donor_id", "project_code", "icgc_specimen_id", "icgc_sample_id", "chromosome", "chromosome_start", "chromosome_end", "chromosome_strand", "mutation_type", "mutated_from_allele", "mutated_to_allele", "consequence_type", "aa_mutation", "cds_mutation", "gene_affected", "transcript_affected"],
        "types":{"icgc_.*_id":"int", "chromosome.*":"int"},
        #"preprocess":{"icgc_.*_id":preprocessICGCCode},
        "primary_key":["icgc_mutation_id"], 
        "foreign_keys":{"icgc_specimen_id":"clinical"},
        "indices":["icgc_specimen_id"]},
}

# Common settings used in multiple experiments
META = "{dict(dict(example), label=str(label), features=len(features))}"
EXP = "SELECT ('EXP:'||gene_stable_id),normalized_expression_level FROM gene_expression WHERE icgc_specimen_id={example['icgc_specimen_id']} AND normalized_expression_level != 0"
SSM = "SELECT ('SSM:'||gene_affected),1, ('SSM:'||gene_affected||':'||aa_mutation),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id={example['icgc_specimen_id']};"

# Experiments #################################################################

REMISSION = {
    "project":"BRCA-US",
    "example":"SELECT icgc_donor_id,icgc_specimen_id,disease_status_last_followup,specimen_type FROM clinical WHERE project_code={project} AND specimen_type IS NOT NULL AND specimen_type NOT LIKE '%control%'",
    "label":"{'remission' in example['disease_status_last_followup']}",
    "classIds":{True:1, False:-1},
    "features":[EXP,SSM],
    "hidden":0.3,
    "meta":META
}

CANCER_OR_CONTROL = {
    "project":"BRCA-US",
    "example":"SELECT icgc_donor_id,icgc_specimen_id,disease_status_last_followup,specimen_type FROM clinical WHERE project_code={project} AND specimen_type IS NOT NULL",
    "label":"{'control' not in example['specimen_type']}",
    "classIds":{True:1, False:-1},
    "features":[EXP,SSM],
    "hidden":0.3,
    "meta":META
}