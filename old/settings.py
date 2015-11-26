import os
import hashlib, base64
import math
import inspect
from collections import OrderedDict
#from data.project import Experiment

def logrange(a, b):
    return [math.pow(10,x) for x in range(a, b)]

def preprocessCGIAliasValues(tableName, elem, valueLists):
    primaryName = elem.find("HUGOGeneSymbol").text
    return [[primaryName, primaryName]] + valueLists

DATA_PATH = os.path.expanduser("~/data/CAMDA2015-data-local/")

DB_PATH = os.path.join(DATA_PATH, "database/ICGC-18-150514.sqlite")
ICGC_FTP = "data.dcc.icgc.org"
ICGC_URL = "https://dcc.icgc.org/api/v1/download?fn=/release_18/Projects/"
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
        "preprocess":preprocessCGIAliasValues},
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
    "exp_array":"exp_array.%c.tsv.gz",
    "exp_seq":"exp_seq.%c.tsv.gz",
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
    "exp_array":{
        "columns":["icgc_donor_id", "project_code", "icgc_specimen_id", "gene_id", "normalized_expression_value", "fold_change"],
        "types":{"normalized_expression_level|fold_change":"REAL"},
        "foreign_keys":{"icgc_specimen_id":"clinical"},
        "indices":["icgc_specimen_id"]},
    "exp_seq":{
        "columns":["icgc_donor_id", "project_code", "icgc_specimen_id", "gene_id", "normalized_read_count", "fold_change"],
        "types":{"normalized_read_count|fold_change":"REAL"},
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
EXP_ARRAY = "SELECT ('EXP_ARRAY:'||gene_id),CAST(normalized_expression_value as decimal) FROM exp_array WHERE icgc_specimen_id={example['icgc_specimen_id']} AND normalized_expression_value != 0"
EXP_SEQ = "SELECT ('EXP_SEQ:'||gene_id),100000*normalized_read_count FROM exp_seq WHERE icgc_specimen_id={example['icgc_specimen_id']} AND normalized_read_count != 0"
PEXP = "SELECT ('PEXP:'||antibody_id||':'||gene_name),normalized_expression_level FROM protein_expression WHERE icgc_specimen_id={example['icgc_specimen_id']} AND normalized_expression_level != 0"
MIRNA = "SELECT ('MIRNA:'||mirna_seq),log(normalized_expression_level+1) FROM mirna_expression WHERE icgc_specimen_id={example['icgc_specimen_id']}"
SSM = "SELECT ('SSM:'||gene_affected),1, ('SSM:'||gene_affected||':'||aa_mutation),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id={example['icgc_specimen_id']}"
#CNSM = "SELECT ('CNSM:'||gene_affected||':'||chromosome||':'||chromosome_start||':'||chromosome_end||':'||mutation_type),1 FROM copy_number_somatic_mutation WHERE icgc_specimen_id={example['icgc_specimen_id']}"
CNSM = "SELECT ('CNSM:'||gene_affected),copy_number FROM copy_number_somatic_mutation WHERE icgc_specimen_id={example['icgc_specimen_id']} AND copy_number != ''"
MAIN_FEATURES = [EXP,PEXP,MIRNA,SSM]#,CNSM]
ALL_FEATURES = [EXP,PEXP,MIRNA,SSM,CNSM]

PROJECT_CODE = "SELECT ('code:'||project_code),1 FROM clinical WHERE icgc_specimen_id={example['icgc_specimen_id']} AND length(project_code) > 0"

EXP_SEQ_CUTOFF = "SELECT ('EXP_SEQ:'||gene_id),100000*normalized_read_count FROM gene_expression WHERE icgc_specimen_id={example['icgc_specimen_id']} AND abs(normalized_read_count) > 0.005"

EXP_FILTER = "SELECT * FROM gene_expression WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1" # Require EXP
EXP_ARRAY_FILTER = "SELECT * FROM exp_array WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1" # Require EXP
EXP_SEQ_FILTER = "SELECT * FROM exp_seq WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1" # Require EXP
PEXP_FILTER = "SELECT * FROM protein_expression WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1" # Require EXP
SSM_FILTER = "SELECT * FROM simple_somatic_mutation_open WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1" # Require SSM
CNSM_FILTER = "SELECT * FROM copy_number_somatic_mutation WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1" # Require SSM
MIRNA_FILTER = "SELECT * FROM mirna_expression WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1" # Require SSM


#def require(table):
#    return "SELECT * FROM " + table + " WHERE icgc_specimen_id={example['icgc_specimen_id']} LIMIT 1"


SSM_GENE_ONLY = "SELECT ('SSM:'||gene_affected),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id={example['icgc_specimen_id']}"
#SSM_GENE_CONSEQUENCE = "SELECT ('SSM:'||gene_affected),1, ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id={example['icgc_specimen_id']}"
SSM_GENE_AA = "SELECT ('SSM:'||gene_affected),1, ('SSM:'||gene_affected||':'||aa_mutation),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id={example['icgc_specimen_id']}"
SSM_GENE_CONSEQUENCE = "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id={example['icgc_specimen_id']}"

SSM_ID = "SELECT ('SSM:'||icgc_mutation_id),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id={example['icgc_specimen_id']}"

def makeAll(template):
    templateAll = dict(template)
    del templateAll["project"]
    templateAll["example"] = templateAll["example"].replace("project_code IN {'project'} AND", "")
    return templateAll

# Experiments #################################################################

gradeMap = {"g1":1, "g2":2, "g3":3, 
            "G1":1, "G2":2, "G3":3, "G4":4,
            "G1 to G3":2, "G2 and G3":3,
            "FL grade I":1, "FL grade II":2, "FL grade III":3, "FL grade IIIa":3, "FL grade IIIb":3,
            
            "1":1, "2":2, "3":3, "4":4,
            "1 - Well differentiated":1, "2 - Moderately differentiated":2, "3 - Poorly differentiated":3,
            "3+3":3, "3+4":4, "4+3":4,
            "4 - Undifferentiated":4,
            "Grade 1":1, "Grade 2":2, "Grade 3":3,
            "I":1, "II":2, "III":3, "I-III":2, "I-II":2, "II-I":2, "II-III":3,
            "IV":4, "NET-G1":1, "NET-G2":2, "NET-G3":3,
            "T1a":1, "T1b":1, "T2a":2, "T2b":2, "T3":3,
            "Undifferentiated":4,
            "moderate":2, "poor":3, "well":1,
            
            
}
def getGrade(stage):
    global gradeMap
    assert stage in gradeMap
    numGrade = gradeMap[stage]
    if numGrade < 3:
        return -1
    else:
        return 1

def getStage(stage):
    if "T1" in stage:
        return 1
    elif "T2" in stage:
        return 1
    elif "T3" in stage:
        return -1
    elif "T4" in stage:
        return -1

STAGE = {
    "project":"KIRC-US",
    "example":"""
        SELECT icgc_donor_id,icgc_specimen_id,project_code,tumour_stage,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup 
        FROM clinical
        WHERE project_code IN {'project'} AND 
        length(tumour_stage) > 0 AND
        specimen_type NOT LIKE '%Normal%' AND
        (tumour_stage LIKE '%T1%' OR tumour_stage LIKE '%T2%' OR
        tumour_stage LIKE '%T3%' OR tumour_stage LIKE '%T4%')
    """,
    "label":"{settings.getStage(example['tumour_stage'])}",
    "features":[SSM_GENE_ONLY],
    "filter":SSM_FILTER,
    "hidden":0.3,
    "meta":META
}
STAGE_ALL = makeAll(STAGE)

GRADE = {
    "project":"KIRC-US",
    "example":"""
        SELECT icgc_donor_id,icgc_specimen_id,project_code,tumour_grade,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup 
        FROM clinical
        WHERE project_code IN {'project'} AND 
        length(tumour_grade) > 0 AND
        specimen_type NOT LIKE '%blood%' AND
        specimen_type NOT LIKE '%Normal%' AND
        tumour_grade != 'NA' AND tumour_grade != 'TNM' AND tumour_grade != 'X - Cannot be assessed' AND
        tumour_grade != 'x' AND tumour_grade NOT LIKE '%DLBCL%'
    """,
    "label":"{settings.getGrade(example['tumour_grade'])}",
    "features":[SSM_GENE_ONLY],
    "filter":SSM_FILTER,
    "hidden":0.3,
    "meta":META
}
GRADE_ALL = makeAll(GRADE)

SURVIVAL = {
    "project":"KIRC-US",
    "example":"""
        SELECT icgc_donor_id,icgc_specimen_id,project_code,tumour_grade,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup, 
        donor_age_at_last_followup, donor_age_at_diagnosis, 
        cast(donor_age_at_last_followup as int) - cast(donor_age_at_diagnosis as int) as delta
        FROM clinical
        WHERE project_code IN {'project'} AND
        length(donor_age_at_diagnosis) > 0 AND 
        length(donor_age_at_last_followup) > 0 AND 
        length(donor_vital_status) > 0 AND
        ((delta >= 5 and donor_vital_status='alive') OR
        (delta >= 0 and delta < 5 and donor_vital_status='deceased')) AND
        specimen_type NOT LIKE '%Normal%'
    """,
    "label":"{'alive' in example['donor_vital_status']}",
    "classes":{'True':1, 'False':-1},
    "features":[SSM_GENE_CONSEQUENCE],
    "filter":SSM_FILTER,
    "hidden":0.3,
    "meta":META
}
SURVIVAL_ALL = makeAll(SURVIVAL)

REMISSION_MUT = {
    "project":"KIRC-US",
    "example":"""
        SELECT icgc_donor_id,icgc_specimen_id,project_code,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup 
        FROM clinical
        WHERE project_code IN {'project'} AND 
        length(specimen_type) > 0 AND 
        length(disease_status_last_followup) > 0 AND
        ((disease_status_last_followup LIKE '%remission%') OR
        (donor_vital_status IS 'deceased')) AND
        specimen_type NOT LIKE '%Normal%'
    """,
    "label":"{'remission' in example['disease_status_last_followup']}",
    "classes":{'True':1, 'False':-1},
    "features":[SSM_GENE_CONSEQUENCE],
    "filter":SSM_FILTER,
    "hidden":0.3,
    "meta":META
}
REMISSION_MUT_ALL = makeAll(REMISSION_MUT)

# def RemissionMutTest(Experiment):
#     def __init__(self):
#         self.project = "KIRC-US"
#         self.exampleTable = "clinical"
#         self.exampleFields = "icgc_donor_id,icgc_specimen_id,project_code,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup"
#         self.exampleWhere = """
#             length(specimen_type) > 0 AND 
#             length(disease_status_last_followup) > 0 AND
#             ((disease_status_last_followup LIKE '%remission%') OR
#             (donor_vital_status IS 'deceased')) AND
#             specimen_type NOT LIKE '%Normal%'
#             """
#         self.featureGroups = [SSM_GENE_CONSEQUENCE]
#         self.filter = "SELECT * FROM simple_somatic_mutation_open WHERE icgc_specimen_id=? LIMIT 1"


REMISSION = {
    "project":"KIRC-US",
    "example":"""
        SELECT icgc_donor_id,icgc_specimen_id,project_code,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup 
        FROM clinical
        WHERE project_code IN {'project'} AND 
        length(specimen_type) > 0 AND 
        length(disease_status_last_followup) > 0 AND
        ((disease_status_last_followup LIKE '%remission%') OR
        (donor_vital_status IS 'deceased')) AND
        specimen_type NOT LIKE '%Normal%'
    """,
    "label":"{'remission' in example['disease_status_last_followup']}",
    "classes":{'True':1, 'False':-1},
    "features":[EXP_SEQ],
    "filter":EXP_SEQ_FILTER,
    "hidden":0.3,
    "meta":META
}

REGRESSION = {
    "project":"KIRC-US",
    "example":"""
        SELECT icgc_donor_id,icgc_specimen_id,project_code,donor_survival_time,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup 
        FROM clinical
        WHERE project_code IN {'project'} AND
        donor_vital_status IS 'deceased' AND
        donor_survival_time != '' AND
        length(specimen_type) > 0 AND 
        specimen_type LIKE '%umour%'
    """,
    "label":"{example['donor_survival_time']}",
    "features":[EXP_SEQ],
    "filter":EXP_SEQ_FILTER,
    "hidden":0.3,
    "meta":META
}

REGRESSION_ALL = dict(REGRESSION)
del REGRESSION_ALL["project"]
REGRESSION_ALL["example"] = REGRESSION_ALL["example"].replace("project_code IN {'project'} AND", "")

REMISSION_ALL = dict(REMISSION)
del REMISSION_ALL["project"]
REMISSION_ALL["example"] = REMISSION_ALL["example"].replace("project_code IN {'project'} AND", "")
#REMISSION_ALL["sample"] = {"1":0.1, "-1":0.1}

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
#     "example":"""
#         SELECT project_code,icgc_donor_id,icgc_specimen_id,donor_vital_status,disease_status_last_followup,specimen_type 
#         FROM clinical WHERE
#         project_code IN {'project'} AND
#         length(specimen_type) > 0 AND
#         specimen_type LIKE '%primary%'
#     """,
    "example":"""
        SELECT project_code,icgc_donor_id,icgc_specimen_id,donor_vital_status,disease_status_last_followup,specimen_type 
        FROM clinical WHERE
        project_code IN {'project'} AND
        length(specimen_type) > 0
    """,
    "label":"{'umour' in example['specimen_type']}",
    "classes":{'True':1, 'False':-1},
    #"label":"{example['specimen_type']}",
    #"classes":{},
    "features":[SSM_GENE_AA],
    "filter":SSM_FILTER, #CONTROL_EXP_FILTER,
    "hidden":0.3,
    "meta":META
}

CANCER_OR_CONTROL_ALL = dict(CANCER_OR_CONTROL)
del CANCER_OR_CONTROL_ALL["project"]
CANCER_OR_CONTROL_ALL["example"] = CANCER_OR_CONTROL_ALL["example"].replace("project_code IN {'project'} AND", "")
#CANCER_OR_CONTROL_ALL["sample"] = {"1":0.05, "-1":0.5}
#CANCER_OR_CONTROL_ALL["sample"] = {"1":0.1}
#CANCER_OR_CONTROL_ALL["sample"] = {"1":0.075, "-1":0.75}

# SURVIVAL = {
#     "project":"KIRC-US",
#     "example":"""
#         SELECT donor_age_at_diagnosis,donor_vital_status,icgc_donor_id,donor_survival_time,icgc_specimen_id,disease_status_last_followup,specimen_type 
#         FROM clinical 
#         WHERE project_code IN {'project'} AND 
#             length(specimen_type) > 0 AND 
#             specimen_type NOT LIKE '%control%' AND 
#             ((length(donor_survival_time) > 0 AND donor_vital_status IS 'deceased') OR disease_status_last_followup LIKE '%remission%')
#     """,
#     "label":"{0 if 'remission' in example['disease_status_last_followup'] else 1.0/(int(example['donor_survival_time'])+1)}",
#     "features":[EXP,SSM],
#     "hidden":0.3,
#     "meta":META
# }