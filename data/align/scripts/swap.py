import sys
for line in sys.stdin:
    l = line.strip().split()
    newl = []
    for i in l:
        pos1, pos2 = i.split('-')
        newl.append(pos2 + '-' + pos1)
    print ' '.join(newl)
