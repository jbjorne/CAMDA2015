import os
from data.project import Experiment
from learn.Classification import Classification

DATA_PATH = os.path.expanduser("~/data/CAMDA2015-data-local/")
DB_PATH = os.path.join(DATA_PATH, "database/ICGC-18-150514.sqlite")

SSM_GENE_CONSEQUENCE = "SELECT ('SSM:'||gene_affected||':'||consequence_type),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"
SSM_GENE_POS = "SELECT ('SSM:'||gene_affected||':'||consequence_type||':'||chromosome||':'||chromosome_start||':'||chromosome_end),1 FROM simple_somatic_mutation_open WHERE icgc_specimen_id=?"

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
        self.projects = ["KIRC-US"]
        self.featureGroups = [SSM_GENE_POS]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run University of Turku experiments for CAMDA 2015')
    parser.add_argument('-x', '--experiment', help='Output directory', default="RemissionMutTest")
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-b', '--icgcDB', default=DB_PATH, dest="icgcDB")
    parser.add_argument('-d', "--debug", default=False, action="store_true", dest="debug")
    parser.add_argument('-e', "--examples", default=False, action="store_true", dest="examples")
    parser.add_argument('-c','--classifier', help='', default=None)
    parser.add_argument('-a','--classifierArguments', help='', default=None)
    parser.add_argument('-m','--metric', help='', default="roc_auc")
    parser.add_argument('-i','--iteratorCV', help='', default='getStratifiedKFoldCV')
    parser.add_argument('-f','--numFolds', help='Number of folds in cross-validation', type=int, default=10)
    parser.add_argument('-v','--verbose', help='Cross-validation verbosity', type=int, default=3)
    parser.add_argument('-p', '--parallel', help='Cross-validation parallel jobs', type=int, default=1)
    parser.add_argument("--hidden", default=False, action="store_true", dest="hidden")
    parser.add_argument('--preDispatch', help='', default='2*n_jobs')
    parser.add_argument("--cosmic", default=False, action="store_true", dest="cosmic")
    options = parser.parse_args()
    
    ExperimentClass = eval(options.experiment)
    
    if options.examples:
        print "======================================================"
        print "Building Examples"
        print "======================================================"
        e = ExperimentClass()
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