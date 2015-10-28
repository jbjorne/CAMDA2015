import sys, os
from data.project import Experiment
import data.writer
from utils.Database import Database

DATA_PATH = os.path.expanduser("~/data/CAMDA2015-data-local/")
DB_PATH = os.path.join(DATA_PATH, "database/ICGC-18-150514.sqlite")

SSM_GENE_CONSEQUENCE = "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"

class RemissionMutTest(Experiment):
    def __init__(self):
        Experiment.__init__(self)
        self.projects = ["KIRC-US"]
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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run University of Turku experiments for CAMDA 2014')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-b', '--icgcDB', default=DB_PATH, dest="icgcDB")
    parser.add_argument('-d', "--debug", default=False, action="store_true", dest="debug")
    options = parser.parse_args()
    
    e = RemissionMutTest()
    e.databasePath = options.icgcDB
    e.debug = options.debug
    e.writeExamples(options.output)