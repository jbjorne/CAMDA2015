from learn.Experiment import Experiment
from learn.FeatureGroup import FeatureGroup

#SSM_GENE_CONSEQUENCE = "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"
#SSM_GENE_POS = "SELECT ('SSM:'||gene_affected||':'||consequence_type||':'||chromosome||':'||chromosome_start||':'||chromosome_end),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"

class SSMCluster(FeatureGroup):
    def __init__(self):
        super(SSMCluster, self).__init__("SSM", "SELECT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["consequence_type", "chromosome", "chromosome_start"])   
    def getFeatureName(self, row):
        return [row["chromosome"], row["chromosome_start"] / 10000, row["consequence_type"]]

SSM_GENE_CONSEQUENCE = FeatureGroup("SSM", "SELECT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["gene_affected", "consequence_type"])
SSM_GENE_POS = FeatureGroup("SSM", "SELECT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["gene_affected", "consequence_type", "chromosome", "chromosome_start", "chromosome_end"])
SSM_CLUSTER = SSMCluster()

class RemissionMutTest(Experiment):
    def __init__(self):
        super(RemissionMutTest, self).__init__()
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
        self.featureGroups = [SSM_GENE_CONSEQUENCE]
        self.filter = "SELECT * FROM simple_somatic_mutation_open WHERE icgc_specimen_id=? LIMIT 1"
    
    def getLabel(self, example):
        return 'remission' in example['disease_status_last_followup']

class RemissionMutSites(RemissionMutTest):
    def __init__(self):
        super(RemissionMutSites, self).__init__()
        self.featureGroups = [SSM_GENE_POS]

class RemissionMutCluster(RemissionMutTest):
    def __init__(self):
        super(RemissionMutCluster, self).__init__()
        self.featureGroups = [SSM_CLUSTER]