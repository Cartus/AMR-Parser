#-*- coding: utf-8 -*
from enum import Enum
import re
import sys

act_name = Enum(
    "act_name", "SHIFT REDUCE LEFTLABEL RIGHTLABEL SWAP PRED MERGE ENTITY GENERATE"
)


def get_act_name(act_str):
    ac = act_str[0]
    ac2 = act_str[1]

    if ac == "P":
        return act_name.PRED
    elif ac == "S" and ac2 == "L":
        return act_name.LEFTLABEL
    elif ac == "S" and ac2 == "R":
        return act_name.RIGHTLABEL
    elif ac == "S" and ac2 == "S":
        return act_name.SHIFT
    elif ac == "S" and ac2 == "W":
        return act_name.SWAP
    elif ac == "E" and ac2 == "N":
        return act_name.ENTITY
    elif ac == "M" and ac2 == "R":
        return act_name.REDUCE
    elif ac == "M" and ac2 == "E":
        return act_name.MERGE
    elif ac == "G" and ac2 == "E":
        return act_name.GENERATE
    else:
        sys.exit('Invalid Action!!!')


def get_all_acts(act_dict, all_corpus_acts, act_types):
    if not act_dict.is_frozen():
        sys.exit('Cannot do this unless frozen')

    for a in range(act_dict.get_size()):
        act_enum = get_act_name(act_dict.index_convert(a))
        all_corpus_acts.append(act_enum)
        act_types.add(act_enum)


def count_consec(listrand):
    count = 1
    consec_list = []
    for i in range(len(listrand[:-1])):
        if listrand[i]+1 == listrand[i+1]:
            count += 1
        else:
            consec_list.append(count)
            count = 1

    consec_list.append(count)
    return consec_list


def dfs(graph, node, visited):
    if node not in visited:
        visited.append(node)
        if node in graph.keys():
            for n in graph[node]:
                dfs(graph, n, visited)
    return visited


def is_joint_action_forbidden(action, prev_action, prev2_action, prev3_action, buf_size, stack_size, stack_top, buffer_top, sent_string, reent_node_dict, reent_num, reent_max, reent_nodes, merge_max, forbid_cyc, gen_max, gen_num, partial):

    # print(action)
    # print(stack_size)

    if action == act_name.SWAP and stack_size <= 2:
        return True
    if action == act_name.LEFTLABEL and (stack_size <=1 or buf_size < 2):
        return True
    if action == act_name.RIGHTLABEL and (stack_size <= 1 or buf_size <= 2):
        return True
    if action == act_name.REDUCE and stack_size <= 1:
        return True
    if action == act_name.SHIFT and buf_size == 1:
        return True
    if action == act_name.PRED and buf_size == 1:
        return True
    if action == act_name.ENTITY and buf_size == 1:
        return True
    if action == act_name.GENERATE and buf_size == 1:
        return True
    if action == act_name.MERGE and (stack_size <= 1 or buf_size <= 2):
        return True

    if action == act_name.SWAP and prev_action == act_name.SWAP:
        return True
    if action == act_name.MERGE and (prev_action == act_name.MERGE or prev_action == act_name.ENTITY or prev_action == act_name.PRED or prev_action == act_name.GENERATE):
        return True
    if (action == act_name.PRED or action == act_name.ENTITY or action == act_name.GENERATE) and prev_action == act_name.PRED:
        return True
    if (action == act_name.ENTITY or action == act_name.PRED or action == act_name.GENERATE) and prev_action == act_name.ENTITY:
        return True
    if (action == act_name.REDUCE or action == act_name.LEFTLABEL or action == act_name.RIGHTLABEL or action == act_name.PRED or action == act_name.SWAP or action == act_name.MERGE) and prev_action == act_name.MERGE:
        return True
    if (action == act_name.SHIFT or action == act_name.REDUCE or action == act_name.LEFTLABEL or action == act_name.RIGHTLABEL or action == act_name.SWAP or action == act_name.MERGE) and prev_action == act_name.GENERATE:
        return True
    if (action == act_name.MERGE or action == act_name.PRED or action == act_name.ENTITY or action == act_name.GENERATE) and (prev_action == act_name.LEFTLABEL or prev_action == act_name.RIGHTLABEL):
        return True

    '''Consecutive GEN actions are forbidden (max = 3)'''
    # if (action == act_name.GENERATE or action == act_name.SHIFT or action == act_name.LEFTLABEL or action == act_name.RIGHTLABEL or action == act_name.SWAP or action == act_name.MERGE) and prev_action == act_name.GENERATE and prev2_action == act_name.GENERATE:
    #     return True
    if (action == act_name.SHIFT or action == act_name.LEFTLABEL or action == act_name.RIGHTLABEL or action == act_name.SWAP or action == act_name.MERGE) and prev_action == act_name.GENERATE and prev2_action == act_name.GENERATE:
        return True
    if (action == act_name.GENERATE or action == act_name.SHIFT or action == act_name.LEFTLABEL or action == act_name.RIGHTLABEL or action == act_name.SWAP or action == act_name.MERGE) and prev_action == act_name.GENERATE and prev2_action == act_name.GENERATE and prev3_action == act_name.GENERATE:
        return True

    if (action == act_name.LEFTLABEL or action == act_name.RIGHTLABEL) and partial.contains_edge(stack_top, buffer_top):
        return True
    if (action == act_name.RIGHTLABEL or action == act_name.LEFTLABEL) and partial.contains_edge(buffer_top, stack_top):
        return True

    if (action == act_name.PRED or action == act_name.ENTITY or action == act_name.GENERATE or action == act_name.MERGE) and buffer_top in partial.pred_pos:
        return True
    if (action == act_name.ENTITY or action == act_name.PRED or action == act_name.GENERATE or action == act_name.MERGE) and buffer_top in partial.ent_pos:
        return True
    if (action == act_name.PRED or action == act_name.ENTITY or action == act_name.GENERATE or action == act_name.MERGE) and buffer_top in partial.gen_pos:
        return True
    if action == act_name.MERGE and buffer_top in partial.mer_pos:
        return True

    if (action == act_name.LEFTLABEL or action == act_name.RIGHTLABEL) and buffer_top not in partial.pred_pos and buffer_top not in partial.ent_pos and buffer_top not in partial.gen_pos:
        return True
    if (action == act_name.LEFTLABEL or action == act_name.RIGHTLABEL) and stack_top not in partial.pred_pos and stack_top not in partial.ent_pos and stack_top not in partial.gen_pos:
        return True
    if (action == act_name.LEFTLABEL or action == act_name.RIGHTLABEL) and partial.root_connected:
        return True

    '''Set hard constrain for the number of generated permitted in on AMR graph'''
    if action == act_name.GENERATE and gen_num == gen_max:
        return True

    '''Consecutive Merge operations are bounded'''
    if action == act_name.MERGE and len(partial.mer_pos):
        if list(partial.mer_pos)[-1] == (buffer_top - 1) and count_consec(list(partial.mer_pos))[-1] == merge_max:
            return True

    '''left bracket and right bracket without merge actions (like (ASEAN) can not be nodes in AMR graph)'''
    if buffer_top - int(buffer_top) == 0:
        if (action == act_name.PRED or action == act_name.ENTITY or action == act_name.GENERATE or action == act_name.LEFTLABEL or action == act_name.RIGHTLABEL) and (sent_string[buffer_top] in ('(', ')', '--', '"')) and buffer_top not in partial.mer_pos:
            return True
        # if (action == act_name.ENTITY or action == act_name.GENERATE or action == act_name.MERGE) and ("http" in sent_string[buffer_top]):
        #     return True
        if (action == act_name.GENERATE or action == act_name.MERGE) and ("http" in sent_string[buffer_top]): # website can used ENT(url-entity)
            return True
        if (action == act_name.RIGHTLABEL or action == act_name.GENERATE or action == act_name.ENTITY or action == act_name.MERGE) and sent_string[buffer_top] == 'ROOT':
            return True

    # '''Name of entites, digits, interrogative , time(2:00) and polarity can not be parent nodes'''
    # if action == act_name.LEFTLABEL and buffer_top in partial.predicate_lemmas.keys():
    #     if partial.predicate_lemmas[buffer_top] == 'PR(-)' or partial.predicate_lemmas[buffer_top] == 'PR(interrogative)':
    #         return True
    #
    # if action == act_name.RIGHTLABEL and stack_top in partial.predicate_lemmas.keys():
    #     if partial.predicate_lemmas[stack_top] == 'PR(-)' or partial.predicate_lemmas[stack_top] == 'PR(interrogative)':
    #         return True

    '''Name of entites, digits, interrogative , time(2:00) and polarity can not be parent nodes'''
    if action == act_name.LEFTLABEL and buffer_top in partial.predicate_lemmas.keys():
        if partial.predicate_lemmas[buffer_top] == 'PR(-)' or partial.predicate_lemmas[buffer_top] == 'PR(+)' or partial.predicate_lemmas[buffer_top] == 'PR(interrogative)' or partial.predicate_lemmas[buffer_top] == 'PR(expressive)':
            return True

    if action == act_name.LEFTLABEL and buffer_top in partial.gen_lemmas.keys():
        if partial.gen_lemmas[buffer_top] == 'GEN(-)' or partial.gen_lemmas[buffer_top] == 'GEN(imperative)':
            return True

    if action == act_name.RIGHTLABEL and stack_top in partial.predicate_lemmas.keys():
        if partial.predicate_lemmas[stack_top] == 'PR(-)' or partial.predicate_lemmas[stack_top] == 'PR(+)' or partial.predicate_lemmas[stack_top] == 'PR(interrogative)' or partial.predicate_lemmas[stack_top] == 'PR(expressive)':
            return True

    if action == act_name.RIGHTLABEL and stack_top in partial.gen_lemmas.keys():
        if partial.gen_lemmas[stack_top] == 'GEN(-)' or partial.gen_lemmas[stack_top] == 'GEN(imperative)':
            return True

    '''Double quotes can not be part of an entity'''
    if action == act_name.MERGE and buffer_top in partial.predicate_lemmas.keys():
        if sent_string[buffer_top] == '"' or sent_string[buffer_top] == '-' or sent_string[buffer_top] == ',' or sent_string[buffer_top] == '.' or sent_string[buffer_top] == '--' or sent_string[buffer_top] == "'":
            return True

    if action == act_name.MERGE and stack_top in partial.predicate_lemmas.keys():
        if sent_string[stack_top] == '"' or sent_string[stack_top] == '-' or sent_string[stack_top] == ',' or sent_string[stack_top] == '.' or sent_string[stack_top] == '--' or sent_string[stack_top] == "'":
            return True

    # if stack_top != -999:
    #     print sent_string[stack_top]
    # print sent_string[buffer_top]

    # print("Here")

    if (action == act_name.LEFTLABEL) and (buffer_top - int(buffer_top) == 0) and buffer_top not in partial.mer_pos:
        if '"' in sent_string[buffer_top] and len(sent_string[buffer_top]) > 1:
            return True
        if buffer_top in partial.predicate_lemmas.keys():
            if '"' in partial.predicate_lemmas[buffer_top][3:-1]:
                # print(2)
                return True
        # Only Date Digits can have children
        # if not (partial.predicate_lemmas[buffer_top] == 'ENT(sdate-entity)'):
        #     match = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', sent_string[buffer_top])
        #     if match is not None:
        #         return True
        match1 = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', sent_string[buffer_top]) and sent_string[buffer_top] not in ('-', '+')
        if buffer_top in partial.predicate_lemmas.keys():
            match2 = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', partial.predicate_lemmas[buffer_top][3:-1])  # if the original token is string, like two, then we convert it into digti by PR(2)
            if match1 or match2 is not None:
                # print(3)
                return True

    if (action == act_name.RIGHTLABEL) and (stack_top - int(stack_top) == 0) and stack_top not in partial.mer_pos:
        if '"' in sent_string[stack_top] and len(sent_string[stack_top]) > 1:
            return True
        if stack_top in partial.predicate_lemmas.keys():
            if '"' in partial.predicate_lemmas[stack_top][3:-1]:
                # print(4)
                return True
        # Only Date Digits can have children
        # if not (partial.predicate_lemmas[stack_top] == 'ENT(sdate-entity)'):
        #     match = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', sent_string[stack_top])
        #     if match is not None:
        #         return True
        match1 = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', sent_string[stack_top]) and sent_string[stack_top] not in ('-', '+') # if the original token is a digit / for date-interval invoked by -
        if stack_top in partial.predicate_lemmas.keys():
            match2 = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', partial.predicate_lemmas[stack_top][3:-1]) # if the original token is string, like two, then we convert it into digti by PR(2)
            if match1 or match2 is not None:
                # print(1)
                return True

    # print("Here")

    '''Generated polarity - can not be reentrance'''
    if action == act_name.LEFTLABEL and stack_top in partial.gen_lemmas.keys() and stack_top in partial.edges.keys():
        if partial.gen_lemmas[stack_top] == 'GEN(-)' or partial.gen_lemmas[stack_top] == 'GEN(more)' or partial.gen_lemmas[stack_top] == 'GEN(most)' or partial.gen_lemmas[stack_top] == 'GEN(imperative)' or partial.gen_lemmas[stack_top] == 'GEN(expressive)':
            return True

    if action == act_name.RIGHTLABEL and buffer_top in partial.gen_lemmas.keys() and buffer_top in partial.edges.keys():
        if partial.gen_lemmas[buffer_top] == 'GEN(-)' or partial.gen_lemmas[buffer_top] == 'GEN(more)' or partial.gen_lemmas[buffer_top] == 'GEN(most)' or partial.gen_lemmas[buffer_top] == 'GEN(imperative)' or partial.gen_lemmas[buffer_top] == 'GEN(expressive)':
            return True

    '''Set hard constrain for the number of reentrancy permitted in on AMR graph
        1. One graph have limited number of reentrancy node (reen_nodes)
        2. Reentrancy for all nodes/one node can not excess reent_max.
        3. Already connected and cannot be connected by another node. (entities, digits and polarites)'''
    if action == act_name.LEFTLABEL and stack_top in reent_node_dict.keys():
        if reent_num == reent_max or reent_node_dict[stack_top] == reent_max:
            # print(1)
            return True
        cur_reent_nodes = {k: v for k, v in reent_node_dict.items() if v > 1}
        if cur_reent_nodes == reent_nodes and stack_top not in cur_reent_nodes.keys():
            # print('2')
            return True
        if (reent_node_dict[stack_top] == 1) and (stack_top - int(stack_top) == 0):
            if '"' in sent_string[stack_top] or (':' in sent_string[stack_top] and len(sent_string[stack_top]) > 1):
                # print('3')
                # print(sent_string[stack_top])
                return True
            if stack_top in partial.predicate_lemmas.keys():
                # if (partial.predicate_lemmas[stack_top] == 'PR(-)') or ('"' in partial.predicate_lemmas[stack_top][3:-1]) or (partial.predicate_lemmas[stack_top][3:-1] == 'interrogative'):
                if (partial.predicate_lemmas[stack_top] == 'PR(-)') or (partial.predicate_lemmas[stack_top] == 'PR(+)') or ('"' in partial.predicate_lemmas[stack_top][3:-1]) or (partial.predicate_lemmas[stack_top][3:-1] == 'interrogative') or (partial.predicate_lemmas[stack_top][3:-1] == 'imperative') or (partial.predicate_lemmas[stack_top][3:-1] == 'expressive'):
                    # print('4')
                    return True
            match1 = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', sent_string[stack_top])
            if stack_top in partial.predicate_lemmas.keys():
                match2 = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', partial.predicate_lemmas[stack_top][3:-1])  # if the original token is string, like two, then we convert it into digti by PR(2)
                if match1 or match2 is not None:
                    # print('5')
                    return True
            # else:
            #     if match1 is not None:
            #         print('6')
            #         return True

    if action == act_name.RIGHTLABEL and buffer_top in reent_node_dict.keys():
        if reent_num == reent_max and reent_node_dict[buffer_top] == reent_max:
            # print(1)
            return True
        cur_reent_nodes = {k: v for k, v in reent_node_dict.items() if v > 1}
        if cur_reent_nodes == reent_nodes and buffer_top not in cur_reent_nodes.keys():
            # print(2)
            return True
        if (reent_node_dict[buffer_top] == 1) and (buffer_top - int(buffer_top) == 0):
            if '"' in sent_string[buffer_top] or (':' in sent_string[buffer_top] and len(sent_string[buffer_top]) > 1):
                # print(3)
                return True
            if buffer_top in partial.predicate_lemmas.keys():
                # if (partial.predicate_lemmas[buffer_top] == 'PR(-)') or ('"' in partial.predicate_lemmas[buffer_top][3:-1]) or (partial.predicate_lemmas[buffer_top][3:-1] == 'interrogative'):
                if (partial.predicate_lemmas[buffer_top] == 'PR(-)') or (partial.predicate_lemmas[buffer_top] == 'PR(+)') or ('"' in partial.predicate_lemmas[buffer_top][3:-1]) or (partial.predicate_lemmas[buffer_top][3:-1] == 'interrogative') or (partial.predicate_lemmas[buffer_top][3:-1] == 'imperative') or (partial.predicate_lemmas[buffer_top][3:-1] == 'expressive'):
                    # print(4)
                    return True
            match1 = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', sent_string[buffer_top])
            if buffer_top in partial.predicate_lemmas.keys():
                match2 = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', partial.predicate_lemmas[buffer_top][3:-1])  # if the original token is string, like two, then we convert it into digti by PR(2)
                if match1 or match2 is not None:
                    # print(5)
                    return True
            # else:
            #     if match1 is not None:
            #         return True

    # print("Here")

    '''Forbid actions that will form cycle structure'''
    if forbid_cyc:
        if action == act_name.LEFTLABEL or action == act_name.RIGHTLABEL:
            graph = {}
            for index, parent_list in partial.edges.items():
                for parent in parent_list:
                    if parent.head not in graph.keys():
                        graph[parent.head] = [index]
                    else:
                        graph[parent.head].append(index)
            # print(graph)
            if action == act_name.LEFTLABEL and buffer_top in dfs(graph, stack_top, []):
                return True
            if action == act_name.RIGHTLABEL and stack_top in dfs(graph, buffer_top, []):
                # print('hmmmmm')
                return True

    return False


