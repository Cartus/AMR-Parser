import sys

input = sys.argv[1]
output = sys.argv[2]

with open(input) as f:
    lines = f.readlines()

with open(output, 'w') as result_file:
    all_node_list = []
    cache_node_list = []
    index_list = []
    index_cache = ''
    start_index = ''
    is_break = False
    is_continue = False
    is_added = False
    have_break = False
    counter = -1
    for line in lines:
        if line.startswith('id:'):
            counter += 1
            result_file.write(line)
            all_node_list = []
            cache_node_list = []
            index_list = []
            index_cache = ''
            is_break = False
            is_continue = False
            is_added = False
            have_break = False
        elif line.startswith('# ::node') or line.startswith('# ::root'):
            line_list = line.split('\t')
            index = line_list[1]
            if not is_break:
                if not is_continue:
                    if index[-2:] == '10' and index_list[-1][-1:] != '9':
                        is_break = True
                        have_break = True
                        cache_node_list.append(line)
                        index_cache = index
                    else:
                        # print(line)
                        all_node_list.append(line)
                        index_list.append(index)
                        if index[-1] == '9' and have_break:
                            is_continue = True
                            index_cache = index
                else:
                    # print(line)
                    prev_index_len = len(index_cache)
                    if len(index) > prev_index_len and index[:prev_index_len] == index_cache:
                        all_node_list.append(line)
                        index_list.append(index)
                    else:
                        if len(cache_node_list):
                            print(counter)
                        all_node_list.extend(cache_node_list)
                        all_node_list.append(line)
                        index_list.append(index)
                        is_continue = False
            else:
                prev_index_len = len(index_cache)
                if len(index) > prev_index_len and index[:prev_index_len] == index_cache:
                    cache_node_list.append(line)
                elif index[-2:] in ('11', '12', '13', '14', '15', '16', '17', '18', '19'):
                    cache_node_list.append(line)
                    index_cache = index
                else:
                    is_break = False
                    all_node_list.append(line)
                    index_list.append(index)

        else:
            if line.startswith('# ::edge'):
                if not is_added:
                    for node in all_node_list:
                        result_file.write(node)
                    is_added = True
                    result_file.write(line)
                else:
                    result_file.write(line)
            else:
                if line.startswith('('):
                    if not is_added:
                        for node in all_node_list:
                            result_file.write(node)
                        is_added = True
                        result_file.write(line)
                    else:
                        result_file.write(line)
                else:
                    result_file.write(line)

    # for node in all_node_list:
    #     print(node)
