#!/usr/bin/python

# Splits parallel English/AMR corpus in English and AMR input files (one sentence/AMR per line)

import sys

if len(sys.argv) != 2:
    print "Usage: python split_en_amr.py <file parallel English/AMR data>"
    sys.exit(0)

# English/AMR corpus file
input_file = sys.argv[1]

# For each sentence
block = []

# Store English sentences and AMR graphs
en = []
amr = []

with open(input_file, 'r+') as f:
    for line in f:
        # Get sentence
        if line.strip():
            block.append(line)
        # Parse each sentence
        else:
            tmp = []
            for line in block:
                if line.startswith('#'):
                    # Get English sentence
                    if line.startswith('# ::snt'):
                        line = line.replace('# ::snt ','')
                        en.append(line.strip())
                # Get AMR graph
                else:
                    tmp.append(line.strip())
            
            amr.append(' '.join(tmp))
            tmp = []
            block = []


# Write English file
with open('en.txt', 'ab') as out:
    out.write("\n".join(str(sentence) for sentence in en))

# Write AMR file
with open('amr.txt', 'ab') as out:
    out.write("\n".join(str(graph) for graph in amr))
