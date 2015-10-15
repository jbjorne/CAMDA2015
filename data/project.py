import math
import sqlite3

def connect(con):
    if isinstance(con, basestring):
        con = sqlite3.connect(con) # @UndefinedVariable
        con.row_factory = sqlite3.Row # @UndefinedVariable
        con.create_function("log", 1, math.log)
    return con

class Project:
    def getExampleFields(self):
        return "icgc_donor_id,icgc_specimen_id,project_code,donor_vital_status,disease_status_last_followup,specimen_type,donor_interval_of_last_followup"
    
    def getExampleTable(self):
        return "clinical"
    
    def getExampleConditions(self):
        return """
        length(specimen_type) > 0 AND 
        length(disease_status_last_followup) > 0 AND
        ((disease_status_last_followup LIKE '%remission%') OR
        (donor_vital_status IS 'deceased')) AND
        specimen_type NOT LIKE '%Normal%'
        """
    
    def getExamples(self):
        query = "SELECT " + self.getExampleFields() + "\n"
        query += "FROM " + self.getExampleTable() + "\n"
        query += "WHERE "
        if self.projects != None:
            query += " project_code IN " + self.projects + " AND" + "\n"
        query += self.getExampleConditions()
    
    def getLabel(self, example):
        return 'remission' in example['disease_status_last_followup']
    
    def __init__(self):
        self.name
        self.projects = None
        self.classes = {'True':1, 'False':-1},
        self.features = [SSM_GENE_CONSEQUENCE],
        self.filter = SSM_FILTER
        self.hidden = 0.3
        self.meta = META
    
    def process(con, experimentName, callback, callbackArgs, metaDataFileName=None, options=None, experimentMeta=None):
        con = connect(con)
        template = parseExperiment(experimentName).copy()
        template = parseTemplateOptions(options, template)
        #con = connect(con, template.get("functions", None))
        #options = updateTemplateOptions(template, options)
        print "Template:", self.name
        print json.dumps(template, indent=4)
        compiled, lambdaArgs = compileTemplate(template)
        print "Compiled experiment"
        examples = [dict(x) for x in compiled["example"](con=con, **lambdaArgs)]
        numHidden = hidden.setHiddenValues(examples, compiled)
        numExamples = len(examples)
        print "Examples " +  str(numExamples) + ", hidden " + str(numHidden)
        count = 0
        clsIds = compiled.get("classes", None)
        hiddenRule = compiled.get("include", "train")
        featureIds = {}
        meta = []
        featureGroups = compiled.get("features", [])
        sampleRandom = MTwister()
        sampleRandom.set_seed(2)
        for example in examples:
            count += 1
            if not hidden.getInclude(example, compiled.get("hidden", None), hiddenRule):
                continue
            hidden.setSet(example, compiled.get("hidden", None))
            #print experiment["class"](con, example)
            #if count % 10 == 0:
            print "Processing example", example,
            cls = getIdOrValue(compiled["label"](con=con, example=example, **lambdaArgs), clsIds)
            print cls, str(count) + "/" + str(numExamples)
            strCls = str(cls)
            if "sample" in compiled and strCls in compiled["sample"] and sampleRandom.random() > compiled["sample"][strCls]:
                print "NOTE: Downsampled example"
                continue
            if "filter" in compiled and compiled["filter"] != None and len([x for x in compiled["filter"](con=con, example=example, **lambdaArgs)]) == 0:
                print "NOTE: Filtered example"
                continue
            features = {}
            for featureGroup in featureGroups:
                for row in featureGroup(con=con, example=example, **lambdaArgs):
                    for key, value in itertools.izip(*[iter(row)] * 2): # iterate over each consecutive key,value columns pair
                        if not isinstance(key, basestring):
                            raise Exception("Non-string feature key '" + str(key) + "' in feature group " + str(featureGroups.index(featureGroup)))
                        if not isinstance(value, Number):
                            raise Exception("Non-number feature value '" + str(value) + "' in feature group " + str(featureGroups.index(featureGroup)))
                        features[getId(key, featureIds)] = value
            if len(features) == 0:
                print "WARNING: example has no features"
            if callback != None:
                callback(example=example, cls=cls, features=features, **callbackArgs)
            if "meta" in compiled:
                meta.append(compiled["meta"](label=cls, features=features, example=example, **lambdaArgs))
        saveMetaData(metaDataFileName, con, template, experimentName, options, clsIds, featureIds, meta, experimentMeta)
        return featureIds