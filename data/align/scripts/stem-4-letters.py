import re
import sys

'''
remove ulf-style alignment label for amr-english align
'''

for line in sys.stdin:
    #print ' '.join(w if w.startswith(':') or (w.startswith('++') and w.endswith('++')) else str(int(len(w)/3))+'dg' if (len(w) > 6 and w[-4:] == '0000' and w.isdigit()) else 'fpdg' if (w.replace('.','',1).isdigit() and not w.isdigit()) else w[:4] for w in line.strip().split())
    print ' '.join(w if w.startswith(':') or (w.startswith('++') and w.endswith('++')) else w[:3] for w in line.strip().split())
