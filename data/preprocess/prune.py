import sys


hybrid_input = sys.argv[1]
output = sys.argv[2]

with open(hybrid_input) as f:
    align_file = f.readlines()

with open(output, 'w') as result_file:
    for line in align_file:
        #line = line.strip()
        if line.startswith('# ::node	0.0.0.0.0.0	1	2-3'):
            new_line = line.replace('# ::node	0.0.0.0.0.0	1	2-3', '# ::node	0.0.0.0.0.0	1')
            result_file.write(new_line)
        else:
            result_file.write(line)
            