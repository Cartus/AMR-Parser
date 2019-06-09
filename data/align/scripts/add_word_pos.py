import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        print
    else:
        print ' '.join(word + '_' + str(pos) for pos, word in enumerate(line.split())) 
