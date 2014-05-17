import sys, os, tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.example import exampleOptions, readAuto
from data.template import parseOptionString
from data.cache import getExperiment
import settings
import learn

CLASSIFIER_ARGS = {
    'ensemble.RandomForest':{'n_estimators':[10,100],'max_features':['auto',None]},
    'svm.LinearSVC':{'C':settings.logrange(-10, 10)}
}

def runImmediate(experiment, project, classifier, classifierArgs, results, database, hidden, writer):
    featureFilePath, labelFilePath, metaFilePath = getExperiment(
                    experiment=experiment, experimentOptions={'project':project}, 
                    database=database, hidden=hidden, writer=writer, useCached=True)
    learn.test(featureFilePath, labelFilePath, metaFilePath, classifier=classifier, classifierArgs=classifierArgs, 
                resultPath=results)
                
def batch(experiments, projects, classifiers, database, hidden, writer):
    if isinstance(experiments, basestring):
        experiments = experiments.split(",")
    if isinstance(projects, basestring):
        projects = projects.split(",")
    run = runImmediate
    for experiment in experiments:
        template = settings[experiment]
        if 'project' in template:
            projectsToProcess = projects
        else:
            projectsToProcess = [None]
        for project in projectsToProcess:
            for classifier in classifiers:
                print "Processing", experiment + "/" + str(project) + "/" + classifier
                run(experiment, project, classifier, CLASSIFIER_ARGS[classifier], database, hidden, writer)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(parents=[exampleOptions], description='')
    parser.add_argument('-e','--experiments', help='', default=None)
    parser.add_argument('-p','--projects', help='', default=None)
    parser.add_argument('-r','--results', help='Output directory', default=None)
    parser.add_argument('--slurm', help='', default=False, action="store_true")
    parser.add_argument('--cacheDir', help='Cache directory (optional)', default=os.path.join(tempfile.gettempdir(), "CAMDA2014"))
    options = parser.parse_args()
