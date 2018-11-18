import collections
import sys
import re


abs_set = {'have-rel-role-91', 'person', 'man', 'aircraft', 'date-entity', 'government-organization', 'political-party', 'product-of', 'multiple', 'criminal-organization', 'have-purpose-91', 'have-polarity-91', 'ethnic-group', 'religious-group', 'email-address-entity', 'have-subevent-91', 'be-temporally-at-91', 'be-destined-for-91', 'street-address-91', 'score-entity', 'byline-91', 'phone-number-entity', 'ordinal-entity', 'url-entity', 'have-frequency-91', 'have-quant-91', 'be-located-at-91', 'relative-position', 'temperature-quantity', 'seismic-quantity', 'energy-quantity', 'numerical-quantity', 'area-quantity', 'distance-quantity', 'volume-quantity', 'have-org-role-91', 'mass-quantity', 'monetary-quantity', 'temporal-quantity', 'percentage-entity', 'power-quantity','railway-line','airport','club','ocean','sports-facility','show','aircraft-type','war','worm','channel','university','book','military','magazine','animal','peninsula','department','bank','car-make','hospital','city-district','natural-disaster','medicine','network','newspaper','valley','band','city','ship','palace','person','school','spaceship','treaty','operation','planet','movie','street','district','company','bay','earthquake','journal','family','event','publication','language','republic','hotel','mountain','agency','moon','road','initiative','system','name','island','game','disease','station','lawyer','park','local-region','research-institute','country','doctor','worship-place','building','organization','seminar','music','river','rocket','dynasty','vehicle','county','incident','state','world-region','range','province','thing','country-region','law','broadcast-program','capital','continent','facility','revolution','conference','location','page','date-entity','territory','man','sea','product','award','pass','destroyer','ethnic-group','son','plane','television','mission','drug','meet-03','government-organization','strait','political-party','missile','league','program','criminal-organization','group','project','religious-group','team','radio','museum','husband','festival'}
quantity_set = ('temporal-quantity', 'distance-quantity', 'volume-quantity', 'mass-quantity', 'volume-quantity', 'energy-quantity', 'numerical-quantity', 'monetary-quantity', 'temperature-quantity', 'area-quantity', 'seismic-quantity', 'power-quantity')
digit_set = {'1': ['first', 'per', 'once', 'one', 'uni', 'an', 'a'], '2': ['second', 'two', 'twice', 'double'], '3': ['third', 'three', 'triple'], '4': ['fourth', 'four'], '5': ['fifth', 'five'], '6': ['sixth', 'six'], '7': ['seventh', 'seven'], '8': ['eighth', 'eight'], '9': ['ninth', 'nine'], '10': ['tenth', 'ten']}
tok_node_dict = {'be-located-at-91': ['in', 'there', 'on', 'where', 'at', 'onto', 'located', 'from'], 'this': ['this', 'these'], 'they': ['they', 'them', 'their', "'m"], 'interrogative': ['?', '??', '???', 'whether', 'if', 'what', 'would', 'does'], 'amr-unknown': ['why', 'what', 'who', 'how', 'if', 'when', 'where'], 'contrast-01': ['but', 'however', 'contrast', 'instead', 'yet', 'rather', 'while', 'otherwise', 'or', 'hand', 'opposed'], 'thing': ['thing', 'things'], 'and': [';', 'and', ',', '...', ':'], 'have-part-91': ['part'], 'have-03': ['have', 'has', 'had', 'with', 'having'], 'have-06': ['have', 'has', 'had'], 'date-interval': ['from', '-', 'to', 'till', 'through'], 'relative-position': ['north', 'west', 'south', 'east', 'northwest', 'northeast', 'southeast', 'southwest', 'away', 'from', 'above', 'southernmost', 'easternmost', 'westernmost', 'northernmost'], 'personal-02': ['personal', 'personally'], 'have-concession-91': ['though', 'although', 'still', 'anyway', 'granted', 'nevertheless', 'nonetheless', 'even', 'but', 'yet', 'despite', 'however'], 'possible-01': ['can', 'could', 'perhaps'], 'then': ['then'], 'slash': ['/'], 'multi-sentence': ['.....', '...', ':', ';', '.', '!', ',', '?'], 'cause-01': ['because'], 'mean-01': [':']}
abstract_node_set = {'thing'}


def is_entity_node(node_idx, ins_dict):
    is_entity = False
    name_index = ''
    for index, info in ins_dict.items():
        if len(index) == len(node_idx) + 2:
            par_len = len(node_idx)
            if index[:par_len] == node_idx:
                if info[0] == 'name':
                    is_entity = True
                    name_index = index
                    break

    return is_entity, name_index


def is_date_node(node_idx, node_info, ins_dict):
    date_node = False
    match = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', node_info[0])
    if match is not None:
        for index, info in ins_dict.items():
            if len(index) + 2 == len(node_idx):
                idx_len = len(index)
                if node_idx[:idx_len] == index:
                    if info[0] == 'date-entity':
                        date_node = True

    return date_node


def is_continuous(start_list, threshold):
    # print(start_list)
    continuous = True
    wrong_idx = -1
    for idx, num in enumerate(start_list):
        if idx != len(start_list) - 1:
            if start_list[idx+1] - num > threshold:
                # if start_list[idx+1] - num == threshold:
                #     print("hahaha")
                continuous = False
                wrong_idx = idx
                break

    # print(continuous)
    # print(wrong_idx)
    return continuous, wrong_idx


def check_span_overlap(span, ins_dict):
    start_list = list()
    start = int(span.split('-')[0])
    end = int(span.split('-')[1])
    pointer = start + 1
    while pointer < end:
        start_list.append(pointer)
        pointer += 1

    for index, info in ins_dict.items():
        if len(info) > 1:
            if int(info[1].split('-')[0]) in start_list:
                # print('overlap')
                # print(span)
                # print(start_list)
                del info[1]
                # print(info)


def span_solver(span_list, threshold):
    start_list = list()
    for idx, span in enumerate(span_list):
        start = int(span.split('-')[0])
        start_list.append(start)

    start_list = sorted(start_list)
    for i in range(3):
        continuous, wrong_idx = is_continuous(start_list, threshold)  # ['28-29', '29-30', '34-35', '31-32', '32-33', '33-34']
        if not continuous:  # ['23-24', '24-25', '25-26', '33-34', '27-28', '28-29']
            if wrong_idx < int(len(start_list)/2):
                del start_list[wrong_idx]
            else:
                del start_list[-1]

    span = str(start_list[0]) + '-' + str(start_list[-1] + 1)
    return span


def span_check_long(span_list):
    start_list = list()
    result_span = ''
    for span in span_list:
        start = int(span.split('-')[0])
        if len(start_list) == 0:
            start_list.append(start)
        else:
            if start < start_list[-1]:
                # print('Reversed Order')
                # print('Inconsist with the span')
                # print(span_list)
                result_span = span_solver(span_list, 3)
                # print(result_span)
                break

            else:
                if start != start_list[-1] + 1 and start != start_list[-1] + 2 and start != start_list[-1] + 3 and start != start_list[-1]:
                    # print('Inconsist with the span')
                    # print(span_list)
                    result_span = span_solver(span_list, 3)
                    # print(result_span)
                    break
                else:
                    start_list.append(start)

    return result_span


def span_check(span_list):
    result_span = ''
    first_start = int(span_list[0].split('-')[0])
    second_start = int(span_list[1].split('-')[0])
    if first_start > second_start:
        if abs(first_start - second_start) > 2:
            # print('Inconsist with the span')
            # print(span_list)
            result_span = span_list[1]
    else:
        if abs(first_start - second_start) > 3:
            # print('Inconsist with the span')
            # print(span_list)
            result_span = span_list[0]

    # if result_span:
        # print(result_span)
    return result_span


def merge_span(span_list):
    result_span = ''
    if len(span_list) > 2:
        result_span = span_check_long(span_list)
    elif len(span_list) == 2:
        result_span = span_check(span_list)

    if result_span:
        return result_span
    else:
        if len(span_list) > 1:
            start_list = list()
            for span in span_list:
                start = int(span.split('-')[0])
                start_list.append(start)
            start_list = sorted(start_list)
            span = str(start_list[0]) + '-' + str(start_list[-1] + 1)
        else:
            span = span_list[0]

        return span


def find_node_index(node_name, ins_dict):
    node_index = ''
    for index, info in ins_dict.items():
        if info[0] == node_name and len(info) > 1:
            node_index = index

    return node_index


def find_parent(node_idx, ins_dict):
    # print(node_idx)
    parent_name = ''
    parent_align = ''
    for index, info in ins_dict.items():
        if len(index) + 2 == len(node_idx):
            idx_len = len(index)
            if node_idx[:idx_len] == index and len(info) > 1:
                parent_name = info[0]
                parent_align = info[1]

    return parent_name, parent_align


def find_grand_parent(node_idx, ins_dict):
    # print(node_idx)
    parent_name = ''
    parent_align = ''
    for index, info in ins_dict.items():
        if len(index) + 4 == len(node_idx):
            idx_len = len(index)
            if node_idx[:idx_len] == index and len(info) > 1:
                parent_name = info[0]
                parent_align = info[1]

    return parent_name, parent_align


def find_all_children(node_idx, ins_dict):
    # print(node_idx)
    children_tuple_list = list()
    for index, info in ins_dict.items():
        if len(index) == len(node_idx) + 2:
            idx_len = len(node_idx)
            if index[:idx_len] == node_idx:
                if len(info) > 1:
                    children_tuple_list.append((index, info[0], info[1]))
                else:
                    children_tuple_list.append((index, info[0]))

    return children_tuple_list


def exchange_align(node_info, origin_align, aligned_index, ins_dict):
    for index, info in ins_dict.items():
        if index == aligned_index:
            alignment = info[1]
            node_info.append(alignment)
            del info[1]
            info.append(origin_align)
            # print(node_info)
            # print(info)


def has_child(node_idx, ins_dict):
    terminal = True
    for index, info in ins_dict.items():
        if len(index) == len(node_idx) + 2:
            idx_len = len(node_idx)
            if node_idx == index[:idx_len]:
                terminal = False
                break
    return terminal


def has_been_aligned(tok_idx, ins_dict):
    is_aligned = False
    aligned_index = ''
    aligned_name = ''
    for index, info in ins_dict.items():
        if len(info) > 1:
            alignment = info[1].split('-')[0]
            if str(tok_idx) == alignment:
                # print(info)
                if info[0] in ('multi-sentence', 'have-org-role-91'):
                    del info[1]
                    continue
                is_aligned = True
                aligned_index = index
                aligned_name = info[0]
                break

    # print(is_aligned)
    return is_aligned, aligned_index, aligned_name


def is_parent(node_idx, parent_idx):
    is_parent_node = False
    if len(node_idx) == len(parent_idx) + 2:
        par_len = len(parent_idx)
        if node_idx[:par_len] == parent_idx:
            is_parent_node = True

    return is_parent_node


def align_to_sib(node_idx, node_info, ins_dict):
    have_align = False
    for index, info in ins_dict.items():
        if len(index) == len(node_idx) and index[:-1] == node_idx[:-1] and index != node_idx and len(info) > 1:
            node_info.append(info[1])
            have_align = True
            # print(node_info)
            # print(info)
            break

    return have_align


def align_from_next_sib(node_idx, ins_dict):
    # print(node_idx)
    have_align = False
    sib_alignment = ''
    for index, info in ins_dict.items():
        if len(index) == len(node_idx) and index[:-1] == node_idx[:-1] and index[-1] > node_idx[-1] and len(info) > 1:
            have_align = True
            sib_alignment = info[1].split('-')[0]
            # print(info)
            break

    return have_align, sib_alignment


def align_certain_sib(node_idx, node_info, ins_dict, sib_name):
    have_align = False
    for index, info in ins_dict.items():
        if len(index) == len(node_idx) and index[:-1] == node_idx[:-1] and index != node_idx and len(info) > 1 and info[0] == sib_name:
            node_info.append(info[1])
            have_align = True
            # print(node_info)
            # print(info)
            break

    return have_align


def align_to_par(node_idx, node_info, ins_dict, align_sib=False):
    # print(node_idx)
    have_align = False
    for index, info in ins_dict.items():
        if len(index) + 2 == len(node_idx):
            idx_len = len(index)
            if node_idx[:idx_len] == index and len(info) > 1:
                # print('Align to parent node.')
                node_info.append(info[1])
                have_align = True
                # print(info)
                # print(node_info)
                break

    if align_sib and not have_align:
        # print('Align to siblings')
        have_align = align_to_sib(node_idx, node_info, ins_dict)
        # print(node_info)

    return have_align


def align_to_par_re(node_idx, ins_dict):
    for index, info in ins_dict.items():
        if index == node_idx:
            node_info = info

    for index, info in ins_dict.items():
        if len(index) + 2 == len(node_idx):
            idx_len = len(index)
            if node_idx[:idx_len] == index and len(info) > 1:
                # print('Align to parent node.')
                node_info.append(info[1])
                # print(info)
                # print(node_info)
                break


def align_to_child(node_idx, node_info, ins_dict):
    have_align = False
    for index, info in ins_dict.items():
        parent_node = is_parent(node_idx, index)
        if parent_node and info[0] in abstract_node_set and len(info) == 1:
            # print('Align to children node')
            info.append(node_info[1])
            # have_align = True
            # print(info)
            break

    # return have_align


def align_to_last_children(node_idx, node_info, ins_dict):
    have_align = False
    for index, info in ins_dict.items():
        parent_node = is_parent(index, node_idx)
        if parent_node and len(info) > 1:
            if info[0] == 'date-entity':
                continue
            if len(node_info) > 1:
                del node_info[1]
                node_info.append(info[1])
                have_align = True
            else:
                node_info.append(info[1])
                have_align = True
            # print(info)

    return have_align


def align_to_first_children(node_idx, node_info, ins_dict):
    have_align = False
    for index, info in ins_dict.items():
        parent_node = is_parent(index, node_idx)
        if parent_node and len(info) > 1:
            if len(node_info) > 1:
                del node_info[1]
                node_info.append(info[1])
                have_align = True
                break
            else:
                node_info.append(info[1])
                have_align = True
                break
            # print(info)

    return have_align


def align_to_first_child(node_idx, node_info, ins_dict):
    have_align = False
    for index, info in ins_dict.items():
        parent_node = is_parent(index, node_idx)
        if parent_node and len(info) > 1:
            node_info.append(info[1])
            have_align = True
            break
            # print(info)

    return have_align


def align_to_digit_child(node_idx, node_info, ins_dict):
    have_align = False
    for index, info in ins_dict.items():
        parent_node = is_parent(index, node_idx)
        if parent_node and len(info) > 1:
            match = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', info[0])
            if match is not None:
                node_info.append(info[1])
                have_align = True
                break

    return have_align


def align_certain_node(node_info, name_node_index, ins_dict):
    for index, info in ins_dict.items():
        if index == name_node_index and len(info) > 1:
            # print(index)
            # print(info)
            node_info.append(info[1])


def align_to_sent(node_idx, node_info, ins_dict, tok_list):
    # print(tok_list)
    have_align = False
    node_name = node_info[0]
    cache = ''
    if len(node_info) > 1:
        cache = node_info[1]
        del node_info[1]
    aligned_index = ''
    aligned_name = ''
    if node_name in tok_node_dict:
        for token in tok_node_dict[node_name]:
            if token in tok_list and not have_align:
                for tok_idx, element in enumerate(tok_list):
                    if element == token:
                        # print(tok_idx)
                        # is_aligned = check_parent(node_idx, node_info, tok_idx, ins_dict)
                        is_aligned, aligned_index, aligned_name = has_been_aligned(tok_idx, ins_dict)
                        # print(is_aligned)
                        # print(aligned_index)
                        # print(aligned_name)
                        # TODO: Do we really need parent node be abstract node???
                        if not is_aligned or (is_parent(node_idx, aligned_index) and aligned_name in abstract_node_set):
                            # if not is_aligned or is_parent(node_idx, aligned_index):
                            alignment = str(tok_idx) + '-' + str(tok_idx + 1)
                            node_info.append(alignment)
                            del tok_list[tok_idx]
                            tok_list.insert(tok_idx, '"dummy"')
                            align_to_child(node_idx, node_info, ins_dict)
                            have_align = True
                            # print('here is ;')
                            # print(token)
                            break
                    else:
                        continue

    if not have_align and cache:
        node_info.append(cache)
    # print(node_info)
    return have_align, aligned_index, aligned_name


def align_digit(node_idx, node_info, ins_dict, tok_list):
    # print(node_idx)
    have_align = False
    for index, info in ins_dict.items():
        if len(index) + 2 == len(node_idx):
            idx_len = len(index)
            if node_idx[:idx_len] == index:
                if info[0] == 'ordinal-entity' and len(info) > 1:
                    node_info.append(info[1])
                    have_align = True
                    # print(node_info)
                    break
                elif info[0] == 'rate-entity-91' and len(info) > 1:
                    node_info.append(info[1])
                    have_align = True
                    # print(node_info)
                    break
                elif info[0] == 'date-entity':
                    # print('Date-entity Align...')
                    for index_2, info_2 in ins_dict.items():
                        if len(index_2) == len(node_idx) and index_2[:-1] == node_idx[:-1] and index_2 != node_idx and len(info_2) > 1:
                            node_info.append(info_2[1])
                            # if len(info) == 1:
                            #     info.append(info_2[1])
                            have_align = True
                            break
                    # print(node_info)
                    # print(info)
                    break
                elif info[0] in quantity_set:
                    for index_2, info_2 in ins_dict.items():  # find siblings
                        if len(index_2) == len(node_idx) and index_2[:-1] == node_idx[:-1] and index_2 != node_idx and len(info_2) > 1:
                            # print('Align to siblings, like days')
                            node_info.append(info_2[1])
                            info.append(info_2[1])
                            have_align = True
                            # print(node_info)
                            # print(info)
                            break

    if not have_align:
        for tok_idx in range(len(tok_list)):
            if node_info[0] in tok_list[tok_idx] and len(tok_list[tok_idx]) < 3:
                # print("Find 1./#1 etc. in the sentence.")
                is_aligned, _, _ = has_been_aligned(tok_idx, ins_dict)
                if not is_aligned:
                    alignment = str(tok_idx) + '-' + str(tok_idx + 1)
                    tok_list.remove(tok_list[tok_idx])
                    tok_list.insert(tok_idx, '"dummy"')
                    node_info.append(alignment)
                    have_align = True
                    # print(node_info)
                    break

        if not have_align:
            if node_info[0] in digit_set:
                token_list = digit_set[node_info[0]]
                for token in token_list:
                    if have_align:
                        break
                    else:
                        for tok_idx in range(len(tok_list)):
                            if tok_list[tok_idx].lower() == token:
                                # print("Find ordinial word in the sentence.")
                                is_aligned, _, _ = has_been_aligned(tok_idx, ins_dict)
                                if not is_aligned:
                                    alignment = str(tok_idx) + '-' + str(tok_idx + 1)
                                    tok_list.remove(tok_list[tok_idx])
                                    tok_list.insert(tok_idx, '"dummy"')
                                    node_info.append(alignment)
                                    have_align = True
                                    # print(node_info)
                                    break

    return have_align


def align_polarity(node_idx, node_info, ins_dict, tok_list):
    have_align = False
    has_sib = False
    # print(node_idx)
    for index, info in ins_dict.items():
        if len(index) + 2 == len(node_idx):
            idx_len = len(index)
            if node_idx[:idx_len] == index and len(info) == 1 and (info[0] == 'possible-01' or info[0] == 'have-03'): # has parent node-possible
                for index_2, info_2 in ins_dict.items(): # find siblings
                    if len(index_2) == len(node_idx) and index_2[:-1] == node_idx[:-1] and index_2 != node_idx and len(info_2) > 1:
                        # print('Align to siblings, like inaccessble')
                        node_info.append(info_2[1])
                        info.append(info_2[1])
                        has_sib = True
                        have_align = True
                        # print(node_info)
                        # print(info)
                        break

                if not has_sib: # find parent node of possible
                    for index_3, info_3 in ins_dict.items():
                        if len(index_3) + 2 == len(index):
                            parent_idx_len = len(index_3)
                            if index[:parent_idx_len] == index_3 and len(info_3) > 1:
                                # print('Align to parent of possible, like unimaginable')
                                node_info.append(info_3[1])
                                info.append(info_3[1])
                                have_align = True
                                # print(node_info)
                                # print(info)
                                break
                else:
                    break

    if not have_align:
        if 'without' in tok_list:
            # print('without')
            tok_idx = tok_list.index('without')
            is_aligned, _, _ = has_been_aligned(tok_idx, ins_dict)
            if not is_aligned:
                alignment = str(tok_idx) + '-' + str(tok_idx + 1)
                node_info.append(alignment)
                tok_list.remove('without')
                tok_list.insert(tok_idx, '"dummy"')
                have_align = True
                # print(node_info)
        elif 'non' in tok_list:
            # print('non')
            tok_idx = tok_list.index('non')
            is_aligned, _, _ = has_been_aligned(tok_idx, ins_dict)
            if not is_aligned:
                alignment = str(tok_idx) + '-' + str(tok_idx + 1)
                node_info.append(alignment)
                tok_list.remove('non')
                tok_list.insert(tok_idx, '"dummy"')
                have_align = True
                # print(node_info)
        else:
            for index, info in ins_dict.items():
                if len(index) + 2 == len(node_idx):
                    idx_len = len(index)
                    if node_idx[:idx_len] == index and len(info) > 1:
                        node_info.append(info[1])
                        have_align = True
                        # print(node_info)

    return have_align


input = sys.argv[1]
output = sys.argv[2]


with open(input) as f:
    align_file = f.readlines()


with open(output, 'w') as result_file:
    alignment_list = []
    sent_list = []
    for line in align_file:
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

    tok_set = set()
    count_dict = {}

    for ins_number, ins_dict in enumerate(alignment_list):
        # print(ins_number)
        for node_idx, node_info in ins_dict.items():
            # Re-arrange nodes
            if len(node_info) >= 2:
                if node_info[0] == 'date-interval':
                    tok_idx = int(node_info[1].split('-')[0])
                    aligned_tok = sent_list[ins_number][tok_idx]
                    if aligned_tok not in tok_node_dict['date-interval']:
                        del node_info[1]
                        align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])

    for ins_number, ins_dict in enumerate(alignment_list):
        # print(ins_number)
        for node_idx, node_info in ins_dict.items():
            if node_info[0] == 'slash':
                    if len(node_info) > 1:
                        del node_info[1]
                    have_align, aligned_index, aligned_name = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                    # print(node_info)
                    # if not have_align: TODO: 16/17 did not split
                    #     print("here")
                    #     print(node_info)

    for ins_number, ins_dict in enumerate(alignment_list):
        # print(ins_number)
        for node_idx, node_info in ins_dict.items():
            if len(node_info) == 1:
                if node_info[0] == 'have-concession-91':
                    have_align, aligned_index, aligned_name = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                    # if not have_align:
                    #     print('here')
                    # print(node_info)

    for ins_number, ins_dict in enumerate(alignment_list):
        # print(ins_number)
        for node_idx, node_info in ins_dict.items():
            if len(node_info) == 1:
                if node_info[0] == 'have-03':
                    have_align, aligned_index, aligned_name = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                    # if not have_align:
                    #     print('here')
                    # print('here')

    for ins_number, ins_dict in enumerate(alignment_list):
        print(ins_number)
        for node_idx, node_info in ins_dict.items():
            if len(node_info) == 1:
                if node_info[0] == 'multi-sentence':
                    have_align, aligned_index, aligned_name = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                    # if not have_align:
                    #     print('here')
                    # else:
                    #     if node_info[1].split('-')[0] == len(sent_list[ins_number]) - 1:
                    #         print('shit')

    for ins_number, ins_dict in enumerate(alignment_list):
        print(ins_number)
        for node_idx, node_info in ins_dict.items():
            if len(node_info) == 1:
                if node_info[0] == 'mean-01':
                    have_align, aligned_index, aligned_name = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                    # if not have_align:
                    #     print('here')

    for ins_number, ins_dict in enumerate(alignment_list):
        # print(ins_number)
        for node_idx, node_info in ins_dict.items():
            # Re-arrange nodes
            if len(node_info) >= 2:
                if node_info[0] == 'imperative':
                    tok_idx = int(node_info[1].split('-')[0])
                    aligned_tok = sent_list[ins_number][tok_idx]
                    parent_name, parent_align = find_parent(node_idx, ins_dict)
                    if node_info[1] != parent_align and aligned_tok not in ('do', 'let', 'lets', 'imperative'):
                        del node_info[1]
                        align_to_par(node_idx, node_info, ins_dict)

    for ins_number, ins_dict in enumerate(alignment_list):
        # print(ins_number)
        for node_idx, node_info in ins_dict.items():
            # Re-arrange nodes
            if len(node_info) >= 2:
                if node_info[0] == 'contrast-01':
                    tok_idx = int(node_info[1].split('-')[0])
                    aligned_tok = sent_list[ins_number][tok_idx]
                    if aligned_tok not in tok_node_dict['contrast-01']:
                        origin_align = node_info[1]
                        del node_info[1]
                        have_align, aligned_index, aligned_name = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                        if not have_align: # but/however has been occupied
                            # print('Not Aligned')
                            exchange_align(node_info, origin_align, aligned_index, ins_dict)

    for ins_number, ins_dict in enumerate(alignment_list):
        print(ins_number)
        for node_idx, node_info in ins_dict.items():
            # Re-arrange nodes
            if len(node_info) >= 2:
                if node_info[0] == 'thing':
                    tok_idx = int(node_info[1].split('-')[0])
                    aligned_tok = sent_list[ins_number][tok_idx]
                    children_tuple_list = find_all_children(node_idx, ins_dict)
                    # print(children_tuple_list)
                    align_with_child = False
                    child_not_align = False
                    not_align_list = list()
                    child_verb_tuple = set()
                    this_tuple = set()
                    for child_tuple in children_tuple_list:
                        if len(child_tuple) > 2:
                            if node_info[1] == child_tuple[2]:
                                align_with_child = True
                                # print(align_with_child)
                                break

                            if child_tuple[1] == 'this' and aligned_tok in ('this', 'these'):
                                this_tuple = child_tuple

                            if '-' in child_tuple[1] and child_tuple[1] != '-':
                                child_verb_tuple = child_tuple

                        else:
                            child_not_align = True
                            not_align_list.append(child_tuple)

                    if not align_with_child and aligned_tok not in ('thing', 'things', 'what', 'where'):
                        if child_not_align:
                            for child_tuple in not_align_list:
                                align_to_par_re(child_tuple[0], ins_dict)
                        else:
                            if this_tuple:
                                # print('Exchange with "this" node')
                                aligned_index = find_node_index('this', ins_dict)
                                origin_align = node_info[1]
                                del node_info[1]
                                exchange_align(node_info, origin_align, aligned_index, ins_dict)
                            elif child_verb_tuple:
                                # print('Get alignment for child verb')
                                del node_info[1]
                                node_info.append(child_verb_tuple[2])
                                # print(node_info)
                            else:
                                have_align, _, _ = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                                # if not have_align:
                                #     print("Not Consistent with its children")
                                    # print(node_info)
                                    # print(aligned_tok)

    for ins_number, ins_dict in enumerate(alignment_list):
        # print(ins_number)
        for node_idx, node_info in ins_dict.items():
            # Re-arrange nodes
            if len(node_info) >= 2:
                if node_info[0] == 'interrogative':
                    tok_idx = int(node_info[1].split('-')[0])
                    aligned_tok = sent_list[ins_number][tok_idx]
                    if aligned_tok not in tok_node_dict['interrogative']:
                        # print('Find the aligned tok')
                        del node_info[1]
                        have_align, aligned_index, aligned_name = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                        if not have_align:
                            # print('Not Align')
                            if aligned_name == 'multi-sentence' or aligned_name == '-':
                                exchange_align(node_info, '', aligned_index, ins_dict)
                                # print(node_info)

    for ins_number, ins_dict in enumerate(alignment_list):
        print(ins_number)
        for node_idx, node_info in ins_dict.items():
            if len(node_info) >= 2:
                if node_info[0] == 'be-located-at-91':
                    tok_idx = int(node_info[1].split('-')[0])
                    aligned_tok = sent_list[ins_number][tok_idx]
                    if aligned_tok not in tok_node_dict['be-located-at-91']:
                        del node_info[1]
                        have_align, aligned_index, aligned_name = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
            else:
                if node_info[0] == 'be-located-at-91':
                    have_align, _, _ = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])

    for ins_number, ins_dict in enumerate(alignment_list):
        print(ins_number)
        for node_idx, node_info in ins_dict.items():
            # Re-arrange nodes
            if len(node_info) < 2:
                # Align null terminal nodes
                # print(node_info)
                terminal = has_child(node_idx, ins_dict)
                if terminal:
                    # print(node_info)
                    if node_info[0] == '-':
                        have_align = align_polarity(node_idx, node_info, ins_dict, sent_list[ins_number])
                        # if not have_align:
                        #     print(node_info)
                        # print(node_info)

                    elif node_info[0] == 'most' or node_info[0] == 'more':
                        have_align = align_to_par(node_idx, node_info, ins_dict)
                        # if not have_align:
                        #     print(node_info)

                    elif node_info[0] == 'this':
                        have_align, _, _ = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])

                    elif node_info[0] == 'they':
                        have_align, _, _ = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])

                    elif node_info[0] == 'interrogative':
                        have_align, _, _ = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                        # if not have_align:
                        #     print('here')

                    elif node_info[0] == 'personal-02':
                        have_align, _, _ = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                        # if not have_align:
                        #     print('here')

                    elif node_info[0] == 'then':
                        have_align, _, _ = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                        # if not have_align:
                        #     print('here')

                    elif node_info[0] == 'amr-unknown':
                        parent_name, _ = find_parent(node_idx, ins_dict)
                        if parent_name == 'cause-01':
                            align_to_par(node_idx, node_info, ins_dict)
                        else:
                            align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])

                    elif node_info[0] == 'cause-01':
                        parent_name, _ = find_parent(node_idx, ins_dict)
                        if parent_name == 'amr-unknown':
                            align_to_par(node_idx, node_info, ins_dict)

                    elif node_info[0] == 'imperative':
                        have_align = align_to_par(node_idx, node_info, ins_dict)

                    elif node_info[0] == 'expressive':
                        have_align = align_to_par(node_idx, node_info, ins_dict)

                    elif node_info[0] == 'perpetrate-01':
                        have_align = align_to_par(node_idx, node_info, ins_dict)
                        # if not have_align:
                        #     print('Not Align')
                        #     print(node_info)

                    elif node_info[0] == 'i':
                        have_align = align_to_par(node_idx, node_info, ins_dict)
                        # if not have_align:
                        #     print('Not Align')
                        #     print(node_info)

                    elif node_info[0] == 'now':
                        have_align = align_to_par(node_idx, node_info, ins_dict)
                        # if not have_align:
                        #     print('Not Align')
                        #     print(node_info)

                    elif node_info[0] == 'possible-01':
                        have_align, _, _ = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                        if not have_align:
                            have_align = align_to_par(node_idx, node_info, ins_dict)
                            # if not have_align:
                            #     print('Not Align')
                        else:
                            tok_idx = int(node_info[1].split('-')[0])
                            aligned_tok = sent_list[ins_number][tok_idx]

                    # imperative should align to its parent node, and parent, imperative and you have the same alignment.
                    elif node_info[0] == 'you':
                        have_align = align_certain_sib(node_idx, node_info, ins_dict, 'imperative')
                        # if not have_align:
                        #     print('Not Align')
                        #     print(node_info)

                    elif node_info[0] == 'year':
                        have_align = align_to_sib(node_idx, node_info, ins_dict)
                        if not have_align:
                            grand_parent_name, grand_parent_align = find_grand_parent(node_idx, ins_dict)
                            if grand_parent_name == 'rate-entity-91':
                                node_info.append(grand_parent_align)
                                # print(node_info)

                    elif node_info[0] == 'day':
                        grand_parent_name, grand_parent_align = find_grand_parent(node_idx, ins_dict)
                        if grand_parent_name == 'rate-entity-91':
                            node_info.append(grand_parent_align)
                        # print('here')
                        # print(node_info)

                    elif node_info[0] == 'we':
                        have_align = align_certain_sib(node_idx, node_info, ins_dict, 'imperative')
                        # print('here')
                        # print(node_info)

                    elif node_info[0] == '"the"' or node_info[0] == '"and"':
                        have_align, sib_alignment = align_from_next_sib(node_idx, ins_dict)
                        if sib_alignment:
                            alignment = str(int(sib_alignment) - 1)
                            is_aligned, _, _ = has_been_aligned(alignment, ins_dict)
                            if not is_aligned:
                                node_info.append(alignment + '-' + str(int(alignment)+1))
                    else:
                        match = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', node_info[0])
                        if match is not None:
                            # print('Digits...')
                            have_align = align_digit(node_idx, node_info, ins_dict, sent_list[ins_number])
                            # if not have_align:
                            #     print('Not Align....')
                            # print(node_info)
                        else:
                            # print("Not Align")
                            # print(node_idx)
                            # print(node_info)
                            if node_info[0] not in count_dict:
                                count_dict[node_info[0]] = 1
                            else:
                                count_dict[node_info[0]] += 1
                #     align_to_sib(node_idx, node_info, ins_dict)


    # print(tok_set)
    # print(sorted(count_dict.items(), key=lambda k:k[1], reverse=True))
    # exit()

    for ins_number, ins_dict in enumerate(alignment_list):
        # print(ins_number)
        span_list = list()
        node_list = list()
        is_entity = False
        for node_idx, node_info in ins_dict.items():
            # print(node_info)
            date_node = is_date_node(node_idx, node_info, ins_dict)
            # print(date_node)
            if date_node:
                is_entity = True
                if len(node_info) > 1:
                    span_list.append(node_info[1])
                    node_list.append(node_info)
            elif '"' in node_info[0]:
                is_entity = True
                if len(node_info) > 1:
                    span_list.append(node_info[1])
                    node_list.append(node_info)
            else:
                if is_entity and span_list:
                    span = merge_span(span_list)
                    for node in node_list:
                        del node[1]
                        node.append(span)
                    check_span_overlap(span, ins_dict)
                    node_list = list()
                    span_list = list()
                    is_entity = False

        if is_entity and span_list:
            span = merge_span(span_list)
            for node in node_list:
                del node[1]
                node.append(span)
            check_span_overlap(span, ins_dict)

    # exit()

    # node_set = set()
    for i in range(8):
        for ins_number, ins_dict in enumerate(alignment_list):
            # print(i)
            # print(ins_number)
            for node_idx, node_info in ins_dict.items():
                # print(node_info)
                if len(node_info) < 2:
                    terminal = has_child(node_idx, ins_dict)
                    if not terminal:
                        # print(node_info)
                        if node_info[0] in abs_set:
                            children_not_align = False
                            children_tuple_list = find_all_children(node_idx, ins_dict)
                            # print(children_tuple_list)
                            for child_tuple in children_tuple_list:
                                if len(child_tuple) < 3:
                                    # print(child_tuple)
                                    if not has_child(child_tuple[0], ins_dict):
                                        children_not_align = True
                                        break
                            if not children_not_align or i > 3:
                                entity_or_not, name_node_index = is_entity_node(node_idx, ins_dict)
                                if entity_or_not:
                                    align_certain_node(node_info, name_node_index, ins_dict)
                                elif '-quantity' in node_info[0] or node_info[0] == 'date-entity':
                                    have_align = align_to_digit_child(node_idx, node_info, ins_dict)
                                    if not have_align:
                                        align_to_first_child(node_idx, node_info, ins_dict)
                                else:
                                    align_to_last_children(node_idx, node_info, ins_dict)

    tok_counter = dict()
    for ins_number, ins_dict in enumerate(alignment_list):
        # print(ins_number)
        for node_idx, node_info in ins_dict.items():
            if len(node_info) < 2:
                if node_info[0] not in tok_counter:
                    tok_counter[node_info[0]] = 1
                else:
                    tok_counter[node_info[0]] += 1

                if node_idx == '0':
                    if node_info[0] == 'and':
                        have_align, aligned_index, aligned_name = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                    # elif node_info[0] == 'include-91':
                    #     print('root')
                    elif node_info[0] == 'have-part-91':
                        # print('root')
                        have_align, aligned_index, aligned_name = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                    elif node_info[0] == 'have-06':
                        # print('root')
                        have_align, aligned_index, aligned_name = align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                    # if not have_align:
                    #     print('Not')
                    #     print(node_idx)
                    #     print(node_info)
    # print(sorted(tok_counter.items(), key=lambda k: k[1], reverse=True))
    # exit()

    # Check inconsistent of digits (when token or node is digit)
    for ins_number, ins_dict in enumerate(alignment_list):
        # print(ins_number)
        # print(tok_list)
        for node_idx, node_info in ins_dict.items():
            # print(node_info)
            if len(node_info) > 1:
                start = int(node_info[1].split('-')[0])
                end = int(node_info[1].split('-')[1])
                if end == start + 1: # not a span
                    aligned_tok = sent_list[ins_number][start]
                    # print(aligned_tok)
                    match_tok = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', aligned_tok)
                    if match_tok is not None and aligned_tok != '+': # if aligned tok is a digit, then the node should also be a digit
                        match_node = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', node_info[0])
                        # print(node_info)
                        if match_node is None and node_info[0] != 'date-entity' and '-quantity' not in node_info[0] and '"' not in node_info[0] and node_info[0] not in abs_set:
                            parent_name, parent_align = find_parent(node_idx, ins_dict)
                            if '-quantity' not in parent_name:
                                del node_info[1]
                                # print("Conflict!")
                                # print(aligned_tok)
                                # print(node_info)
                                # print(sent_list[ins_number])

    # Check inconsistent of name and its entities
    for ins_number, ins_dict in enumerate(alignment_list):
        # print(ins_number)
        for node_idx, node_info in ins_dict.items():
            if len(node_info) > 1:
                if node_info[0] == 'name':
                    children_tuple_list = find_all_children(node_idx, ins_dict)
                    for child_tuple in children_tuple_list:
                        if len(child_tuple) > 2 and '"' in child_tuple[1]:
                            if child_tuple[2] != node_info[1]:
                                # print("Conflict!")
                                del node_info[1]
                                node_info.append(child_tuple[2])
                                # print(node_info)
                                # print(child_tuple)
                                break
                if node_info[0] == 'relative-position':
                    children_tuple_list = find_all_children(node_idx, ins_dict)
                    have_align = False
                    for child_tuple in children_tuple_list:
                        if len(child_tuple) > 2:
                            # print(child_tuple)
                            if child_tuple[1] in tok_node_dict['relative-position']:
                                if node_info[1] != child_tuple[2]:
                                    # print('Here')
                                    del node_info[1]
                                    node_info.append(child_tuple[2])
                                    have_align = True
                                    # print(node_info)
                                    # print(child_tuple)
                                else:
                                    have_align = True
                    if not have_align:
                        tok_idx = int(node_info[1].split('-')[0])
                        aligned_tok = sent_list[ins_number][tok_idx]
                        if aligned_tok not in tok_node_dict['relative-position']:
                            align_to_sent(node_idx, node_info, ins_dict, sent_list[ins_number])
                        # print('Not')
                        # print(node_info)

    for ins_number, ins_dict in enumerate(alignment_list):
        # print(ins_number)
        for node_idx, node_info in ins_dict.items():
                if node_info[0] == 'byline-91':
                    children_tuple_list = find_all_children(node_idx, ins_dict)
                    del node_info[1]
                    for tuple in children_tuple_list:
                        if tuple[1] == 'publication':
                            node_info.append(tuple[2])
                    if len(node_info) == 1:
                        # print('here')
                        # print(children_tuple_list)
                        if len(children_tuple_list[0]) > 2:
                            node_info.append(children_tuple_list[0][2])
                        # print(node_info)

    # exit()
    for ins_number, ins_dict in enumerate(alignment_list):
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
