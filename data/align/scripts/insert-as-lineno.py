import sys

insert_content = sys.stdin.read()[:-1]
file = sys.argv[1]
insert_as_lineno = int(sys.argv[2])

orig_list = open(file).read()[:-1].split('\n')

#TODO: handle case of inserting to empty file
if insert_as_lineno <= 0 or insert_as_lineno >= len(orig_list)+2:
    print >> sys.stderr, 'invalid target line number, do not trust this output'

orig_list.insert(insert_as_lineno-1, insert_content)
print '\n'.join(orig_list)
