#!/usr/bin/python

# Sorts gold alignments (one alignment per line) by word indices, used to experiment with partial evaluation scores

import sys
import collections
import itertools

if len(sys.argv) != 2:
    print "Usage: python sort_align.py <file gold alignments>"
    sys.exit(0)

isi_align = open(sys.argv[1])
isi = []

# Get ISI alignments
for line in isi_align:
    isi.append(line.strip().split())

for alignment in isi:
    tmp_seq = []
    tmp_key = []
    for seq in alignment:
        key = seq.split('-')[0]
        tmp_seq.append(seq)
        tmp_key.append(int(key))

    tmp = dict(zip(tmp_key,tmp_seq))
    tmp_sorted = dict(sorted(tmp.iteritems()))
    
    with open('sorted_alignments.keep', 'ab') as out:
        out.write(' '.join(tmp_sorted.values())+'\n')
