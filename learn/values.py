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
                for classifierName in ["LinearSVC", "ExtraTreesClassifier", "RLScore"]:
                    if classifierName in experiment:
                        classifier = experiment[classifierName]
                        #if experiment["classifier"] == "ensemble.ExtraTreesClassifier":
                        row[(experimentName, classifierName)] = classifier["score-hidden"]
                        row[(experimentName, 1)] = classifier["1"]
                        row[(experimentName, -1)] = classifier["-1"]
        rows.append(row)
    columns = ["project",
               ("CANCER_OR_CONTROL", 1),
               ("CANCER_OR_CONTROL", -1),
               ("CANCER_OR_CONTROL", "RLScore"),
               ("CANCER_OR_CONTROL", "LinearSVC"),
               ("CANCER_OR_CONTROL", "ExtraTreesClassifier"),
               ("REMISSION", 1),
               ("REMISSION", -1),
               ("REMISSION", "RLScore"),
               ("REMISSION", "LinearSVC"),
               ("REMISSION", "ExtraTreesClassifier")]
    columnNames = {("CANCER_OR_CONTROL", "ExtraTreesClassifier"):"$AUC_E$",
                   ("CANCER_OR_CONTROL", "LinearSVC"):"$AUC_S$",
                   ("CANCER_OR_CONTROL", "RLScore"):"$AUC_R$",
                   ("CANCER_OR_CONTROL", 1):"cancer",
                   ("CANCER_OR_CONTROL", -1):"normal",
                   ("REMISSION", "ExtraTreesClassifier"):"$AUC_E$",
                   ("REMISSION", "LinearSVC"):"$AUC_S$",
                   ("REMISSION", "RLScore"):"$AUC_R$",
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

def listTopGenes(projects):
    for projectName in ["KIRC-US", "HNSC-US", "LUAD-US"]:
        if projectName not in projects:
            continue
        project = projects[projectName]
        print "===", projectName, "==="
        for experimentName in ["CANCER_OR_CONTROL"]:
            if experimentName in project:
                experiment = project[experimentName]
                classifierName = "ExtraTreesClassifier"
                if classifierName in experiment:
                    classifier = experiment[classifierName]
                    for feature in classifier["top-features"]:
                        print feature["name"].split(":")[1]
    

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
                        # read terms
                        row["n(r)"] = 0
                        row["role"] = "-"
                        if "CancerGeneIndex" in feature:
                            row["n(r)"] = feature["CancerGeneIndex"]["term_count"]
                            row["role"] = pickTopTerm(feature["CancerGeneIndex"]["terms"], preferredTerms[projectName])
                        # read drugs
                        row["n(d)"] = 0
                        row["drug"] = "-"
                        if "CancerGeneDrug" in feature:
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

def makeCGIFigure(projects, experiments, outdir):
    plots = {"CANCER_OR_CONTROL":211, "REMISSION":212}
    titles = {"CANCER_OR_CONTROL":"cancer/control", "REMISSION":"remission/progression"}
    projectNames = ["KIRC-US", "HNSC-US", "LUAD-US"]
    colors = {"KIRC-US":"blue", "HNSC-US":"black", "LUAD-US":"red"}
    markers = {"KIRC-US":"o", "HNSC-US":"h", "LUAD-US":"s"}
    linestyles = {"KIRC-US":"-", "HNSC-US":"--", "LUAD-US":":"}
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
            data[name]["rects"] = ax.plot(ind, data[name]["values"], color=colors[name], linestyle=linestyles[name])#, marker=markers[name], markersize=5)
        #ax.set_ylabel('cgi / features')
        #ax.set_title('Scores by group and gender')
        #ax.set_title(titles[experiment])
        ax.text(0.99, 0.96, titles[experiment],
                verticalalignment='top', horizontalalignment='right',
                transform=ax.transAxes,
                color='black', fontsize=15)
        ax.set_xticks(ind)
        ax.set_xticklabels( data[data.keys()[0]]["labels"] )
        ax.legend( [data[name]["rects"][0] for name in included], included, loc="lower left" )
        plt.grid(True, color='#ADADAD')
        #ax.legend( [data[name]["rects"]], ('Men', 'Women') )
        #for name in data:
        #    autolabel(data[name]["rects"], ax)
    plt.ylim(0,0.45)
    plt.xlabel('decile')
    #plt.savefig(os.path.expanduser('~/Dropbox/git_repositories/CAMDA2014Abstract/figures/cgi-fraction.pdf'))
    plt.savefig(os.path.join(outdir, 'cgi-fraction.pdf'))
    plt.show()

def processProjects(projects):
    classifier["classifier-details"] = meta["results"]["hidden"]["classifier"]
    classifier["score-hidden"] = meta["results"]["hidden"]["score"]
    classifier["score-train"] = meta["results"]["best"]["mean"]
    classifier["std-train"] = meta["results"]["best"]["std"]
    classifier.update(countExamples(meta))
    
    if "analysis" in meta:
        classifier["gene-features-hidden"] = meta["analysis"]["CancerGeneIndex"]["hidden"]
        classifier["gene-features-nonselected"] = meta["analysis"]["CancerGeneIndex"]["non-selected"]
        classifier["top-features"] = []
        for name, feature in meta["features"].items()[:numTopFeatures]:
            feature["name"] = name
            classifier["top-features"].append(feature)

def process(indir, outdir, projectFilter, numTopFeatures=30, actions=""):
    if isinstance(projectFilter, basestring):
        projectFilter = projectFilter.split(",")
    projects = result.getProjects(indir, {"filename":projectFilter, "features":"ALL_FEATURES"}, numTopFeatures)
    if "PROJECTS" in actions:
        print "----------------------------", "Projects", "----------------------------"
        print makeProjectTable(projects)
        print
    if "GENES" in actions:
        print "----------------------------", "Genes", "----------------------------"
        print makeGenesTable(projects)
        print
    if "GENE_LIST" in actions:
        print "----------------------------", "Genes List", "----------------------------"
        print listTopGenes(projects)
    if outdir:
        makeCGIFigure(projects, ["CANCER_OR_CONTROL", "REMISSION"], outdir)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-a','--actions', help='', default="PROJECTS,GENES,GENE_LIST")
    parser.add_argument('-i','--input', help='', default=None)
    parser.add_argument('-o','--output', help='', default=None)
    parser.add_argument('-p','--projects', help='', default=None)
    parser.add_argument('-n','--numTopFeatures', help='', type=int, default=30)
    #parser.add_argument('-c','--classifier', help='', default="ExtraTreesClassifier")
    options = parser.parse_args()
    
    process(options.input, options.output, options.projects, options.numTopFeatures, options.actions.split(","))