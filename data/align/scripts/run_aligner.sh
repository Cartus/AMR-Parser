. ./addresses.keep
CONFIG_DIR=./config/
SCRIPT_DIR=./scripts/

SRC_FILE=`ls fr`
TRG_FILE=`ls en`
$MGIZA_BIN/plain2snt $SRC_FILE $TRG_FILE
$MGIZA_BIN/mkcls -p$SRC_FILE -V$SRC_FILE.vcb.classes
$MGIZA_BIN/mkcls -p$TRG_FILE -V$TRG_FILE.vcb.classes
$MGIZA_BIN/snt2cooc "$SRC_FILE"_"$TRG_FILE".cooc $SRC_FILE.vcb $TRG_FILE.vcb "$SRC_FILE"_"$TRG_FILE".snt

SRC_FILE=`ls en`
TRG_FILE=`ls fr`
$MGIZA_BIN/plain2snt $SRC_FILE $TRG_FILE
$MGIZA_BIN/mkcls -p$SRC_FILE -V$SRC_FILE.vcb.classes
$MGIZA_BIN/mkcls -p$TRG_FILE -V$TRG_FILE.vcb.classes
$MGIZA_BIN/snt2cooc "$SRC_FILE"_"$TRG_FILE".cooc $SRC_FILE.vcb $TRG_FILE.vcb "$SRC_FILE"_"$TRG_FILE".snt

rm ???-??-??.*
$MGIZA_BIN/mgiza  $CONFIG_DIR/giza.config.0.f -ncpu 1 > log.txt
cp *.A3.final.* giza-align.txt
cp *.a3.final atable.prev
cp *.t3.final ttable.prev
cp *.hhmm.5 htable
cp *.hhmm.5.alpha htable.alpha
cp *.hhmm.5.beta htable.beta
cp *.d3.final dtable.prev
cp *.n3.final ntable.prev


rm ???-??-??.*
$MGIZA_BIN/mgiza  $CONFIG_DIR/giza.config.0.b -ncpu 1 > log.txt
cp *.hhmm.5 htable2
cp *.hhmm.5.alpha htable2.alpha
cp *.hhmm.5.beta htable2.beta

for i in {1..2}
do

sh $SCRIPT_DIR/transpose-tables.sh
rm ???-??-??.*
$MGIZA_BIN/mgiza  $CONFIG_DIR/giza.config.f -ncpu 1 > log.txt
sh $SCRIPT_DIR/transpose-tables.sh
rm ???-??-??.*
$MGIZA_BIN/mgiza  $CONFIG_DIR/giza.config.b -ncpu 1 > log.txt

done

sh $SCRIPT_DIR/transpose-tables.sh
rm ???-??-??.*
$MGIZA_BIN/mgiza  $CONFIG_DIR/giza.config.f -ncpu 1 > log.txt

cp *.A3.final.* giza-align.txt
cat giza-align.txt | python $SCRIPT_DIR/giza2isi.py | python $SCRIPT_DIR/swap.py > align
