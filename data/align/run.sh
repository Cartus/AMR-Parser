. ./addresses.keep
DATA_DIR=./data/
SCRIPT_DIR=./scripts/

# preprocess
cp $ENG tmpeng.txt
cp $AMR tmpamr.txt
tr [:upper:] [:lower:] < $ENG > tmp
mv tmp $ENG
tr [:upper:] [:lower:] < $AMR > tmp
mv tmp $AMR
cat $ENG | python -u $SCRIPT_DIR/filter-eng-by-stopwords.py $DATA_DIR/ENG_stopwords.txt > tmp.eng.tok.filtered.txt 2>tmp.eng.tok.origpos.txt
cat tmp.eng.tok.filtered.txt | python -u $SCRIPT_DIR/stem-4-letters.py > tmp.eng.tok.stemmed.txt
cat $AMR | python $SCRIPT_DIR/get_lineartok_with_rel.py $DATA_DIR/AMR_stopwords.txt > tmp.amr_linear.txt 2>tmp.amr_tuple.txt 
while read line ; do echo $line | tr ' ' '\n' | sed 's/\-[0-9]\{2,3\}$//g' | sed 's/"//g' | python -u $SCRIPT_DIR/stem-4-letters.py | tr '\n' ' ' ; echo ; done < tmp.amr_linear.txt > tmp.amr_linear.stemmed.txt
python $SCRIPT_DIR/get_id_mapping_uniq.py tmp.eng.tok.stemmed.txt tmp.amr_linear.stemmed.txt > tmp.id.txt
cp tmp.id.txt tmp.id.eng.txt
cat $DATA_DIR/prep-roles.id.txt | cut -d ' ' -f 2 | python -u $SCRIPT_DIR/stem-4-letters.py >> tmp.id.eng.txt
cat $DATA_DIR/myidmap.eng | python -u $SCRIPT_DIR/stem-4-letters.py >> tmp.id.eng.txt
for i in `seq 1 10` ; do cat tmp.id.eng.txt ; done >> tmp
mv tmp tmp.id.eng.txt
cat tmp.eng.tok.stemmed.txt tmp.id.eng.txt > en
cp tmp.id.txt tmp.id.amr.txt
cat $DATA_DIR/prep-roles.id.txt | cut -d ' ' -f 1 | python -u $SCRIPT_DIR/stem-4-letters.py >> tmp.id.amr.txt
cat $DATA_DIR/myidmap.fr | python -u $SCRIPT_DIR/stem-4-letters.py >> tmp.id.amr.txt
for i in `seq 1 10` ; do cat tmp.id.amr.txt ; done >> tmp
mv tmp tmp.id.amr.txt
cat tmp.amr_linear.stemmed.txt tmp.id.amr.txt > fr

# get alignments
sh $SCRIPT_DIR/run_aligner.sh

#postprocess
lines_number=$(wc -l < $AMR)
head -n $lines_number align > tmp.align.real.txt
cat tmp.align.real.txt | python $SCRIPT_DIR/map-ibmpos-to-origpos_amr-as-f.py tmp.eng.tok.origpos.txt > tmp.align.origpos.txt
paste tmp.amr_tuple.txt tmp.align.origpos.txt | python $SCRIPT_DIR/get_aligned_tuple_amr-as-f_add-align.py > tmp.aligned_tuple.txt
paste $AMR tmp.aligned_tuple.txt | python $SCRIPT_DIR/feat2tree_v9.py --align >tmp.align.ulf.txt 2>tmp.align.ulf.err 
cat $ENG | python $SCRIPT_DIR/add_word_pos.py > tmp.eng.viz.txt
count=0
while [ "$count" -ne $lines_number ]
do
  read eng_line
  echo '#' $eng_line
  count=$(( $count+1 ))
  awk NR==$count tmp.align.ulf.txt
  echo
done <tmp.eng.viz.txt > AMR_Aligned.keep

g++ $SCRIPT_DIR/cpp/get_alignments.cpp
./a.out

#clean
mv tmpeng.txt $ENG
mv tmpamr.txt $AMR
find . -maxdepth 1 -type f -not -name '*.keep' -not -name '*.sh' | xargs rm
