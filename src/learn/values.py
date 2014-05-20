import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
import data.result as result
import copy

def makeTableLatex(columns, rows, columnNames = {}):
    columnNames = copy.copy(columnNames)
    for column in columns:
        if column not in columnNames:
            columnNames[column] = column
    header = " & ".join([columnNames[column] for column in columns]) + " \\\n"
    body = ""
    for row in rows:
        print row
        body += " & ".join([row.get(column, "-") for column in columns]) + " \\\n"
    return header + body
    
def makeProjectTable(projects):
    rows = []
    for projectName in sorted(projects.keys()):
        project = projects[projectName]
        row = {"project":projectName}
        for experimentName in ["CANCER_OR_CONTROL", "REMISSION"]:
            if experimentName in project:
                experiment = project[experimentName]
                #if experiment["classifier"] == "ensemble.ExtraTreesClassifier":
                row[(experimentName, experiment["classifier"])] = experiment["auc-hidden"]
        rows.append(row)
    columns = ["project", 
               ("CANCER_OR_CONTROL", "ensemble.ExtraTreesClassifier"),
               ("REMISSION", "ensemble.ExtraTreesClassifier")]
    columnNames = {("CANCER_OR_CONTROL", "ensemble.ExtraTreesClassifier"):"AUC",
                   ("REMISSION", "ensemble.ExtraTreesClassifier"):"AUC"}
    return makeTableLatex(columns, rows, columnNames)
        
def getProjects(dirname, projectFilter):
    projects = {}
    print "Reading results from", dirname
    filenames = os.listdir(dirname)
    for index, filename in enumerate(filenames):
        filePath = os.path.join(dirname, filename)
        found = True
        if projectFilter != None:
            found = False
            for projectName in projectFilter:
                if projectName in filename:
                    found = True
                    break
        if found and os.path.isfile(filePath) and filePath.endswith(".json"):
            print "Processing", filename, str(index+1) + "/" + str(len(filenames))
            meta = result.getMeta(filePath)
            projectName = meta["template"]["project"]
            if projectName not in projects:
                projects[projectName] = {}
            project = projects[projectName]
            experimentName = meta["experiment"]["name"]
            if experimentName not in project:
                project[experimentName] = {}
            experiment = project[experimentName]
            experiment["classifier"] = meta["results"]["best"]["classifier"]
            experiment["classifier-details"] = meta["results"]["hidden"]["classifier"]
            experiment["auc-hidden"] = meta["results"]["hidden"]["roc_auc"]
            experiment["auc-train"] = meta["results"]["best"]["mean"]
            experiment["std-train"] = meta["results"]["best"]["std"]
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