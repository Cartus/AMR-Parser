import sys

f1, f2 = sys.argv[1], sys.argv[2]

common = set()
for line1, line2 in zip(open(f1), open(f2)):
    l1 = line1.strip().split()
    l2 = line2.strip().split()
    common |= set(line1.strip().split()) & set(line2.strip().split())
if common:
    print '\n'.join(common)

