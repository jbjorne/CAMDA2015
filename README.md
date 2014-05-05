CAMDA 2014
=========

Challenge Dataset 1: ICGC Cancer Genomes
----------------------------------------

The [CAMDA site](http://camda2014.bioinf.jku.at/doku.php/contest_dataset) states that:

>From the comprehensive description of genomic, transcriptomic and epigenomic changes provided by ICGC, the main goal of this challenge is to gain novel biological insights to less well studied cancers selected here. However, we are not merely looking for 'old paradigm' cancer subtype classification!

>For this challenge, only processed data are provided. These cancers all have matched gene expression, microRNA expression, protein expression profiles, somatic CNV, and methylation.


The goal of the CAMDA 2014 challenge 1 (ICGC Cancer Genomes) is to use the ICGC cancer data to try to answer the questions:

1. **What are disease causal changes?** Can the integration of comprehensive multi-track -omics data give a clear answer?
2. **Can personalized medicine and rational drug treatment plans be derived from the data?** And how can we validate them down the road?

The ICGC datasets for the CAMDA challenge (all from the TCGA project):

* HNSC-US (Head and Neck Squamous Cell Carcinoma)
* LUAD-US (Lung Adenocarcinoma)
* KIRC-US (Kidney Renal Clear Cell Carcinoma)

Using the code
----------------------------------------
1. Download the SQLite database from sftp://taito.csc.fi/wrk/jakrbj/CAMDA2014. 
2. Unpack the database to the local disk
3. Alternatively, the database can be constructed using src/data/buildDB.py, but this will take several hours.
4. Generate examples using src/data/buildExamples.py, using a defined experiment. The program will generate an SVM-light format example file and a metadata file containing further information on the examples, class and feature ids etc.

Experiments
----------------------------------------
All experiments are run using the command: `python buildExamples.py -o EXAMPLE_FILE -m METADATA_FILE -b DATABASE_FILE -e EXPERIMENT_NAME -p EXPERIMENT_OPTIONS`. The EXPERIMENT_NAME refers to an experiment template, usually read from src/settings.py. The template can be further customized using EXPERIMENT_OPTIONS.
