from feat2tree_v9 import *
import sys

"""
for input with named entities:

(c2 / company :name (n2 / name :op1 "property" :op2 "insurance" :op3 "co." :op4 "of" :op5 "picc"))

company is the ne type, should be stopword
name in (.. / name ..) is dummy concept, should be stopword

"""
f2 = open('amrorig.txt','w')
ind = -1

def getterminal_except_ne(amr, nt_list):
    global ind
    if (not amr.feats):
        ind = ind+1
        if (amr.val not in [nt.val for nt in nt_list]):
            f2.write(str(ind)+' ')
            return [(amr.pi.val, amr.pi_edge, amr.val)]
    ret = []
    for f in amr.feats:
        ind = ind+1
        if f.edge == INSTANCE:
            # as "company" in the context of ".. / company :name (.."
            if ':name' in [ff.edge for ff in amr.feats]:
                continue
            if f.node.val == 'name' and f.node.pi.pi_edge == ':name':
                continue
            if f.node.val in STOP_SET:
                continue
            ret.append((amr.val, INSTANCE, f.node.val))
            f2.write(str(ind)+' ')
        else:
            if f.edge not in STOP_SET:
                ret.append((amr.val, f.edge))
                f2.write(str(ind)+' ')
            ret.extend(getterminal_except_ne(f.node, nt_list))
    return (ret)

if __name__ == '__main__':

    f_stopwords = sys.argv[1]
    STOP_SET = set(i.strip() for i in open(f_stopwords))

    count = 0
    while True:
        #TODO: lowercasing in wrapper sh, not here
        line = sys.stdin.readline().strip().lower()
        if not line:
            break
        count += 1
        #print 'line', count
        _, amr = input_amrparse(line)
        t_list = getterminal_except_ne(amr, amr.get_nonterm_nodes())
        #print t_list
        print ' '.join(i[-1] for i in t_list)
        print >> sys.stderr, ' '.join('__'.join(i) for i in t_list)
	f2.write('\n')
        ind = -1
