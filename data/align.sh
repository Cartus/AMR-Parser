#!/bin/bash


# CONSTANT
JAMR_FILE=jamr_output/train.txt
JAMR_DIR=jamr_output

# REMOVE CERTAIN EDGES
python preprocess/remove_edges.py ${JAMR_FILE} jamr.txt

# REORDER JAMR FILE
python preprocess/reorder_jamr.py jamr.txt jamr_rm.txt

# EXTRACT SENTENCES AND GRAPH FROM THE ALIGNMENT FILE
python preprocess/extract_pairs.py jamr_rm.txt sent.txt align/eval/graph.txt
cp sent.txt align/eval


# UNSUPERVISED ALIGN
cd align
./run.sh
cd ..


# RULE_BASED ALIGN
python preprocess/extract_align.py align/AMR_Aligned.keep aligned.txt
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
    python preprocess/align2conll.py ${JAMR_DIR}/${SPLIT}.txt ${SPLIT}.txt
    java -jar AMROracle.jar -inp ${SPLIT}.txt > ${SPLIT}.transitions
    rm ${SPLIT}.txt
    rm ${SPLIT}.txt.pb.lemmas
done
