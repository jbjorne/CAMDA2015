import os
from data.project import Experiment
from learn.Classification import Classification
from learn.FeatureGroup import FeatureGroup

DATA_PATH = os.path.expanduser("~/data/CAMDA2015-data-local/")
DB_PATH = os.path.join(DATA_PATH, "database/ICGC-18-150514.sqlite")

#SSM_GENE_CONSEQUENCE = "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"
#SSM_GENE_POS = "SELECT ('SSM:'||gene_affected||':'||consequence_type||':'||chromosome||':'||chromosome_start||':'||chromosome_end),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"

class SSMCluster(FeatureGroup):
    def __init__(self):
        super(SSMCluster, self).__init__("SSM", "SELECT KEYS FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?", ["consequence_type", "chromosome", "chromosome_start"])   
    
    def getFeatureName(self, row):
        return ":".join([str(x) for x in [self.name, row["chromosome"], row["chromosome_start"] / 100, row["consequence_type"]]])

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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run University of Turku experiments for CAMDA 2015')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-d', "--debug", default=False, action="store_true", dest="debug")
    groupE = parser.add_argument_group('Examples', 'Example Generation')
    groupE.add_argument('-e', "--examples", default=False, action="store_true", dest="examples")
    groupE.add_argument('-x', '--experiment', help='Output directory', default="RemissionMutTest")
    groupE.add_argument('--projects', help='Projects used in example generation', default=None)
    groupE.add_argument('-b', '--icgcDB', default=DB_PATH, dest="icgcDB")
    groupC = parser.add_argument_group('Classification', 'Example Classification')
    groupC.add_argument('-c','--classifier', help='', default=None)
    groupC.add_argument('-a','--classifierArguments', help='', default=None)
    groupC.add_argument('-m','--metric', help='', default="roc_auc")
    groupC.add_argument('-i','--iteratorCV', help='', default='getStratifiedKFoldCV')
    groupC.add_argument('-f','--numFolds', help='Number of folds in cross-validation', type=int, default=10)
    groupC.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
    groupC.add_argument('-p', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    groupC.add_argument("--hidden", default=False, action="store_true", dest="hidden")
    groupC.add_argument('--preDispatch', help='', default='2*n_jobs')
    groupA = parser.add_argument_group('Analysis', 'Analysis for classified data')
    groupA.add_argument("--cosmic", default=False, action="store_true", dest="cosmic")
    options = parser.parse_args()
    
    if options.examples:
        print "======================================================"
        print "Building Examples"
        print "======================================================"
        ExperimentClass = eval(options.experiment)
        e = ExperimentClass()
        if options.projects != None:
            e.projects = options.projects.split(",")
        e.databasePath = options.icgcDB
        e.debug = options.debug
        e.writeExamples(options.output)
    
    resultPath = os.path.join(options.output, "classification.json")
    if options.classifier != None:
        print "======================================================"
        print "Classifying"
        print "======================================================"
        classification = Classification(options.classifier, options.classifierArguments, options.numFolds, options.parallel, options.metric, classifyHidden=options.hidden)
        classification.classifierName = options.classifier
        classification.classifierArgs = options.classifierArguments
        classification.metric = options.metric
        classification.readExamples(options.output)
        classification.classify(resultPath)
    
    if options.cosmic:
        print "======================================================"
        print "Analysing"
        print "======================================================"
        from learn.Analysis import COSMICAnalysis
        meta = resultPath
        if options.classifier != None:
            meta = classification.meta
        analysis = COSMICAnalysis(meta, dataPath=DATA_PATH)
        analysis.analyse(options.output, "cosmic")