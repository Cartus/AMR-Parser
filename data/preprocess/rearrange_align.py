import collections
import re
import sys

abs_set = {'person', 'man', 'aircraft', 'date-entity', 'government-organization', 'political-party', 'product-of', 'multiple', 'criminal-organization', 'ethnic-group', 'religious-group', 'email-address-entity', 'have-subevent-91', 'be-temporally-at-91', 'be-destined-for-91', 'street-address-91', 'score-entity', 'byline-91', 'phone-number-entity', 'ordinal-entity', 'url-entity', 'have-frequency-91', 'have-quant-91', 'be-located-at-91', 'relative-position', 'temperature-quantity', 'seismic-quantity', 'energy-quantity', 'numerical-quantity', 'area-quantity', 'distance-quantity', 'volume-quantity', 'have-org-role-91', 'mass-quantity', 'monetary-quantity', 'temporal-quantity', 'percentage-entity', 'power-quantity','railway-line','airport','club','ocean','sports-facility','show','aircraft-type','war','worm','channel','university','book','military','magazine','animal','peninsula','department','bank','car-make','hospital','city-district','natural-disaster','medicine','network','newspaper','valley','band','city','ship','palace','person','school','spaceship','treaty','operation','planet','movie','street','district','company','bay','earthquake','journal','family','event','publication','language','republic','hotel','mountain','agency','moon','road','initiative','system','name','island','game','disease','station','lawyer','park','local-region','research-institute','country','doctor','worship-place','building','organization','seminar','music','river','rocket','dynasty','vehicle','county','incident','state','world-region','range','province','thing','country-region','law','broadcast-program','capital','continent','facility','revolution','conference','location','page','date-entity','territory','man','sea','product','award','pass','destroyer','ethnic-group','son','plane','television','mission','drug','meet-03','government-organization','strait','political-party','missile','league','program','criminal-organization','group','project','religious-group','team','radio','museum','husband','festival'}
children_set = {'more', 'most', '-'}


def find_parent_node(node_idx, ins_dict):
    parent_info = list()
    for index, info in ins_dict.items():
        if len(index) + 2 == len(node_idx):
            par_len = len(index)
            if index == node_idx[:par_len]:
                parent_info = info

    return parent_info


def has_child(node_idx, ins_dict):
    terminal = True
    for index, info in ins_dict.items():
        if len(index) == len(node_idx) + 2:
            idx_len = len(node_idx)
            if node_idx == index[:idx_len]:
                terminal = False
                break
    return terminal


def is_parent_relation(par_idx, child_idx):
    parent_rel = False
    abs_len = len(par_idx)
    if len(par_idx) + 2 == len(child_idx) and child_idx[:abs_len] == par_idx:
        parent_rel = True

    return parent_rel


def is_connected(index_one, index_two):
    connected = False
    if len(index_one) > len(index_two):
        ancestor = index_two
        descendent = index_one
    else:
        ancestor = index_one
        descendent = index_two

    anc_len = len(ancestor)
    if descendent[:anc_len] == ancestor:
        connected = True

    return connected, ancestor


def is_sibling_relation(idx_one, idx_two):
    is_sib = False
    if len(idx_one) == len(idx_two) and idx_one[:-1] == idx_two[:-1] and idx_one != idx_two:
        is_sib = True

    return is_sib


def get_sibling_distance(node_index, ins_dict):
    sib_alignment = -1
    for index, info in ins_dict.items():
        if len(index) == len(node_index) and index[:-1] == node_index[:-1] and index != node_index and len(info) > 1:
            sib_alignment = info[1].split('-')[0]

    return sib_alignment


def get_parent_distance(node_index, node_name, alignment, ins_dict):
    parent_alignment = alignment
    for index, info in ins_dict.items():
        if len(index) + 2 == len(node_index):
            par_len = len(index)
            if index == node_index[:par_len]:
                if len(info) == 1:
                    if info[0] in abs_set:
                        break
                    elif info[0] == 'describe-01':
                        break
                    else:
                        if node_name == '-':
                            if info[0] != 'possible':
                                break
                            else:
                                parent_alignment = 999
                                break
                        else:
                            sib_alignment = get_sibling_distance(node_index, ins_dict)
                            if int(sib_alignment) != -1:
                                print('Cal distance from siblings')
                                parent_alignment = sib_alignment
                                break
                            else:
                                parent_alignment = 999
                                break

                parent_alignment = info[1].split('-')[0]
                break

    parent_distance = abs(int(parent_alignment)-alignment)
    return parent_distance


def get_children_distance(idx_one, alignment, ins_dict):
    children_alignment = alignment
    for index, info in ins_dict.items():
        if len(index) == len(idx_one) + 2:
            par_len = len(idx_one)
            if idx_one == index[:par_len]:
                if len(info) == 1:
                    break
                children_alignment = info[1].split('-')[0]
                break

    children_distance = abs(int(children_alignment) - alignment)
    return children_distance


def token_related(node_name, token):

    related = False

    if node_name == 'have-03' or node_name == 'have-06' and token == 'had':
        related = True
        return related
    if node_name == 'think-01' and token == 'thought' or token == 'thoughts':
        related = True
        return related
    if node_name == '-' and token == "n't":
        related = True
        return related
    if node_name == 'amr-unknown' and token == 'why':
        related = True
        return related
    if node_name == 'good' and token == 'best':
        related = True
        return related
    if node_name == '"britain"' and token == 'british':
        related = True
        return related
    if node_name == 'percentage-entity' and token == '%':
        related = True
        return related
    if node_name == 'we' and token == 'our':
        related = True
        return related
    if node_name == '1000000' and token == 'millions':
        related = True
        return related
    if node_name == '1000' and token == 'thousands':
        related = True
        return related
    if node_name == 'this' and token == 'those':
        related = True
        return related
    if node_name == 'day' and token == 'daily':
        related = True
        return related
    if node_name == 'year' and token == 'annual':
        related = True
        return related


    print('here')
    print(node_name + ' ' + token)

    if '-' in node_name and node_name != '-':
        node_name = node_name.split('-')[0]

    if node_name in token or token in node_name:
        related = True

    if node_name == 'outrageous' and token == 'out':
        related = False
    if node_name == 'i' and token == 'imo':
        related = False
    if node_name == 'have-org-role-91' and token == 'have':
        related = False
    if token == 'outrageous' and node_name == 'out':
        related = False
    if token == 'imo' and node_name == 'i':
        related = False

    if node_name == '"democratic"' and token == 'democrats':
        related = True
    if node_name == 'she' and token == 'her':
        related = True

    # if related and token.count('-') != 2 and token[:2] not in  ('08', '20', '09', '07', '01', '02', '03', '04', '05', '06'):
    #     print("Related to Token: " + node_name + ' ' + token)
    print(related)
    return related


def remove_dup_tuple(tuple_list, alignment, ins_dict):

    # tuple_list = [('0.1.0', 'sanction-02', 'sanctions'), ('0.0.0', 'sanction-02', 'sanctions')]
    # print('--------------------')
    # print(tuple_list)

    alignment = int(alignment.split('-')[0])
    new_alignment = ''

    legal_subgraph = ''
    cache = ()

    idx_one = tuple_list[0][0]
    idx_two = tuple_list[1][0]
    name_one = tuple_list[0][1]
    name_two = tuple_list[1][1]
    token = tuple_list[0][2]

    if name_one == name_two:  # same node name
        connected, ancestor = is_connected(idx_one, idx_two)
        # print(connected)
        if connected: # keep ancestor
            for i in range(2):
                if tuple_list[i][0] != ancestor:
                    del tuple_list[i]
                    break
        else: # keep non-terminal
            is_terminal_one = has_child(idx_one, ins_dict)
            is_terminal_two = has_child(idx_two, ins_dict)
            if is_terminal_one and not is_terminal_two:
                del tuple_list[0]
            elif is_terminal_two and not is_terminal_one:
                del tuple_list[1]
            else: # compare distance with its children
                if is_terminal_one and is_terminal_two:  # select nodes have closer parents for both terminals
                    par_dis_one = get_parent_distance(idx_one, name_one, alignment, ins_dict)
                    par_dis_two = get_parent_distance(idx_two, name_two, alignment, ins_dict)
                    if par_dis_one < par_dis_two:
                        del tuple_list[1]
                    else:
                        del tuple_list[0]
                else:  # select nodes have closer children
                    child_dis_one = get_children_distance(idx_one, alignment, ins_dict)
                    child_dis_two = get_children_distance(idx_two, alignment, ins_dict)
                    if child_dis_one < child_dis_two:
                        del tuple_list[1]
                    else:
                        del tuple_list[0]

    else:
        if name_one in abs_set and name_two not in abs_set: # keep non-abstract node
            parent_rel = is_parent_relation(idx_one, idx_two)
            if not parent_rel:
                del tuple_list[0]
            else:
                # if name_one != 'thing' and name_one != 'person' and name_one != 'government-organization':
                # print(idx_one + ' ' + name_one)
                # print(idx_two + ' ' + name_two)
                # print("Legal Subgraph")
                legal_subgraph = 'parent'
                cache = (idx_one, name_one, token)
                del tuple_list[0]
        elif name_one not in abs_set and name_two in abs_set:
            parent_rel = is_parent_relation(idx_two, idx_one)
            if not parent_rel:
                del tuple_list[1]
            else:
                # if name_two != 'thing' and name_two != 'person' and name_two != 'government-organization':
                # print(idx_two + ' ' + name_two)
                # print(idx_one + ' ' + name_one)
                # print("Legal Subgraph")
                legal_subgraph = 'parent'
                cache = (idx_two, name_two, token)
                del tuple_list[1]
        elif name_two in children_set and is_parent_relation(idx_one, idx_two):
            # print("Legal Subgraph")
            legal_subgraph = 'children'
            cache = (idx_two, name_two, token)
            del tuple_list[1]
        elif name_one in children_set and is_parent_relation(idx_two, idx_one):
            # print("Legal Subgraph")
            legal_subgraph = 'children'
            cache = (idx_one, name_one, token)
            del tuple_list[0]
        else: # select nodes related to the token
            if is_sibling_relation(idx_one, idx_two):
                par_info = find_parent_node(idx_one, ins_dict)
                match_one = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', name_one)
                match_two = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', name_two)
                if match_one is not None and match_two is not None and par_info[0] == 'date-entity':
                    # print("Date")
                    legal_subgraph = 'sibling'
                    cache = (idx_one, name_one, token)
                    del tuple_list[0]
                elif match_one is not None and name_one != '-':
                    # print('Digits!')
                    del tuple_list[1]
                elif match_two is not None and name_two != '-':
                    # print('Digits!')
                    del tuple_list[0]
                elif name_one == 'imperative' and name_two == 'we':
                    if token == 'lets':
                        # print('lets')
                        legal_subgraph = 'sibling'
                        cache = (idx_two, name_two, token)
                        del tuple_list[1]
                    else:
                        # print("let's")
                        new_alignment = str(alignment+1) + '-' + str(alignment+2)
                        cache = (idx_two, name_two, token)
                        del tuple_list[1]
                elif name_one == 'we' and name_two == 'imperative':
                    if token == 'lets':
                        # print('lets')
                        legal_subgraph = 'sibling'
                        cache = (idx_one, name_one, token)
                        del tuple_list[0]
                    else:
                        # print("let's")
                        new_alignment = str(alignment+1) + '-' + str(alignment+2)
                        cache = (idx_one, name_one, token)
                        del tuple_list[0]
                elif name_one == 'ever' and name_two == '-' or name_one == '-' and name_two == 'ever':
                    # print('never')
                    legal_subgraph = 'sibling'
                    cache = (idx_one, name_one, token)
                    del tuple_list[0]
                else:
                    # print("here")
                    related_one = token_related(name_one, token)
                    related_two = token_related(name_two, token)

                    if related_one and not related_two:
                        del tuple_list[1]
                    elif related_two and not related_one:
                        del tuple_list[0]
                    else:  # select nodes have children
                        is_terminal_one = has_child(idx_one, ins_dict)
                        is_terminal_two = has_child(idx_two, ins_dict)
                        if is_terminal_one and not is_terminal_two:
                            del tuple_list[0]
                        elif is_terminal_two and not is_terminal_one:
                            del tuple_list[1]
                        else:
                            if is_terminal_one and is_terminal_two:  # select nodes have closer parents for both terminals
                                par_dis_one = get_parent_distance(idx_one, name_one, alignment, ins_dict)
                                par_dis_two = get_parent_distance(idx_two, name_two, alignment, ins_dict)
                                if par_dis_one < par_dis_two:
                                    del tuple_list[1]
                                else:
                                    del tuple_list[0]
                            else:  # select nodes have closer children
                                child_dis_one = get_children_distance(idx_one, alignment, ins_dict)
                                child_dis_two = get_children_distance(idx_two, alignment, ins_dict)
                                if child_dis_one < child_dis_two:
                                    del tuple_list[1]
                                else:
                                    del tuple_list[0]

            else:
                related_one = token_related(name_one, token)
                related_two = token_related(name_two, token)

                if related_one and not related_two:
                    del tuple_list[1]
                elif related_two and not related_one:
                    del tuple_list[0]
                else:  # select nodes have children
                    is_terminal_one = has_child(idx_one, ins_dict)
                    is_terminal_two = has_child(idx_two, ins_dict)
                    if is_terminal_one and not is_terminal_two:
                        del tuple_list[0]
                    elif is_terminal_two and not is_terminal_one:
                        del tuple_list[1]
                    else:
                        if is_terminal_one and is_terminal_two:  # select nodes have closer parents for both terminals
                            par_dis_one = get_parent_distance(idx_one, name_one, alignment, ins_dict)
                            par_dis_two = get_parent_distance(idx_two, name_two, alignment, ins_dict)
                            if par_dis_one < par_dis_two:
                                del tuple_list[1]
                            else:
                                del tuple_list[0]
                        else:  # select nodes have closer children
                            child_dis_one = get_children_distance(idx_one, alignment, ins_dict)
                            child_dis_two = get_children_distance(idx_two, alignment, ins_dict)
                            if child_dis_one < child_dis_two:
                                del tuple_list[1]
                            else:
                                del tuple_list[0]

    return tuple_list, legal_subgraph, cache, new_alignment


def remove_duplicate_align(ins_dict, tok_list):
    duplicate_set = set()
    for node_index, node_info in ins_dict.items():
        if len(node_info) > 1:
            for index, info in ins_dict.items():
                if len(info) > 1 and index != node_index:
                    if node_info[1] == info[1]:
                        # print(node_info)
                        alignment = node_info[1].split('-')[0]
                        tuple_1 = (node_index, node_info[0], node_info[1], tok_list[int(alignment)])
                        tuple_2 = (index, info[0], info[1], tok_list[int(alignment)])
                        duplicate_set.add(tuple_1)
                        duplicate_set.add(tuple_2)

    # print(duplicate_set)

    duplicate_dict = {}
    for tuple in duplicate_set:
        new_tuple = (tuple[0], tuple[1], tuple[3])
        if tuple[2] in duplicate_dict:
            duplicate_dict[tuple[2]].append(new_tuple)
        else:
            tuple_list = list()
            tuple_list.append(new_tuple)
            duplicate_dict[tuple[2]] = tuple_list

    if duplicate_dict:
        print(duplicate_dict)

    new_alignment = ''
    for alignment, tuple_list in duplicate_dict.items():
        cache_list = list()
        new_alignment_list = list()
        new_tuple_list, legal_subgraph, cache, new_alignment = remove_dup_tuple(tuple_list, alignment, ins_dict)
        if cache:
            if not new_alignment:
                cache_list.append(cache)
            else:
                new_alignment_list.append(cache)

        while len(new_tuple_list) > 1:
            new_tuple_list, legal_subgraph, cache, new_alignment = remove_dup_tuple(tuple_list, alignment, ins_dict)
            if cache:
                if not new_alignment:
                    cache_list.append(cache)
                else:
                    new_alignment_list.append(cache)

        if len(cache_list) > 1 and legal_subgraph != 'sibling':
            # print('Warning!!!')
            print(cache_list)

        if legal_subgraph == 'parent':
            # print('parent')
            for cache in cache_list:
                if is_parent_relation(cache[0], tuple_list[0][0]):
                    tuple_list.append(cache)
        elif legal_subgraph == 'children':
            # print('children')
            if is_parent_relation(tuple_list[0][0], cache_list[0][0]):
                tuple_list.extend(cache_list)
        elif legal_subgraph == 'sibling':
            # print('sibling')
            for cache in cache_list:
                if is_sibling_relation(cache[0], tuple_list[0][0]):
                    tuple_list.append(cache)

    if new_alignment:
        duplicate_dict[new_alignment] = new_alignment_list

    if duplicate_dict:
        print(duplicate_dict)

    return duplicate_dict


input = sys.argv[1]
output = sys.argv[2]

with open(input) as f:
    lines = f.readlines()

with open(output, 'w') as result_file:
    alignment_list = []
    sent_list = []
    for line in lines:
        line = line.strip()
        if line.startswith('id'):
            tok_list = []
            ins_dict = collections.OrderedDict()
            continue
        elif line.startswith('#'):
            line = line.split(' ')
            for tok in line:
                if tok != '#':
                    tok = tok.split('_')
                    tok_list.append(tok[0])
            # print(tok_list)
        elif not line:
            alignment_list.append(ins_dict)
            sent_list.append(tok_list)
        else:
            line = line.split('\t')
            node_info = []
            if len(line) > 2:
                node_info.append(line[1])
                node_info.append(line[2])
            else:
                node_info.append(line[1])
            ins_dict[line[0]] = node_info

    for ins_number, ins_dict in enumerate(alignment_list):
        print(ins_number)
        dup_dict = remove_duplicate_align(ins_dict, sent_list[ins_number])

        if dup_dict:
            result_file.write('id:' + str(ins_number) + '\n')
            result_file.write('# ')
            for idx, tok in enumerate(sent_list[ins_number]):
                result_file.write(tok + '_' + str(idx) + ' ')
            result_file.write('\n')
            node_set = set()
            for key, value in dup_dict.items():
                for tuple in value:
                    node_set.add(tuple[0])
            # print(node_set)
            for node_idx, node_info in ins_dict.items():
                if node_info[-1] in dup_dict.keys():
                    if node_idx in node_set:
                        result_file.write(node_idx + '\t' + node_info[0] + '\t' + node_info[1] + '\n')
                    else:
                        result_file.write(node_idx + '\t' + node_info[0] + '\n')
                else:
                    if len(node_info) > 1:
                        result_file.write(node_idx + '\t' + node_info[0] + '\t' + node_info[1] + '\n')
                    else:
                        result_file.write(node_idx + '\t' + node_info[0] + '\n')
            result_file.write('\n')
        else:
            result_file.write('id:' + str(ins_number) + '\n')
            result_file.write('# ')
            for idx, tok in enumerate(sent_list[ins_number]):
                result_file.write(tok + '_' + str(idx) + ' ')
            result_file.write('\n')
            for node_idx, node_info in ins_dict.items():
                if len(node_info) > 1:
                    result_file.write(node_idx + '\t' + node_info[0] + '\t' + node_info[1] + '\n')
                else:
                    result_file.write(node_idx + '\t' + node_info[0] + '\n')
            result_file.write('\n')

