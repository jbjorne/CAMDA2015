import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
import data.result as result
import copy

def formatValue(value):
    if isinstance(value, basestring):
        return value
    elif isinstance(value, int):
        return str(value)
    else:
        return str("%0.2f" % value)

def makeTableLatex(columns, rows, columnNames = {}):
    columnNames = copy.copy(columnNames)
    for column in columns:
        if column not in columnNames:
            columnNames[column] = column
    header = " & ".join([columnNames[column] for column in columns]) + " \\\\\n"
    body = ""
    for row in rows:
        #print row, columns
        body += " & ".join([formatValue(row.get(column, "-")) for column in columns]) + " \\\\\n"
    return header + body
    
def makeProjectTable(projects):
    rows = []
    for projectName in sorted(projects.keys()):
        project = projects[projectName]
        row = {"project":projectName}
        for experimentName in ["CANCER_OR_CONTROL", "REMISSION"]:
            if experimentName in project:
                experiment = project[experimentName]
                for classifierName in ["LinearSVC", "ExtraTreesClassifier"]:
                    if classifierName in experiment:
                        classifier = experiment[classifierName]
                        #if experiment["classifier"] == "ensemble.ExtraTreesClassifier":
                        row[(experimentName, classifierName)] = classifier["auc-hidden"]
                        row[(experimentName, 1)] = classifier["1"]
                        row[(experimentName, -1)] = classifier["-1"]
        rows.append(row)
    columns = ["project",
               ("CANCER_OR_CONTROL", 1),
               ("CANCER_OR_CONTROL", -1),
               ("CANCER_OR_CONTROL", "ExtraTreesClassifier"),
               ("CANCER_OR_CONTROL", "LinearSVC"),
               ("REMISSION", 1),
               ("REMISSION", -1),
               ("REMISSION", "ExtraTreesClassifier"),
               ("REMISSION", "LinearSVC")]
    columnNames = {("CANCER_OR_CONTROL", "ExtraTreesClassifier"):"$AUC_E$",
                   ("CANCER_OR_CONTROL", "LinearSVC"):"$AUC_S$",
                   ("CANCER_OR_CONTROL", 1):"cancer",
                   ("CANCER_OR_CONTROL", -1):"normal",
                   ("REMISSION", "ExtraTreesClassifier"):"$AUC_E$",
                   ("REMISSION", "LinearSVC"):"$AUC_S$",
                   ("REMISSION", 1):"remission",
                   ("REMISSION", -1):"progression"}
    header = "project & \multicolumn{2}{c}{Multi-column}"
    return makeTableLatex(columns, rows, columnNames)

def countExamples(meta):
    counts = {"1":0, "-1":0}
    for example in meta["examples"]:
        counts[example["label"]] += 1
    return counts
        
def getProjects(dirname, projectFilter):
    projects = {}
    print "Reading results from", dirname
    filenames = os.listdir(dirname)
    index = 0
    for dirpath, dirnames, filenames in os.walk(dirname):
        for filename in filenames:
            index += 1
            filePath = os.path.join(dirpath, filename)
            found = True
            if projectFilter != None:
                found = False
                for projectName in projectFilter:
                    if projectName in filename:
                        found = True
                        break
            if found and os.path.isfile(filePath) and filePath.endswith(".json"):
                print "Processing", filename, str(index+1) #+ "/" + str(len(filenames))
                meta = result.getMeta(filePath)
                projectName = meta["template"]["project"]
                if projectName not in projects:
                    projects[projectName] = {}
                project = projects[projectName]
                experimentName = meta["experiment"]["name"]
                if experimentName not in project:
                    project[experimentName] = {}
                experiment = project[experimentName]
                classifierName = meta["results"]["best"]["classifier"]
                if classifierName not in experiment:
                    experiment[classifierName] = {}
                classifier = experiment[classifierName]
                #experiment["classifier"] = meta["results"]["best"]["classifier"]
                classifier["classifier-details"] = meta["results"]["hidden"]["classifier"]
                classifier["auc-hidden"] = meta["results"]["hidden"]["roc_auc"]
                classifier["auc-train"] = meta["results"]["best"]["mean"]
                classifier["std-train"] = meta["results"]["best"]["std"]
                classifier.update(countExamples(meta))
    return projects

def process(dirname, projectFilter):
    if isinstance(projectFilter, basestring):
        projectFilter = projectFilter.split(",")
    projects = getProjects(dirname, projectFilter)
    print makeProjectTable(projects)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-d','--directory', help='', default=None)
    parser.add_argument('-p','--projects', help='', default=None)
    options = parser.parse_args()
    
    process(os.path.abspath(os.path.expanduser(options.directory)), options.projects)