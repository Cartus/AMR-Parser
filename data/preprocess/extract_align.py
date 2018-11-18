import sys
import re

relation_set = {':prep-following', ':prep-through', ':prep-within', ':prep-instead-of', ':prep-except', ':consist', ':prep-versus', ':value-of', ':subset-of', ':year2', ':arg6', ':arg7', ':arg8', ':arg9', ':arg5-of', ':quarter', ':name-of', ':medium-of', ':prep-along-with', ':prep-into', ':prep-out-of', ':age-of', ':prep-amid', ':prep-toward', ':prep-under', ':accompanier-of', ':conj-as-if', ':timezone', ':op1-of', ':destination-of', ':prep-by', ':purpose-of', ':scale', ':beneficiary-of', ':prep-on-behalf-of', ':prep-among', ':frequency-of', ':prep-for', ':prep-against', ':direction-of', ':ord-of', ':prep-in-addition-to', ':decade', ':prep-with', ':era', ':century', ':prep-on', ':extent-of', ':prep-to', ':prep-as', ':prep-in', ':medium', ':condition-of', ':snt6', ':beneficiary', ':extent', ':snt10', ':duration', ':path-of', ':accompanier', ':arg3-of', ':calendar', ':prep-at', ':mod', ':purpose', ':domain-of', ':snt11', ':example', ':op10', ':op19', ':path', ':time', ':location', ':domain', ':part', ':source', ':arg2-of', ':concession', ':op7', ':manner', ':degree-of', ':snt5', ':source-of', ':arg0-of', ':op3', ':destination', ':compared-to', ':frequency', ':arg0', ':poss-of', ':part-of', ':range', ':snt1', ':poss', ':quant-of', ':arg1', ':op6', ':consist-of', ':op1', ':snt4', ':subevent', ':topic', ':season', ':arg1-of', ':manner-of', ':arg5', ':op8', ':snt9', ':name', ':prep-from', ':instrument-of', ':op20', ':op11', ':snt8', ':instrument', ':op12', ':op18', ':age', ':op17', ':ord', ':op4', ':snt2', ':op5', ':op2', ':op9', ':weekday', ':example-of', ':duration-of', ':arg2', ':polarity', ':direction', ':op16', ':month', ':dayperiod', ':year', ':op13', ':location-of', ':op15', ':snt3', ':arg4', ':subevent-of', ':day', ':arg3', ':value', ':polite', ':li', ':snt7', ':op14', ':topic-of', ':prep-without', ':quant', ':degree', ':time-of', ':concession-of', ':unit', ':arg4-of', ':condition', ':mode'}
special_set = {'imperative', 'interrogative', 'expressive'}

input = sys.argv[1]
output = sys.argv[2]

with open(input) as f:
    lines = f.readlines()

with open(output, 'w') as result_file:
    index = 1
    for line in lines:
        if line.startswith('#'):
            result_file.write('id:{}'.format(index) + '\n')
            result_file.write(line)
            continue
        elif line == '\n':
            index += 1
            result_file.write('\n')
        else:
            node_list = line.split(' ')
            # print(node_list)
            for node in node_list:
                # print(node)
                if '(' in node and ')' not in node:
                    continue
                elif node in relation_set:
                    continue
                elif node == '/':
                    is_node = True
                    continue
                else:
                    # print(node)
                    if is_node:
                        if '~' in node:
                            node_align = node.split('~')
                            if node_align[0] in relation_set:
                                continue
                            node_name = node_align[0]
                            align = node_align[1].split('.')[1]
                            if ')' in align:
                                # print(align)
                                bracket_loc = align.find(')')
                                align = align[:bracket_loc]
                            result_file.write(node_name + '\t' + align + '-' + str(int(align) + 1) + '\n')
                        else:
                            if ')' in node:
                                bracket_loc = node.find(')')
                                node = node[:bracket_loc]
                            result_file.write(node + '\n')

                        is_node = False
                    else:
                        if ')' in node and '(' not in node:
                            # print(node)
                            bracket_loc = node.find(')')
                            node = node[:bracket_loc]
                        match = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', node)
                        if '~' in node or '"' in node or '-' in node or match or node in special_set:
                            # print(node)
                            if '~' in node:
                                node_align = node.split('~')
                                if node_align[0] in relation_set:
                                    continue
                                node_name = node_align[0]
                                align = node_align[1].split('.')[1]
                                if ')' in align:
                                    # print(align)
                                    bracket_loc = align.find(')')
                                    align = align[:bracket_loc]
                                result_file.write(node_name + '\t' + align + '-' + str(int(align) + 1) + '\n')
                            else:
                                if ')' in node:
                                    bracket_loc = node.find(')')
                                    node = node[:bracket_loc]
                                result_file.write(node + '\n')