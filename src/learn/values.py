import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings
import data.result as result
import copy
import numpy as np
import matplotlib.pyplot as plt

def formatValue(value):
    if value == None:
        return "-"
    elif isinstance(value, basestring):
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
                        row[(experimentName, classifierName)] = classifier["auc-train"]
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
    #header = "project & \multicolumn{2}{c}{Multi-column}"
    return makeTableLatex(columns, rows, columnNames)

def pickTopTerm(terms, preferredTerms=None):
    if len(terms) == 0:
        return None
    terms = [eval(term) for term in terms]
    terms = sorted(terms, key=lambda tup: tup[4])
    if preferredTerms != None:
        for preferred in preferredTerms:
            for term in terms:
                if preferred in term[1].lower():
                    return term[1] + " [" + term[2] + "]"
    return terms[0][1] + " [" + terms[0][2] + "]" # return most common term

def makeGenesTable(projects):
    preferredTerms = {"KIRC-US":["kidney", "renal", "clear cell"],
                      "LUAD-US":["lung", "adenocarcinoma"],
                      "HNSC-US":["head and neck", "head", "neck", "squamous"]
                      }
    rows = []
    for projectName in ["KIRC-US", "HNSC-US", "LUAD-US"]:
        if projectName not in projects:
            continue
        project = projects[projectName]
        for experimentName in ["CANCER_OR_CONTROL"]:
            if experimentName in project:
                experiment = project[experimentName]
                classifierName = "ExtraTreesClassifier"
                if classifierName in experiment:
                    classifier = experiment[classifierName]
                    for feature in classifier["top-features"]:
                        row = {"project":projectName, "experiment":experimentName}
                        row["gene"] = feature["name"].split(":")[1]
                        row["n(r)"] = feature["CancerGeneIndex"]["term_count"]
                        row["role"] = pickTopTerm(feature["CancerGeneIndex"]["terms"], preferredTerms[projectName])
                        row["n(d)"] = feature["CancerGeneDrug"]["term_count"]
                        row["drug"] = pickTopTerm(feature["CancerGeneDrug"]["terms"])
                        rows.append(row)
    columns = ["project", "gene", "n(r)", "role", "n(d)", "drug"]
    return makeTableLatex(columns, rows)

def autolabel(rects, ax):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

def makeCGIFigure(projects, experiments):
    plots = {"CANCER_OR_CONTROL":211, "REMISSION":212}
    projectNames = ["KIRC-US", "HNSC-US", "LUAD-US"]
    colors = {"KIRC-US":"r", "HNSC-US":"g", "LUAD-US":"b"}
    markers = {"KIRC-US":"o", "HNSC-US":"h", "LUAD-US":"s"}
    data = {}
    plt.subplots_adjust(wspace=0.5)
    for experiment in experiments:
        for projectName in projectNames:
            if projectName in projects and experiment in projects[projectName] and "ExtraTreesClassifier" in projects[projectName][experiment]:
                classifier = projects[projectName][experiment]["ExtraTreesClassifier"]
                labels = []
                values = []
                for decile in classifier["gene-features-hidden"]:
                    label, value = decile.split("=")
                    value = float(value.split()[0])
                    labels.append(str(int(label)+1))
                    values.append(value)
                values.append(classifier["gene-features-nonselected"])
                labels.append("NS")
                data[projectName] = {"labels":labels, "values":values}
        #fig = plt.figure()
        #ax = fig.add_subplot(plots[experiment])
        ax = plt.subplot(plots[experiment])
        included = []
        for name in projectNames:
            if name in data:
                included.append(name)
        for index, name in enumerate(included):
            ind = np.arange(len(data[name]["values"]))  # the x locations for the groups
            width = 0.2       # the width of the bars        
            print data[name]["values"]
            #data[name]["rects"] = ax.bar(ind + index * width, data[name]["values"], width, color=colors[name])
            data[name]["rects"] = ax.plot(ind, data[name]["values"], color=colors[name])#, marker=markers[name], markersize=5)
        #ax.set_ylabel('cgi / features')
        #ax.set_title('Scores by group and gender')
        ax.set_xticks(ind)
        ax.set_xticklabels( data[data.keys()[0]]["labels"] )
        ax.legend( [data[name]["rects"][0] for name in included], included, loc="lower left" )
        plt.grid(True)
        #ax.legend( [data[name]["rects"]], ('Men', 'Women') )
        #for name in data:
        #    autolabel(data[name]["rects"], ax)
    plt.ylim(0,0.45)
    plt.xlabel('decile')
    plt.savefig(os.path.expanduser('~/Dropbox/git_repositories/CAMDA2014Abstract/figures/cgi-fraction.pdf'))
    plt.show()

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
                
                if "analysis" in meta:
                    classifier["gene-features-hidden"] = meta["analysis"]["CancerGeneIndex"]["hidden"]
                    classifier["gene-features-nonselected"] = meta["analysis"]["CancerGeneIndex"]["non-selected"]
                    classifier["top-features"] = []
                    for name, feature in meta["features"].items()[:5]:
                        feature["name"] = name
                        classifier["top-features"].append(feature)
    return projects

def process(dirname, projectFilter):
    if isinstance(projectFilter, basestring):
        projectFilter = projectFilter.split(",")
    projects = getProjects(dirname, projectFilter)
    print makeProjectTable(projects)
    print
    print makeGenesTable(projects)
    #makeCGIFigure(projects, ["CANCER_OR_CONTROL", "REMISSION"])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-d','--directory', help='', default=None)
    parser.add_argument('-p','--projects', help='', default=None)
    options = parser.parse_args()
    
    process(os.path.abspath(os.path.expanduser(options.directory)), options.projects)