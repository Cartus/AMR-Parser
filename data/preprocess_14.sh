#!/bin/bash

DATA_DIR=amr

# CONSTANTS
PREPROC_DIR=${DATA_DIR}/tmp_amr
ORIG_AMR_DIR=${DATA_DIR}/data/amrs/split

#####
# CREATE FOLDER STRUCTURE

mkdir -p ${PREPROC_DIR}/train
mkdir -p ${PREPROC_DIR}/dev
mkdir -p ${PREPROC_DIR}/test

#####
# CONCAT ALL SEMBANKS INTO A SINGLE ONE
cat ${ORIG_AMR_DIR}/training/amr-release-* > ${PREPROC_DIR}/train/raw_amrs.txt
cat ${ORIG_AMR_DIR}/dev/amr-release-* > ${PREPROC_DIR}/dev/raw_amrs.txt
cat ${ORIG_AMR_DIR}/test/amr-release-* > ${PREPROC_DIR}/test/raw_amrs.txt

# REMOVE REDUNDANT SENT(# AMR release; corpus) 
for SPLIT in train dev test; do
    python preprocess/remove_redundant.py ${PREPROC_DIR}/${SPLIT}/raw_amrs.txt ${PREPROC_DIR}/${SPLIT}/amr.txt
    rm ${PREPROC_DIR}/${SPLIT}/raw_amrs.txt
done
