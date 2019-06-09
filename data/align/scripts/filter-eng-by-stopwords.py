import re
import sys

f_stopwords = sys.argv[1]
STOP_SET = set(i.strip() for i in open(f_stopwords))


for line in sys.stdin:
    orig_ind_list = []
    out_tok_list = []
    for ind, tok in enumerate(line.strip().split()):
        if tok not in STOP_SET:
            orig_ind_list.append(ind)
            out_tok_list.append(tok)
    print ' '.join(out_tok_list)
    print >> sys.stderr, ' '.join(str(i) for i in orig_ind_list)
