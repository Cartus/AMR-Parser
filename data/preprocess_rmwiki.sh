#!/bin/bash

# CHANGE THIS
REPO_DIR=/home/cartus/Desktop/tbparser
DATA_DIR=${REPO_DIR}/data/amr

# CONSTANTS
PREPROC_DIR=${DATA_DIR}/tmp_amr
ORIG_AMR_DIR=${DATA_DIR}/data/amrs/split

#####
# CREATE FOLDER STRUCTURE

# mkdir ${PREPROC_DIR}
mkdir -p ${PREPROC_DIR}/train
mkdir -p ${PREPROC_DIR}/dev
mkdir -p ${PREPROC_DIR}/test

#####
# CONCAT ALL SEMBANKS INTO A SINGLE ONE
cat ${ORIG_AMR_DIR}/training/deft-p2-* > ${PREPROC_DIR}/train/raw_amrs.txt
cat ${ORIG_AMR_DIR}/dev/deft-p2-* > ${PREPROC_DIR}/dev/raw_amrs.txt
cat ${ORIG_AMR_DIR}/test/deft-p2-* > ${PREPROC_DIR}/test/raw_amrs.txt

# REMOVE WIKI 
for SPLIT in train dev test; do
    python preprocess/remove_redundant.py  ${PREPROC_DIR}/${SPLIT}/raw_amrs.txt  ${PREPROC_DIR}/${SPLIT}/raw_amrs_cache.txt
    python preprocess/remove_wiki.py ${PREPROC_DIR}/${SPLIT}/raw_amrs_cache.txt ${PREPROC_DIR}/${SPLIT}/amr.txt
    rm ${PREPROC_DIR}/${SPLIT}/raw_amrs.txt ${PREPROC_DIR}/${SPLIT}/raw_amrs_cache.txt
done
