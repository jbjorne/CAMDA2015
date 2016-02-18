University of Turku in the CAMDA 2015 Challenge
===============================================

This code implements the experiments of the University of Turku IT Department for the [CAMDA 2015 Challenge](http://camda2015.bioinf.jku.at). The program concerns analysis of the ICGC cancer dataset using various machine learning methods. The data processing and experiment pipeline code builds on our work for the 2014 CAMDA challenge.

Required Libraries and Data
---------------------------

### Dependencies
The dependencies are listed in `requirements.txt`. Except for scikit-learn, other versions of the libraries may also work. The specific version 0.16.0 of scikit-learn is required for our extensions to work with it.

### Building the Database
All of the experiments rely on an SQLite database constructed from the ICGC data, so the database needs to be build first. The database can also be used for other applications without any need for the rest of the programs.

To build the database, run `python buildDB.py -o OUTPUT_DIR`, where OUTPUT_DIR is the name of the directory in which to download the ICGC files and build the database. The buildDB.py program will both download the ICGC files and build the database. To construct a database from already downloaded files please use the command line option `--action` or `--a`. The other options can be used to limit download and database import to a subset of the ICGC projects and data types. By default, methylation data will not be downloaded. 

Depending on the speed of your network connection and computer, downloading the ICGC files and building the database can be a very slow process. When using a regular desktop machine, generally around 24 hours should be reserved for the whole process. The database needs to be built only once, and after this step, running the experiments is relatively quick.

> NOTE: Downloading the ICGC release files will require about 12.2 Gb of disk space, and constructing the database will require an additional 56 Gb so please make sure you 
have enough free space before starting.

### Other data files
Once you have the ICGC database built, you can run most of the experiments. The only exception is the analysis of ranked features with the COSMIC database. If you wish to perform this analysis, you will need the COSMIC cancer census file `cancer_gene_census.csv`. To get this file, you will need to register at the COSMIC site and download the CSV file from their FTP site (the COSMIC license does not allow redistribution of this file).

The Experiment System
----------------------------------------
All experiments can be run using the program `run.py`. The experimental code uses a three-step system. One or more of these actions can be performed using the command line option `--action` or `--a`.

### Generating examples for machine learning
Examples are generated using the `build` action. A class is derived from src.Experiment to define the rules and limits for example generation. Classes for the experiments described in the paper are defined in the file `experiments.py`.

### Classification
Examples are classified using the `classify` action. A class can be derived from src.Classification to customize the overall approach for classifying the examples. For most experiments, src.Classification can be used as is. For defining the scikit-learn classifier and its parameters, the  `--classifier` and `--classifierArguments` of `run.py` can be used.

### Analyses
Classified examples can be used for various analyses with the `analyse` action. Analysis classes can be derived from src.analyse.Analysis to define such analyses, and the `--analyses` options of `run.py` can be used to choose which analyses to run for the experiment. Several predefined analyses are available in the src.analyse package.

Running the Experiments
-----------------------
In this section we describe the commands required to run the experiments described in the paper. 

With the following commands we assume the ICGC database is located at `~/CAMDA2015-data/ICGC-20.sqlite`. If not, please use the option `--icgcDB` or `--b` to define its location. Likewise, for experiments where the COSMIC analysis is used, we assume the required data files are in the directory `~/CAMDA2015-data`, but if not, the the option `--dataPath` or `--d` can be used to define their location.

In all the experiments, please replace `[OUTPUT]` with the name of the output directory.

### Classification Performance, COSMIC and Survival analyses

Classification performance is measured for the `Remission` task using the `ExpSeq` and `SSM_GENE_CONSEQUENCE` feature groups and for the `Survival` task using the `ExpSeq` feature group. These experiments produce the data shown in the paper Tables 1, 2 and 3. For the `Remission` experiments also the COSMIC analysis is run, shown in the paper in Table 5 and Figure 2. For the `Survival` experiment the survival analysis is run, shown in the paper in Figure 1.

1. `python run.py -e Remission -f ExpSeq -o [OUTPUT] -c ensemble.ExtraTreesClassifier -r "n_estimators=[1000];random_state=[1]" -p "%-US" -n 5 -y ProjectAnalysis,COSMICAnalysis --hidden`
2. `python run.py -e Remission -f SSM_GENE_CONSEQUENCE -o [OUTPUT] -c ensemble.ExtraTreesClassifier -r "n_estimators=[100];random_state=[1]" -p "%-US" -n 5 -y ProjectAnalysis,COSMICAnalysis --hidden`
3. `python run.py -e Survival -f ExpSeq -o [OUTPUT] -c ensemble.ExtraTreesClassifier -r "n_estimators=[100];random_state=[1]" -p "%-US" -n 5 -y ProjectAnalysis,SurvivalAnalysis --hidden`

### Subset Classification

To determine project combinations that improve performance for all included projects when using `SSM_GENE_CONSEQUENCE` features, the src.SubsetClassification class together with src.analyse.SubsetAnalysis is used.

`python run.py -e Remission -f SSM_GENE_CONSEQUENCE -o [OUTPUT] -c ensemble.ExtraTreesClassifier -r "n_estimators=[100];random_state=[1]" -n 5 -s SubsetClassification -y SubsetAnalysis --hidden -p "%-US"`