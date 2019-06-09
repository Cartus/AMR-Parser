#!/usr/bin/python

# Extracts gold alignments only (without # ::id etc)

import sys

if len(sys.argv) != 2:
    print "Usage: python extract_gold.py <file gold alignments>"
    sys.exit(0)

gold_alignments = open(sys.argv[1])
gold = []

# Get ISI alignments
for line in gold_alignments:
    if line.startswith('# ::alignments'):
        line = line.replace('# ::alignments ', '')
        gold.append(line.strip().split())

with open('gold.keep', 'ab') as out:
    for line in gold:
        out.write(' '.join(line)+'\n')