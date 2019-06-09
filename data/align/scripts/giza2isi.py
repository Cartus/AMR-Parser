import sys

for line in sys.stdin:
    l = line.strip().split()
    print ' '.join( l[ind] + '-' + l[ind+1] for ind in range(0, len(l)-1, 2) )
