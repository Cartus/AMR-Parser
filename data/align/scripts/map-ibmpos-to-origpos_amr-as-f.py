import re
import sys

'''
f_origpos is a file mapping to original pos in english
'''
f_origpos = sys.argv[1]
list_origpos = list(i.strip().split() for i in open(f_origpos))

line_no = 0
for line in sys.stdin:
    orig_pos_list = list_origpos[line_no]
    out_link_list = []
    for link in line.strip().split():
        ibmpos_f, ibmpos_e = link.split('-')
        out_link_list.append(ibmpos_f + '-' + orig_pos_list[ int(ibmpos_e) ] )
    print ' '.join(out_link_list)
    line_no += 1
