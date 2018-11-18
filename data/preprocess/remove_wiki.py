import sys

input = sys.argv[1]
output = sys.argv[2]

with open(input) as f:
    lines = f.readlines()

with open(output, 'w') as result_file:
    for line in lines:
        first_line = False
        if line.startswith('('):
            first_line = True
        if ':wiki' in line:
            # print(line)
            wiki_child = False
            blank_num = line.find(':')
            line_list = line.strip().split(' ')
            ins_list = list()
            for ele in line_list:
                if not wiki_child:
                    if ele == ':wiki':
                        wiki_child = True
                    else:
                        ins_list.append(ele)
                else:
                    wiki_child = False
                    if ele.count(')') > ele.count('('):
                        ins_list.append(ele.count(')')*')')
                    continue
            if first_line:
                string = ''
            else:
                string = blank_num * ' '
            for item in ins_list:
                # print(item)
                string += item + ' '
            result_file.write(string+'\n')
        else:
            result_file.write(line)