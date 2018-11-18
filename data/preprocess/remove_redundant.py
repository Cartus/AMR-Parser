import sys

input = sys.argv[1]
output = sys.argv[2]

with open(input) as f:
    lines = f.readlines()

with open(output, 'w') as result_file:
    counter = 0
    string = ''
    for line in lines:
        # print(line)
        if line.startswith('# AMR release;'):
            continue
        if line.startswith('# ::'):
            if line.startswith('# ::id'):
                string += '# ::id:'+str(counter)+'\n'
            else:
                if '-_-' in line:
                    new_string = line.replace(' -_-', '.')
                    string += new_string
                else:
                    string += line
        else:
            if line.startswith('(a / amr-empty)'):
                string = ''
            elif '"Republican Party"' in line:
                new_string = line.replace('"Republican Party"', '"Republican" :op2 "Party"')
                string += new_string
            elif '"Soviet Union"' in line:
                new_string = line.replace('"Soviet Union"', '"Soviet" :op2 "Union"')
                string += new_string
            elif '"United States"' in line:
                new_string = line.replace('"United States"', '"United" :op2 "States"')
                string += new_string
            elif '"Middle East"' in line:
                new_string = line.replace('"Middle East"', '"Middle" :op2 "East"')
                string += new_string
            elif '"JP Morgan"' in line:
                new_string = line.replace('"JP Morgan"', '"JP" :op2 "Morgan"')
                string += new_string
            elif '"United Kingdom"' in line:
                new_string = line.replace('"United Kingdom"', '"United" :op2 "Kingdom"')
                string += new_string
            elif '"MHC 51 Osprey"' in line:
                new_string = line.replace('"MHC 51 Osprey"', '"MHC" :op2 "51" :op3 "Ospery"')
                string += new_string
            elif ':op1 "LSD" :op2 41' in line:
                new_string = line.replace(':op2 41', ':op2 "41"')
                string += new_string
            elif line == '\n':
                if string:
                    result_file.write(string+'\n')
                    counter += 1
                string = ''
            else:
                string += line