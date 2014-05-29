import os
import hashlib, base64
import math
import inspect
import gene.buildCancerGeneIndexDB
from collections import OrderedDict

def logrange(a, b):
    return [math.pow(10,x) for x in range(a, b)]

DATA_PATH = os.path.expanduser("~/data/CAMDA2014-data-local/")

DB_PATH = os.path.join(DATA_PATH, "ICGC/ICGC.sqlite")
ICGC_FTP = "data.dcc.icgc.org"
ICGC_VERSION = "version_15.1"

CGI_DOWNLOAD_PATH = os.path.join(DATA_PATH, "NCI-CancerGeneIndex")
CGI_DB_PATH = os.path.join(DATA_PATH, "NCI-CancerGeneIndex/NCI-CGI.sqlite")
CGI_GENE_DISEASE_FILE = "https://ncisvn.nci.nih.gov/svn/files/trunk/cancergeneindex/cancergeneindex/CancerGeneIndex/NCI_CancerIndex_allphases_disease.zip"
CGI_GENE_COMPOUND_FILE = "https://ncisvn.nci.nih.gov/svn/files/trunk/cancergeneindex/cancergeneindex/CancerGeneIndex/NCI_CancerIndex_allphases_compound.zip"

CGI_TABLES = {
    "gene_entry":{
        "columns":OrderedDict([
                    ("HUGOGeneSymbol", "hugo_gene_symbol"), 
                    ("SequenceIdentificationCollection/HgncID", "hgnc_id"), 
                    ("SequenceIdentificationCollection/LocusLinkID", "locus_link_id"), 
                    ("SequenceIdentificationCollection/GenbankAccession", "genbank_accession"), 
                    ("SequenceIdentificationCollection/RefSeqID", "refseq_id"), 
                    ("SequenceIdentificationCollection/UniProtID", "uniprot_id"), 
                    ("GeneStatusFlag", "gene_status_flag")]),
        "primary_key":["hugo_gene_symbol"]},
    "gene_alias":{
        "elements":"GeneAliasCollection/GeneAlias",
        "columns":OrderedDict([
            ("../HUGOGeneSymbol", "hugo_gene_symbol"),           
            ("GeneAliasCollection/GeneAlias", "alias")]),
        "primary_key":["hugo_gene_symbol", "alias"],
        "indices":["alias"],
        "preprocess":gene.buildCancerGeneIndexDB.preprocessAliasValues},
    "sentence":{
        "elements":"Sentence",
        "columns":OrderedDict([
            ("../HUGOGeneSymbol", "hugo_gene_symbol"),           
            ("Sentence/GeneData/MatchedGeneTerm", "matched_gene_term"),
            ("Sentence/GeneData/NCIGeneConceptCode", "nci_gene_concept_code"),
            ("Sentence/DiseaseData/MatchedDiseaseTerm", "matched_disease_term"),
            ("Sentence/DiseaseData/NCIDiseaseConceptCode", "nci_disease_concept_code"),
            ("Sentence/DrugData/DrugTerm", "drug_term"),
            ("Sentence/DrugData/NCIDrugConceptCode", "nci_drug_concept_code"),
            ("Sentence/Statement", "statement"),
            ("Sentence/PubMedID", "pubmed_id"),
            ("Sentence/Organism", "organism"),
            ("Sentence/NegationIndicator", "negation_indicator"),
            ("Sentence/CellineIndicator", "celline_indicator"),
            ("Sentence/Comments", "comments"),
            ("Sentence/EvidenceCode", "evidence_code"),
            ("Sentence/Roles/PrimaryNCIRoleCode", "primary_nci_role_code"),
            ("Sentence/Roles/OtherRole", "other_roles"),
            ("Sentence/SentenceStatusFlag", "sentence_status_flag"),
            ]),
        "indices":["hugo_gene_symbol"]}
}

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

def testFunction(value, con):
    print value#, inspect.stack()[0][3]
    print [x["file"] for x in con.execute("PRAGMA database_list;")][0]
    return True
SQLITE_FUNCTIONS = [testFunction]

# How ICGC data files are imported to the database
TABLE_FORMAT = {
    "clinical":{
        #"columns":["REVERSE", "digital_image_of_stained_section"],
        "types":{".*_age.*":"int", ".*_time":"int", ".*_interval.*":"int"},
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
        "columns":["icgc_donor_id", "project_code", "icgc_specimen_id", "gene_stable_id", "normalized_expression_level"],
        "types":{
            "analysis_id|gene_chromosome|gene_strand|gene_start|gene_end|normalized_read_count|raw_read_count":"int",
            "normalized_expression_level|fold_change|quality_score|probability":"REAL"},
        #"primary_key":["icgc_sample_id","gene_stable_id"], 
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
        #"primary_key":["icgc_sample_id","antibody_id"], 
        "foreign_keys":{"icgc_specimen_id":"clinical"},
        "indices":["icgc_specimen_id"]},
    "simple_somatic_mutation_open":{
        "columns":["icgc_mutation_id", "icgc_donor_id", "project_code", "icgc_specimen_id", "icgc_sample_id", "chromosome", "chromosome_start", "chromosome_end", "chromosome_strand", "mutation_type", "mutated_from_allele", "mutated_to_allele", "consequence_type", "aa_mutation", "cds_mutation", "gene_affected", "transcript_affected"],
        "types":{"icgc_.*_id":"int", "chromosome.*":"int"},
        #"preprocess":{"icgc_.*_id":preprocessICGCCode},
        #"primary_key":["icgc_mutation_id"], 
        "foreign_keys":{"icgc_specimen_id":"clinical"},
        "indices":["icgc_specimen_id"]},
}

TABLE_FORMAT["cosmic_gene_census"] = { 
    "primary_key":["Symbol"],
    "file":os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'COSMIC-cancer_gene_census-140510.tsv'))
}


# Common settings used in multiple experiments
CAMDA_PROJECTS = "HNSC-US','LUAD-US','KIRC-US"
META = "{dict(dict(example), label=str(label), features=len(features))}"
EXP = "SELECT ('EXP:'||gene_stable_id),100000*normalized_expression_level FROM gene_expression WHERE icgc_specimen_id={example['icgc_specimen_id']} AND normalized_expression_level != 0"
PEXP = "SELECT ('PEXP:'||antibody_id||':'||gene_name),normalized_expression_level FROM protein_expression WHERE icgc_specimen_id={example['icgc_specimen_id']} AND normalized_expression_level != 0"
MIRNA = "SELECT ('MIRNA:'||mirna_seq),log(normalized_expression_level+1) FROM mirna_expression WHERE icgc_specimen_id={example['icgc_specimen_id']}"
SSM = "SELECT ('SSM:'||gene_affected),1, ('SSM:'||gene_affected||':'||aa_mutation),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id={example['icgc_specimen_id']}"
CNSM = "SELECT ('CNSM:'||gene_affected||':'||chromosome||':'||chromosome_start||':'||chromosome_end||':'||mutation_type),1 FROM copy_number_somatic_mutation WHERE icgc_specimen_id={example['icgc_specimen_id']}"
MAIN_FEATURES = [EXP,PEXP,MIRNA,SSM]#,CNSM]
ALL_FEATURES = [EXP,PEXP,MIRNA,SSM,CNSM]

EXP_CUTOFF = "SELECT ('EXP:'||gene_stable_id),100000*normalized_expression_level FROM gene_expression WHERE icgc_specimen_id={example['icgc_specimen_id']} AND abs(normalized_expression_level) > 0.005"

EXP_FILTER = "SELECT * FROM gene_expression WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1" # Require EXP
PEXP_FILTER = "SELECT * FROM protein_expression WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1" # Require EXP
SSM_FILTER = "SELECT * FROM simple_somatic_mutation_open WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1" # Require SSM
CNSM_FILTER = "SELECT * FROM copy_number_somatic_mutation WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1" # Require SSM
MIRNA_FILTER = "SELECT * FROM mirna_expression WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1" # Require SSM
#def require(table):
#    return "SELECT * FROM " + table + " WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1"

# Experiments #################################################################

REMISSION = {
    "project":"KIRC-US",
    "example":"""
        SELECT icgc_donor_id,icgc_specimen_id,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup 
        FROM clinical
        WHERE project_code IN {'project'} AND 
        length(specimen_type) > 0 AND 
        length(disease_status_last_followup) > 0 AND
        ((disease_status_last_followup LIKE '%remission%') OR
        (donor_vital_status IS 'deceased')) AND
        specimen_type NOT LIKE '%control%'
    """,
    "label":"{'remission' in example['disease_status_last_followup']}",
    "classes":{'True':1, 'False':-1},
    "features":[EXP],
    "filter":EXP_FILTER,
    "hidden":0.3,
    "meta":META
}

REMISSION_ALL = dict(REMISSION)
del REMISSION_ALL["project"]
REMISSION_ALL["example"] = REMISSION_ALL["example"].replace("project_code IN {'project'} AND", "")
REMISSION_ALL["sample"] = {"1":0.1, "-1":0.1}

TUMOUR_STAGE_AT_DIAGNOSIS = {
    "project":"NBL-US",
    "example":"""
        SELECT icgc_donor_id,donor_tumour_stage_at_diagnosis,icgc_specimen_id,disease_status_last_followup,specimen_type 
        FROM clinical 
        WHERE project_code IN {'project'} AND 
        length(specimen_type) > 0 AND 
        specimen_type NOT LIKE '%control%' AND
        length(donor_tumour_stage_at_diagnosis)>0
    """,
    "label":"{example['donor_tumour_stage_at_diagnosis']}",
    "classes":{},
    "features":[EXP,SSM],
    "hidden":0.3,
    "meta":META
}

CONTROL_EXP_FILTER = """
    SELECT * FROM gene_expression
    WHERE
        icgc_specimen_id = {example['icgc_specimen_id']} AND
        CASE WHEN {example['specimen_type']} LIKE '%control%'
        THEN
            icgc_specimen_id IN 
            (
                SELECT icgc_specimen_id FROM clinical WHERE 
                    icgc_donor_id = {example['icgc_donor_id']} AND
                    specimen_type LIKE '%control%' AND
                    specimen_type LIKE '%primary%'
            )
        ELSE 
            {example['icgc_donor_id']} NOT IN
            (
                SELECT control_specimens.icgc_donor_id FROM
                    (SELECT icgc_donor_id, icgc_specimen_id FROM clinical 
                        WHERE 
                        icgc_donor_id = {example['icgc_donor_id']} AND
                        specimen_type LIKE '%control%' AND
                        specimen_type LIKE '%primary%'
                    ) AS control_specimens
                JOIN gene_expression
                ON gene_expression.icgc_specimen_id = control_specimens.icgc_specimen_id
                LIMIT 1
            )
        END
    LIMIT 1
"""
    
    #(project_code IN {'project'} OR specimen_type LIKE '%control%') AND 
#        project_code='KIRC-US' AND
CANCER_OR_CONTROL = {
    "project":"KIRC-US",
    "example":"""
        SELECT project_code,icgc_donor_id,icgc_specimen_id,donor_vital_status,disease_status_last_followup,specimen_type 
        FROM clinical WHERE
        project_code IN {'project'} AND
        length(specimen_type) > 0 AND
        specimen_type LIKE '%primary%'
    """,
    "label":"{'control' not in example['specimen_type']}",
    "classes":{'True':1, 'False':-1},
    #"label":"{example['specimen_type']}",
    #"classes":{},
    "features":[EXP],
    "filter":CONTROL_EXP_FILTER,
    "hidden":0.3,
    "meta":META
}

CANCER_OR_CONTROL_ALL = dict(CANCER_OR_CONTROL)
del CANCER_OR_CONTROL_ALL["project"]
CANCER_OR_CONTROL_ALL["example"] = CANCER_OR_CONTROL_ALL["example"].replace("project_code IN {'project'} AND", "")
#CANCER_OR_CONTROL_ALL["sample"] = {"1":0.05, "-1":0.5}
#CANCER_OR_CONTROL_ALL["sample"] = {"1":0.1}
CANCER_OR_CONTROL_ALL["sample"] = {"1":0.075, "-1":0.75}

SURVIVAL = {
    "project":"KIRC-US",
    "example":"""
        SELECT donor_age_at_diagnosis,donor_vital_status,icgc_donor_id,donor_survival_time,icgc_specimen_id,disease_status_last_followup,specimen_type 
        FROM clinical 
        WHERE project_code IN {'project'} AND 
            length(specimen_type) > 0 AND 
            specimen_type NOT LIKE '%control%' AND 
            ((length(donor_survival_time) > 0 AND donor_vital_status IS 'deceased') OR disease_status_last_followup LIKE '%remission%')
    """,
    "label":"{0 if 'remission' in example['disease_status_last_followup'] else 1.0/(int(example['donor_survival_time'])+1)}",
    "features":[EXP,SSM],
    "hidden":0.3,
    "meta":META
}