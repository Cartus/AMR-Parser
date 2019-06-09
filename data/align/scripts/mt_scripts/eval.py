#!/usr/bin/python

# Evaluates computed alignments against gold alignments
# Outputs precision, recall, and F1 scores

from __future__ import division
import sys

if len(sys.argv) != 3:
    print "Usage: python eval.py <file computed alignments> <file gold alignments>"
    sys.exit(0)

isi_alignment = open(sys.argv[1])
gold_alignment = open(sys.argv[2])

isi = []
gold = []

precision_scores = []
recall_scores = []

# Get computed alignments
for line in isi_alignment:
    isi.append(line.strip().split())

# Get gold alignments
for line in gold_alignment:
    gold.append(line.strip().split())

# Compute scores
for i, g in zip(isi, gold):
    isi_set = set(i)
    gold_set = set(g) 
    intersection = len(set.intersection(isi_set,gold_set))

    precision_scores.append(intersection/len(isi_set))
    recall_scores.append(intersection/len(gold_set))

precision = sum(precision_scores)/len(precision_scores)
recall = sum(recall_scores)/len(recall_scores)
f1 = (2*precision*recall) / (precision+recall)

print 'Precision:\t', ("%.4f" % round(precision,4))
print 'Recall:\t\t', ("%.4f" % round(recall,4))
print 'F1:\t\t', ("%.4f" % round(f1,4))
