import sys

ul_input = sys.argv[1]
jamr_input = sys.argv[2]
output = sys.argv[3]

with open(ul_input) as f:
    align_lines = f.readlines()

with open(jamr_input) as f:
    jamr_lines = f.readlines()

with open(output, 'w') as result_file:
    jamr_list = []
    for line in jamr_lines:
        if line.startswith('# ::node'):
            line = line.split('\t')
            ins_list.append(line[1])
        elif line.startswith('# ::snt'):
            ins_list = []
        elif line == "\n":
            jamr_list.append(ins_list)
        else:
            continue

    ins_index = -1
    counter = 0
    id = 0
    for line in align_lines:
        if line.startswith('id:'):
            result_file.write('id:' + str(id) + '\n')
            id = int(id) + 1
            ins_index += 1
            counter = 0
        elif line.startswith('#'):
            result_file.write(line)
        elif line == "\n":
            result_file.write(line)
        else:
            line = line.split('\t')
            if len(line) > 1:
                result_file.write(jamr_list[ins_index][counter] + '\t' + line[0] + '\t' + line[1])
            else:
                result_file.write(jamr_list[ins_index][counter] + '\t' + line[0])
            counter += 1