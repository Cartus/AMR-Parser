import sys


hybrid_input = sys.argv[1]
jamr_input = sys.argv[2]
sent_input = sys.argv[3]
output = sys.argv[4]

with open(hybrid_input) as f:
    align_file = f.readlines()

with open(jamr_input) as f:
    jamr_file = f.readlines()
    
with open(sent_input) as f:
    tok_file = f.readlines()

with open(output, 'w') as result_file:
    node_list = []
    for line in align_file:
        line = line.strip()
        if line.startswith('#'):
            continue
        elif line.startswith('id:'):
            instance_dict = []
        elif not line:
            node_list.append(instance_dict)
        else:
            line = line.split('\t')
            if len(line) > 2:
                instance_dict.append((line[0], line[1], line[2]))
            else:
                instance_dict.append((line[0], line[1]))

    sent_list = []
    for line in tok_file:
        line = line.strip()
        sent_list.append(line)

    keep = False
    index = -1

    manual_fix = False
    for line in jamr_file:
        # line = line.strip()
        if line.startswith('# ::snt'):
            if line.startswith('# ::snt BP and such British companies are already in Libya'):
                manual_fix = True
            elif line.startswith('# ::snt COD4 to me was the best real-war based FPS...'):
                manual_fix = True
            elif line.startswith('# ::snt Provide examples of how they'):
                manual_fix = True
            elif line.startswith('# ::snt Indeed there was a plot to Kamikaze attack the surrender ceremony'):
                manual_fix = True
            elif line.startswith('# ::snt <a href="http://www.summitdaily.com/article/20101108/NEWS'):
                manual_fix = True
            elif line.startswith('# ::snt The problem with that thinking is that you'):
                manual_fix = True
            elif line.startswith("# ::snt Safdar Sadiqui's son was"):
                manual_fix = True
            elif line.startswith('# ::snt I am happy with the evil and Orwellian'):
                manual_fix = True
            elif line.startswith('# ::snt The MiG-25 fired an AAM'):
                manual_fix = True
            elif line.startswith('# ::snt Children of the rich and government officials'):
                manual_fix = True
            result_file.write(line)
            line = line.split(' ')
            if len(line) > 100:
                keep = True
            index += 1
            counter = 0

        elif line.startswith('# ::node'):
            if keep:
                result_file.write(line)
            else:
                result_file.write('# ::node' + '\t')
                # print(node_list)
                node_tuple = node_list[index][counter]
                if len(node_tuple) > 2:
                    if manual_fix and line.startswith('# ::node	0.1	be-located-at-91'):
                        result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\t' + '8-9' + '\n')
                        manual_fix = False
                    elif manual_fix and line.startswith('# ::node	0	game'):
                        result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\t' + '0-1' + '\n')
                        manual_fix = False
                    elif manual_fix and line.startswith('# ::node	0.2	thing') or line.startswith('# ::node	0.2.0	thing'):
                        result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\t' + '1-2' + '\n')
                        manual_fix = False
                    elif manual_fix and line.startswith('# ::node	0.2.0.0.0	-') or line.startswith('# ::node	0.2.0.0	thing'):
                        result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\t' + '6-7' + '\n')
                        manual_fix = False
                    elif manual_fix and line.startswith('# ::node	0.0.0.2.0	person'):
                        result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\n')
                        manual_fix = False
                    elif manual_fix and line.startswith('# ::node	0.1.1.1	have-org-role-91'):
                        result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\n')
                        manual_fix = False
                    elif manual_fix and line.startswith('# ::node	0.1.1.1	temporal-quantity'):
                        result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\t' + '10-11' + '\n')
                        manual_fix = False
                    elif manual_fix and line.startswith('# ::node	0	be-located-at-91'):
                        result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\t' + '5-6' + '\n')
                        manual_fix = False
                    elif manual_fix and line.startswith('# ::node	0.0.1	i'):
                        result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\t' + '0-1' + '\n')
                        manual_fix = False
                    elif manual_fix and line.startswith('# ::node	0.1	missile'):
                        result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\t' + '6-7' + '\n')
                        manual_fix = False
                    elif manual_fix and line.startswith('# ::node	0.1.1	person'):
                        result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\n')
                        manual_fix = False
                    else:
                        result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\t' + node_tuple[2] + '\n')
                else:
                    result_file.write(node_tuple[0] + '\t' + node_tuple[1] + '\n')
                counter += 1
        # elif line.startswith('# ::id'):
        elif line.startswith('id'):
            result_file.write(line)
            keep = False
        elif line.startswith('# ::tok'):
            result_file.write('# ::tok ')
            result_file.write(sent_list[index] + '\n')
        else:
            result_file.write(line)
