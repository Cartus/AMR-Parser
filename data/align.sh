#!/bin/bash

# CHANGE THIS
REPO_DIR=/home/cartus/Desktop/tbparser/data
JAMR_FILE=${REPO_DIR}/jamr_output/train.2015

# CONSTANT
JAMR_DIR=${REPO_DIR}/jamr_output


# REMOVE CERTAIN EDGES
python preprocess/remove_edges.py ${JAMR_FILE} ${REPO_DIR}/jamr.txt

# REORDER JAMR FILE
python preprocess/reorder_jamr.py ${REPO_DIR}/jamr.txt ${REPO_DIR}/jamr_rm.txt

# EXTRACT SENTENCES AND GRAPH FROM THE ALIGNMENT FILE
python preprocess/extract_pairs.py ${REPO_DIR}/jamr_rm.txt ${REPO_DIR}/sent.txt ${REPO_DIR}/unsupervised_align/eval/graph.txt
cp ${REPO_DIR}/sent.txt unsupervised_align/eval


# UNSUPERVISED ALIGN
cd unsupervised_align
./run.sh
cd ..


# RULE_BASED ALIGN
python preprocess/extract_align.py unsupervised_align/AMR_Aligned.keep aligned.txt
python preprocess/convert_format.py aligned.txt jamr_rm.txt aligned_jamr.txt
python preprocess/rearrange_align.py aligned_jamr.txt aligned_ra.txt
python preprocess/entity_align.py aligned_ra.txt aligned_en.txt
python preprocess/merge_file.py aligned_en.txt jamr_rm.txt sent.txt hybrid.txt
python preprocess/prune.py hybrid.txt hybrid_pr.txt
python preprocess/align2conll.py hybrid_pr.txt train.txt
java -jar AMROracle.jar -inp train.txt > train.transitions
rm aligned* hybrid*
rm jamr.txt jamr_rm.txt sent.txt train.txt


# DEV/TEST 
for SPLIT in dev test; do
    python preprocess/align2conll.py ${JAMR_DIR}/${SPLIT}.2014 ${SPLIT}.txt
    java -jar AMROracle.jar -inp ${SPLIT}.txt > ${SPLIT}.transitions
    rm ${SPLIT}.txt
    rm ${SPLIT}.txt.pb.lemmas
done
