import sys

'''
Remove cycle edge and two edges to same child node
'''

input = sys.argv[1]
output = sys.argv[2]


def dfs(graph, node, visited):
    if node not in visited:
        visited.append(node)
        if node in graph.keys():
            for n in graph[node]:
                dfs(graph, n, visited)
    return visited


def correct_span(node_index, node_dict, all_span_list, start_index, end_index):
    parent_len = len(node_index)
    counter = 0
    backward = False
    for idx, name in node_dict.items():
        if '"' in name and idx[:parent_len] == node_index and len(idx) == parent_len+4:
            # print(name)
            counter += 1
    if counter == 0:
        for idx, name in node_dict.items():
            if '"' in name and idx[:parent_len] == node_index and len(idx) == parent_len + 2:
                # print(name)
                counter += 1
    end_index_count = int(start_index) + counter
    for idx in range(int(start_index), end_index_count):
        # print(idx)
        if idx in all_span_list:
            backward = True
            break
    if backward:
        forward = False
        start_index_count = int(end_index) - counter
        for idx in range(start_index_count, int(end_index)):
            # print(idx)
            if idx in all_span_list:
                # print(all_span_list)
                forward = True
                break
        if forward:
            span = 1
        else:
            span = str(start_index_count) + '-' + end_index
    else:
        span = start_index + '-' + str(end_index_count)
    # print(span)
    return span


with open(input) as f:
    align_file = f.readlines()
    
    
with open(output, 'w') as result_file:
    rm_entity = False 
    reent_max = 6
    merge_max = 11
    
    index = 0
    two_edges_set = set()
    cycle_set = set()
    date_reent_set = set()

    edge_list = list()
    all_edge_list = list()
    reent_list = list()
    entity_list = list()

    node_dict = dict()
    all_span_list = list()
    all_node_list = list()

    graph = dict()

    is_empty = False
    for line in align_file:
        if line.startswith('# ::id'):
            if '# ::id PROXY_AFP_ENG_20030624_0449.22 ::date 2013-07-26T14:31:43 ::snt-type body ::annotator SDL-AMR-09 ::preferred' in line:
                is_empty = True
                continue
            else:
                is_empty = False
            result_file.write('id:' + str(index) + '\n')
        elif line.startswith('# ::node'):
            if is_empty:
                continue
            node_list = line.strip().split('\t')
            node_index = node_list[1]
            node_name = node_list[2]
            if len(node_list) == 4:
                span = node_list[3]
                span_list = span.split('-')
                if int(span_list[1]) - int(span_list[0]) < merge_max:
                    for idx in range(int(span_list[0]), int(span_list[1])):
                        # print(idx)
                        all_span_list.append(idx)
            node_dict[node_index] = node_name
            all_node_list.append(line)

        elif line.startswith('# ::root'):
            if is_empty:
                continue
            root_line = line

        elif line.startswith('# ::edge'):
            if is_empty:
                continue

            cycle = False
            two_edges = False
            date_reent = False
            line_list = line.strip().split('\t')

            if line.strip() == '# ::edge	have-rel-role-91	ARG1	person	0.1.1.1.0	0.1.1.0':
                continue
            elif line.strip() == '# ::edge	temporal-quantity	unit	year	0.0.2.1.0.0	0.0.2.0.0.0.1':
                continue
            elif line.strip() == '# ::edge	more	op1	1000000000	0.1.0.1.0.1.0.0.1	0.1.0.1.0.1.0.0.0':
                continue
            elif line.strip() == '# ::edge	make-14	ARG1	1	0.1.1.0.2.1	0.1.0':
                continue
            elif line.strip() == '# ::edge	make-14	ARG0	i	0.1.1.0.2.1	0.0.0':
                continue

            relation = line_list[2]
            child_node = line_list[3]
            parent_index = line_list[4]
            child_index = line_list[5]
            edge_tuple = (parent_index, child_index)

            # Remove edge to the same child node.
            if edge_tuple in edge_list:
                print('Two edges to one child node')
                two_edges = True
                two_edges_set.add(index)
            else:
                edge_list.append(edge_tuple)

            # Remove cycle.
            if len(parent_index) > len(child_index):
                child_len = len(child_index)
                if parent_index[:child_len] == child_index:
                    print('Cycle')
                    cycle = True
                    cycle_set.add(index)

            # Remove reentrancy to the date-entity.
            if child_node == 'date-entity':
                parent_len = len(parent_index)
                if child_index[:parent_len] != parent_index:
                    print('Date-entity reentrancy')
                    date_reent = True
                    date_reent_set.add(index)

            # Find all reentrancy relations
            if len(parent_index) >= len(child_index):
                reent_list.append(line)
            else:
                parent_len = len(parent_index)
                if child_index[:parent_len] != parent_index:
                    reent_list.append(line)

            # Find all entities
            if relation == 'name' and child_node == 'name':
                entity_list.append(parent_index)

            if not cycle and not two_edges and not date_reent:
                all_edge_list.append(line)
                if parent_index not in graph:
                    graph[parent_index] = list()
                    graph[parent_index].append(child_index)
                else:
                    graph[parent_index].append(child_index)

        elif line.startswith('('):
            if is_empty:
                continue
            reent_num = 0
            real_span = ''
            for node in all_node_list:
                node_list = node.strip().split('\t')
                if len(node_list) == 4:
                    align_list = node_list[3].split('-')
                    span = int(align_list[1]) - int(align_list[0])
                    if span > merge_max:
                        node_index = node_list[1]
                        if real_span:
                            if real_span == 1:
                                new_string = node_list[0] + '\t' + node_list[1] + '\t' + node_list[2] + '\n'
                            else:
                                new_string = node_list[0] + '\t' + node_list[1] + '\t' + node_list[
                                    2] + '\t' + real_span + '\n'
                        else:
                            real_span = correct_span(node_index, node_dict, all_span_list, align_list[0], align_list[1])
                            if real_span == 1:
                                new_string = node_list[0] + '\t' + node_list[1] + '\t' + node_list[2] + '\n'
                            else:
                                new_string = node_list[0] + '\t' + node_list[1] + '\t' + node_list[
                                    2] + '\t' + real_span + '\n'
                        result_file.write(new_string)
                    else:
                        result_file.write(node)
                else:
                    result_file.write(node)

            result_file.write(root_line)

            remove_loop = False

            for edge in all_edge_list:
                edge_list = edge.strip().split('\t')

                parent_index = edge_list[4]
                child_index = edge_list[5]
                if edge in reent_list:
                    reent_num += 1
                    if reent_num > reent_max:
                        continue
                    if not remove_loop:
                        visited = dfs(graph, child_index, [])
                        if parent_index in visited:
                            print("Remove Loop...")
                            print(parent_index)
                            print(child_index)
                            remove_loop = True
                            continue
                if child_index in entity_list and edge in reent_list:
                    if rm_entity:
                        continue
                    else:
                        result_file.write(edge)
                else:
                    result_file.write(edge)

            edge_list = list()
            all_edge_list = list()
            reent_list = list()
            entity_list = list()

            node_dict = dict()
            all_node_list = list()
            all_span_list = list()

            graph = dict()

            index += 1
            result_file.write(line)
        else:
            if is_empty:
                continue
            result_file.write(line)
