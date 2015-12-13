from learn.Experiment import Experiment
from learn.FeatureGroup import FeatureGroup
from itertools import combinations

###############################################################################
# Features
###############################################################################

#SSM_GENE_CONSEQUENCE = "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"
#SSM_GENE_POS = "SELECT ('SSM:'||gene_affected||':'||consequence_type||':'||chromosome||':'||chromosome_start||':'||chromosome_end),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"

class SSMClusterBase(FeatureGroup):
    def __init__(self):
        super(SSMClusterBase, self).__init__("SSM", "SELECT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["consequence_type", "chromosome", "chromosome_start"])   

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

SSM_CONSEQUENCE = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["consequence_type"])
SSM_GENE = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["gene_affected"])
#SSM_GENE_PROJECT = FeatureGroup("SSM", "SELECT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["gene_affected", "project_code"])
SSM_PROJECT = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["project_code"])
SSM_TRANSCRIPT = FeatureGroup("SSM", "SELECT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["transcript_affected"])
SSM_GENE_CONSEQUENCE = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["gene_affected", "consequence_type"])
SSM_GENE_CONSEQUENCE_V20 = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM ssm WHERE icgc_specimen_id=?", ["gene_affected", "consequence_type"])
SSM_CHROMOSOME_CONSEQUENCE = FeatureGroup("SSM", "SELECT DISTINCT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["chromosome", "consequence_type"])
SSM_GENE_POS = FeatureGroup("SSM", "SELECT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["gene_affected", "consequence_type", "chromosome", "chromosome_start", "chromosome_end"])

CNSM_MUTATION_TYPE = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM copy_number_somatic_mutation WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["mutation_type"])
CNSM_CHROMOSOME = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM copy_number_somatic_mutation WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["chromosome", "mutation_type"])
CNSM_CHROMOSOME_COUNT = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM copy_number_somatic_mutation WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["chromosome", "mutation_type", "copy_number"])
CNSM_GENE = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM copy_number_somatic_mutation WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["gene_affected", "copy_number"])

CNSM_CHROMOSOME_COUNT_V20 = FeatureGroup("CNSM", "SELECT DISTINCT KEYS FROM cnsm WHERE mutation_type IS NOT 'undetermined' AND icgc_specimen_id=?", ["chromosome", "mutation_type", "copy_number"])

###############################################################################
# Experiments
###############################################################################

class Survival(Experiment):
    def __init__(self, days=365):
        super(Survival, self).__init__()
        self.days = days
        self.query = """
            SELECT specimen.icgc_donor_id,specimen.icgc_specimen_id,donor_survival_time,donor_interval_of_last_followup,
            specimen.project_code,specimen_type,donor_vital_status,disease_status_last_followup
            FROM donor INNER JOIN specimen
            ON specimen.icgc_donor_id = donor.icgc_donor_id 
            WHERE
            donor_vital_status IS NOT NULL AND
            ((donor_vital_status == 'deceased'  AND 
            (donor_survival_time IS NOT NULL OR donor_interval_of_last_followup IS NOT NULL))
            OR
            (donor_survival_time > %d OR donor_interval_of_last_followup > %d))
            """ % (self.days, self.days)
    
    def getDays(self, example):
        return max([example[key] for key in ["donor_survival_time", "donor_interval_of_last_followup"] if example[key] != None])
        #return max((example.get("donor_survival_time", 0), example.get("donor_interval_of_last_followup", 0))
    
    def getLabel(self, example):
        days = self.getDays(example)
        if example["donor_vital_status"] == "alive":
            assert days >= self.days
            return True
        else:
            assert example["donor_vital_status"] == "deceased"
            return days >= self.days

#         if example["donor_survival_time"]  != None:
#             assert example["donor_vital_status"] == "deceased"
#             return example["donor_survival_time"] >= self.days
#         else:
#             assert example["donor_vital_status"] == "alive"
#             return True

class RemissionBase(Experiment):
    def __init__(self):
        super(RemissionBase, self).__init__()
        #self.projects = ["KIRC-US"]
        self.exampleTable = "clinical"
        self.exampleFields = "icgc_donor_id,icgc_specimen_id,project_code,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup"
        self.exampleWhere = """
            length(specimen_type) > 0 AND 
            length(disease_status_last_followup) > 0 AND
            ((disease_status_last_followup LIKE '%remission%') OR
            (donor_vital_status IS 'deceased')) AND
            specimen_type NOT LIKE '%Normal%'
            """
        #self.filter = "SELECT * FROM simple_somatic_mutation_open WHERE icgc_specimen_id=? LIMIT 1"
        #self.unique = "icgc_donor_id"
    
    def getLabel(self, example):
        return 'remission' in example['disease_status_last_followup']
        
class RemissionV20(Experiment):
    def __init__(self):
        super(RemissionV20, self).__init__()
        self.query = """
            SELECT specimen.icgc_donor_id,specimen.icgc_specimen_id,
            specimen.project_code,specimen_type,donor_vital_status,disease_status_last_followup
            FROM donor INNER JOIN specimen
            ON specimen.icgc_donor_id = donor.icgc_donor_id 
            WHERE
            length(specimen_type) > 0 AND 
            length(disease_status_last_followup) > 0 AND
            ((disease_status_last_followup LIKE '%remission%') OR
            (donor_vital_status IS 'deceased')) AND
            specimen_type NOT LIKE '%Normal%'
            """
            #specimen_interval is NULL AND
            #specimen_type LIKE 'Primary%' AND
    
    def getLabel(self, example):
        return 'remission' in example['disease_status_last_followup']


class RemissionMutTest(RemissionBase):
    def __init__(self):
        super(RemissionMutTest, self).__init__()
        self.featureGroups = [SSM_GENE_CONSEQUENCE]

class RemissionConsequence(RemissionBase):
    def __init__(self):
        super(RemissionConsequence, self).__init__()
        self.featureGroups = [SSM_CONSEQUENCE]

class RemissionGene(RemissionBase):
    def __init__(self):
        super(RemissionGene, self).__init__()
        self.featureGroups = [SSM_GENE]

class RemissionMutSites(RemissionBase):
    def __init__(self):
        super(RemissionMutSites, self).__init__()
        self.featureGroups = [SSM_GENE_POS]

class RemissionMutClusterSimple(RemissionBase):
    def __init__(self):
        super(RemissionMutClusterSimple, self).__init__()
        self.featureGroups = [SSMClusterSimple()]

class RemissionMutCluster(RemissionBase):
    def __init__(self):
        super(RemissionMutCluster, self).__init__()
        self.featureGroups = [SSMCluster()]