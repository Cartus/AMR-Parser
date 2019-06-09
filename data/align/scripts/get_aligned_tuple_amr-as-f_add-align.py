import sys
from collections import defaultdict
'''
amr->f
eng->e

s__/__say-01 p__/__person p__:arg0-of h__/__have-org-role-91 l__:op1__"lorillard" h__:arg2 s2__/__spokeswoman s3__/__story s3__:domain t__/__this o2__/__old

0-3 3-2 4-1 6-2 7-10 9-6 10-9

'''

while True:
    line = sys.stdin.readline().strip()
    if not line:
        break
    split = line.split('\t')
    tuple_str = split[0]
    try:
        align_str = split[1]
    except:
        align_str = ''
    # e->f
    align_dict = defaultdict(set)
    for align in align_str.split():
        f, e = align.split('-')
        align_dict[int(f)].add(int(e))
    out = []
    tuple_list = tuple_str.split()
 
    for ind, tuple_one in enumerate(tuple_list):
        concept = tuple_one.split('__')[-1]
        if align_dict[ind]:
            out.append( tuple_one+'__'+'e.'+','.join(str(i) for i in align_dict[ind]) )
        elif concept in ['product','company','person', 'thing'] and ind+2 < len(tuple_list) and tuple_list[ind+1].split('__')[-1] in [':arg0-of', ':arg1-of', ':arg2-of'] and align_dict[ind+2]:
            out.append( tuple_one+'__'+'e.'+','.join(str(i) for i in align_dict[ind+2]) )
        elif ind-1>=0 and tuple_list[ind-1].split('__')[-1] in ['product','company','person', 'thing'] and concept in [':arg0-of', ':arg1-of', ':arg2-of'] and ind+1<len(tuple_list) and align_dict[ind+1]:
            out.append( tuple_one+'__'+'e.'+','.join(str(i) for i in align_dict[ind+1]) )
        
        else:
            out.append( tuple_one )
    print ' '.join(out)
