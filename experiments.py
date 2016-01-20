from learn.Experiment import Experiment
from learn.FeatureGroup import FeatureGroup
from itertools import combinations
from collections import OrderedDict
from learn.analyse.mapping import ensemblToName

###############################################################################
# Features
###############################################################################

#SSM_GENE_CONSEQUENCE = "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"
#SSM_GENE_POS = "SELECT ('SSM:'||gene_affected||':'||consequence_type||':'||chromosome||':'||chromosome_start||':'||chromosome_end),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"

class Age(FeatureGroup):
    def __init__(self):
        super(Age, self).__init__("AGE", None)
    def buildFeatures(self, row):
        if row["donor_age_at_diagnosis"] != None:
            return ["AGE"], [int(row["donor_age_at_diagnosis"])]
        else:
            return [], []

class ExpSeq(FeatureGroup):
    def __init__(self): #, cutoff=0.0005):
        super(ExpSeq, self).__init__("EXP_SEQ", "SELECT gene_id,1000000*normalized_read_count as count FROM exp_seq WHERE icgc_specimen_id=?")
        #super(ExpressionSeq, self).__init__("EXP_SEQ", "SELECT gene_id,100000*normalized_read_count as count FROM exp_seq WHERE abs(normalized_read_count) > %f AND icgc_specimen_id=?" % cutoff)
    def buildFeatures(self, row):
        return[(row["gene_id"],)], [row["count"]]

class ExpArray(FeatureGroup):
    def __init__(self):
        super(ExpArray, self).__init__("EXP_ARR", "SELECT gene_id,normalized_expression_value FROM exp_array WHERE icgc_specimen_id=?")
    def buildFeatures(self, row):
        return[(row["gene_id"],)], [row["normalized_expression_value"]]

class SSMClusterBase(FeatureGroup):
    def __init__(self):
        super(SSMClusterBase, self).__init__("SSM", "SELECT KEYS FROM ssm WHERE icgc_specimen_id=?", ["consequence_type", "chromosome", "chromosome_start"])   

class SSMClusterSimple(SSMClusterBase):
    def __init__(self):
        super(SSMClusterSimple, self).__init__()   
    def buildFeatures(self, row):
        return [(row["chromosome"], row["chromosome_start"] / 10000, row["consequence_type"])], None

class SSMCluster(SSMClusterBase):
    def __init__(self):
        super(SSMCluster, self).__init__()
        self.steps = [10,1000,10000]
        #self.halfStep = self.step / 2
    def buildFeatures(self, row):
        features = []
        for step in self.steps:
            features.append((row["chromosome"], row["chromosome_start"] / step, row["consequence_type"]))
        return features, None
    
    #     ---------------------- Best scores on development set --------------------------
    #     [ 0.51881322  0.47312086  0.39220871  0.25795435  0.47840649  0.75779902
    #       0.80282313  0.76598522  0.84503739  0.54922784]
    #     0.584 (+/-0.094) for {'n_estimators': 10, 'random_state': 1}
    #def buildFeatures(self, row):
    #    return [("S0", row["chromosome"], row["chromosome_start"] / self.step, row["consequence_type"]),
    #            ("S1", row["chromosome"], (row["chromosome_start"] + self.halfStep) / self.step, row["consequence_type"])]


class SSMClusterPair(SSMClusterBase):
    def __init__(self):
        super(SSMClusterPair, self).__init__()
        self.step = 100
        self.halfStep = self.step / 2
    def buildFeatures(self, row):
        return [("S0", row["chromosome"], row["chromosome_start"] / self.step),
                ("S1", row["chromosome"], (row["chromosome_start"] + self.halfStep) / self.step)], None
#         return [("S0", row["chromosome"], row["chromosome_start"] / self.step, row["consequence_type"]),
#                 ("S1", row["chromosome"], (row["chromosome_start"] + self.halfStep) / self.step, row["consequence_type"])], None

# for KIRC-US SSM_GENE_CONSEQUENCE_V20,SSM_TEST,SSM_CHROMOSOME,SSM_CONSEQUENCE,SSMAminoAcid
class SSMAminoAcid(FeatureGroup):
    def __init__(self):
        super(SSMAminoAcid, self).__init__("SSM", "SELECT KEYS FROM ssm WHERE icgc_specimen_id=?", ["aa_mutation"], required=False)
    def buildFeatures(self, row):
        return [("AA", ''.join([x for x in (row["aa_mutation"] if row["aa_mutation"] else "-") if not x.isdigit()]))], None

class Mutation(FeatureGroup):
    def __init__(self):
        super(Mutation, self).__init__("MUT")
    def processExample(self, connection, example, exampleFeatures, featureIds, meta):
        ssm = [x for x in connection.execute("SELECT DISTINCT gene_affected FROM ssm WHERE icgc_specimen_id=?", (example['icgc_specimen_id'],))]
        if len(ssm) == 0: return False
        exp = [x for x in connection.execute("SELECT gene_id,1000000*normalized_read_count as count FROM exp_seq WHERE icgc_specimen_id=?", (example['icgc_specimen_id'],))]
        if len(exp) == 0: return False
        #mutated = set([x for x in [ensemblToName(row["gene_affected"]) for row in ssm] if x != None])
        mutated = [row["gene_affected"] for row in ssm]
        mutated = set(mutated + [x for x in [ensemblToName(gene) for gene in mutated] if x != None])
        #print mutated
        features, values = [], []
        for row in exp:
            if row["gene_id"] in mutated:
                features.append(row["gene_id"])
                values.append(row["count"])
        self._addFeatures(features, values, exampleFeatures, featureIds, meta)
        return True

class FeatureCount(FeatureGroup):
    def __init__(self, name, table, key):
        super(FeatureCount, self).__init__(name, "SELECT * FROM " + table + " WHERE icgc_specimen_id=?")
        self.key = key
    def processExample(self, connection, example, exampleFeatures, featureIds, meta):
        counts = OrderedDict()
        numTotal = numUnique = 0
        for row in connection.execute(self.query, (example['icgc_specimen_id'], )):
            value = row[self.key]
            if value not in counts:
                counts[value] = 0
                numUnique += 1
            counts[value] += 1
            numTotal += 1
        if numTotal == 0:
            return False
        keys = counts.keys()
        features = [(self.name, key) for key in keys] + [(self.name, "NUM_TOTAL"), (self.name, "NUM_GENES")]
        values = [counts[key] for key in keys] + [numTotal, numUnique]
        #print features, values
        self._addFeatures(features, values, exampleFeatures, featureIds, meta)
        return True

MUTATION_COUNT = FeatureCount("N_MUT", "ssm", "gene_affected")
CONSEQUENCE_COUNT = FeatureCount("N_MUT", "ssm", "consequence_type")

class GenePair(FeatureGroup):
    def __init__(self):
        super(GenePair, self).__init__("SSM", "SELECT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["gene_affected"])   
    
    def buildRows(self, rows):
        features = []
        for row1, row2 in combinations(rows, 2):
            features.append([row1["gene_affected"]])
            features.append([row2["gene_affected"]])
            features.append([row1["gene_affected"], row2["gene_affected"]])
        return features

SSM_CONSEQUENCE = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM ssm WHERE icgc_specimen_id=?", ["consequence_type"])
SSM_GENE = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM ssm WHERE icgc_specimen_id=?", ["gene_affected"])
SSM_CHROMOSOME = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM ssm WHERE icgc_specimen_id=?", ["chromosome"])
#SSM_GENE_PROJECT = FeatureGroup("SSM", "SELECT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["gene_affected", "project_code"])
SSM_PROJECT = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["project_code"])
SSM_TRANSCRIPT_V18 = FeatureGroup("SSM", "SELECT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["transcript_affected"])
SSM_TRANSCRIPT = FeatureGroup("SSM", "SELECT KEYS FROM ssm WHERE icgc_specimen_id=?", ["transcript_affected"])
SSM_GENE_CONSEQUENCE_V18 = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["gene_affected", "consequence_type"])
SSM_GENE_CONSEQUENCE = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM ssm WHERE icgc_specimen_id=?", ["gene_affected", "consequence_type"])
#SSM_GENE_CONSEQUENCE_V20_FILTER = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM ssm WHERE icgc_specimen_id=?", ["gene_affected", "consequence_type"], dummy=True)
SSM_CHROMOSOME_CONSEQUENCE_V18 = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["chromosome", "consequence_type"])
SSM_CHROMOSOME_CONSEQUENCE = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM ssm WHERE icgc_specimen_id=?", ["chromosome", "consequence_type"])
SSM_GENE_POS = FeatureGroup("SSM", "SELECT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["gene_affected", "consequence_type", "chromosome", "chromosome_start", "chromosome_end"])

#SSM_ALLELE = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM ssm WHERE icgc_specimen_id=?", ["mutated_from_allele"])
SSM_TEST = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM ssm WHERE icgc_specimen_id=?", ["transcript_affected", "consequence_type"])

SSM_GENE_LIMITED = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM ssm WHERE consequence_type == 'exon_variant' AND icgc_specimen_id=?", ["gene_affected"])

CNSM_MUTATION_TYPE = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM copy_number_somatic_mutation WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["mutation_type"])
CNSM_CHROMOSOME = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM copy_number_somatic_mutation WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["chromosome", "mutation_type"])
CNSM_CHROMOSOME_COUNT = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM copy_number_somatic_mutation WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["chromosome", "mutation_type", "copy_number"])
CNSM_GENE = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM copy_number_somatic_mutation WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["gene_affected", "copy_number"])

CNSM_GENE_V20 = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM cnsm WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["gene_affected", "copy_number"])
CNSM_NUMBER_V20 = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM cnsm WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["gene_affected"], "copy_number")
CNSM_TYPE_V20 = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM cnsm WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["gene_affected", "mutation_type", "copy_number"])
CNSM_TYPE2_V20 = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM cnsm WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["gene_affected", "mutation_type"], "copy_number")
CNSM_CHROMOSOME_COUNT_V20 = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM cnsm WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["chromosome", "mutation_type", "copy_number"])
#CNSM_CHROMOSOME_COUNT_V20_FILTER = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM cnsm WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["chromosome", "mutation_type", "copy_number"], dummy=True)
PROJECT = FeatureGroup("PROJECT", None, ["project_code"])
AGE = Age()

MIRNA = FeatureGroup("MIRNA", "SELECT DISTINCT KEYS FROM mirna_seq WHERE icgc_specimen_id=?", ["normalized_read_count", "chromosome"])

###############################################################################
# Experiments
###############################################################################

class Survival(Experiment):
    def __init__(self, days=5*365, maxAge=60):
        super(Survival, self).__init__()
        self.days = days
        self.query = """
            SELECT specimen.icgc_donor_id,specimen.icgc_specimen_id,
            specimen.project_code,specimen_type,donor_vital_status,
            disease_status_last_followup,donor_age_at_diagnosis,
            CAST(IFNULL(donor_survival_time, 0) as int) as time_survival,
            CAST(IFNULL(donor_interval_of_last_followup, 0) as int) as time_followup
            FROM donor INNER JOIN specimen
            ON specimen.icgc_donor_id = donor.icgc_donor_id 
            WHERE
            /*P specimen.project_code PROJECTS AND P*/
            donor_vital_status IS NOT NULL AND specimen_type NOT LIKE '%Normal%' AND
            donor_age_at_diagnosis < {AGE} AND
            ((donor_vital_status == 'deceased' AND (time_survival > 0 OR time_followup > 0))
            OR
            (time_survival > {DAYS} OR time_followup > {DAYS}))
            """.replace("{DAYS}", str(self.days)).replace("{AGE}", str(maxAge))
    
    def getLabel(self, example):
        days = max(example["time_survival"], example["time_followup"])
        if example["donor_vital_status"] == "alive":
            assert days >= self.days
            return True
        else:
            assert example["donor_vital_status"] == "deceased"
            return days >= self.days

class RemissionV18(Experiment):
    def __init__(self):
        super(RemissionV18, self).__init__()
        self.exampleTable = "clinical"
        self.exampleFields = "icgc_donor_id,icgc_specimen_id,project_code,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup"
        self.exampleWhere = """
            length(specimen_type) > 0 AND 
            length(disease_status_last_followup) > 0 AND
            ((disease_status_last_followup LIKE '%remission%') OR
            (donor_vital_status IS 'deceased')) AND
            specimen_type NOT LIKE '%Normal%'
            """
    
    def getLabel(self, example):
        return 'remission' in example['disease_status_last_followup']
        
class Remission(Experiment):
    def __init__(self):
        super(Remission, self).__init__()
        self.query = """
            SELECT specimen.icgc_donor_id,specimen.icgc_specimen_id,
            specimen.project_code,specimen_type,donor_vital_status,disease_status_last_followup,donor_age_at_diagnosis
            FROM donor INNER JOIN specimen
            ON specimen.icgc_donor_id = donor.icgc_donor_id 
            WHERE
            /*P specimen.project_code PROJECTS AND P*/
            specimen_type IS NOT NULL AND
            ((donor_vital_status IS 'alive' AND 
            disease_status_last_followup IS 'complete remission') OR
            (donor_vital_status IS 'deceased' AND 
            (disease_status_last_followup IS NULL OR disease_status_last_followup NOT LIKE '%remission%'))) AND
            specimen_type NOT LIKE '%Normal%'
            """
    
    def getLabel(self, example):
        if example['disease_status_last_followup'] and ('remission' in example['disease_status_last_followup']):
            assert example['donor_vital_status'] == 'alive'
            return True
        else:
            assert example['donor_vital_status'] == 'deceased'
            return False