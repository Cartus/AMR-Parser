#!/usr/bin/python

# Used to preprocess English, switched to using Publish_Version code for final version

import sys
import re

if len(sys.argv) != 2:
    print "Usage: python prep_en.py <file English data>"
    sys.exit(0)

en = open(sys.argv[1], 'r')
en_stopwords = open('../../data/ENG_stopwords.txt','r')

## Lowercasing
def lowercasing():
    global en
    en = [line.lower() for line in en]

## Filter English stopwords
def filter_en_stopwords():
    stop_en = set(word.strip() for word in en_stopwords)

    for line in en:
        orig_ind_en = []
        out_tok_en = []
        # Record word and index
        for index, token in enumerate(line.strip().split()):
            if token not in stop_en:
                orig_ind_en.append(index)
                out_tok_en.append(token)
        with open('_en_tok_filtered.txt', 'ab') as out:
        	out.write(' '.join(out_tok_en)+'\n')
    	with open('_en_tok_orig.txt', 'ab') as out:
    		out.write(' '.join(str(index) for index in orig_ind_en)+'\n')

## Stem filtered English words
def stem_en_filtered_words():
    with open('_en_tok_filtered.txt', 'r') as f:
        for line in f:
            stemmed_en = []
            for token in line.strip().split():
                if token.startswith(':') or token.startswith('++') and token.endswith('++'):
                    stemmed_en.append(token)
                else: 
                    token = token[:4]
                    stemmed_en.append(token)
            with open('_en_tok_stemmed.txt', 'ab') as out:
                out.write(' '.join(stemmed_en)+'\n')


if __name__ == '__main__':
    lowercasing()
    filter_en_stopwords()
    stem_en_filtered_words()



