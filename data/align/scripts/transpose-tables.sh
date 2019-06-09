cp *.a3.final atable.tmp
cp *.t3.final ttable.tmp
cp *.d3.final dtable.tmp

mv ttable.tmp scripts/cpp/t1
mv ttable.prev scripts/cpp/t0
mv atable.tmp scripts/cpp/a1
mv dtable.tmp scripts/cpp/d1
cd scripts/cpp/
g++ transpose-ttable.cpp
./a.out
g++ transpose-adtable.cpp
./a.out
rm t1 t0 a1 d1
mv ttable ../..
mv atable ../..
mv dtable ../..
cd ../..

mv ntable.prev ntable

mv *.d3.final dtable.prev
mv *.n3.final ntable.prev
mv *.a3.final atable.prev
mv *.t3.final ttable.prev

rm 114*
