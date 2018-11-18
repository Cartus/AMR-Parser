# -*- coding: utf-8 -*

import sys
import model.evaluation as evaluation
import re
from copy import deepcopy
from collections import OrderedDict
from ordered_set import OrderedSet


'''Class for AMR node'''
class AMR_node(object):

    def __init__(self, index, name, parent_dict, child_entity_node, abbr=" ", entity_name_abbr=" ", node_order=20, is_reentrancy=False, is_root=False, no_edge=False):
        self.__index = index # node index, the primary key for one node, get it from the parsing results.
        self.__name = name # node name
        self.__parent_dict = parent_dict # dict of parent node_names, key is the parent node index, value is the edge label
        self.__abbr = abbr # abbreviation for the node name, we need to make sure the AMR graph does not have duplicated abbr for different node but have the same name, like: person, country, etc.,
        self.__child_entity_node = child_entity_node # if this node is the entity node, like ENperson, we need to add its corresponding tokens to a node_list, in order to recover the subgraph of the entity node.
        self.__entity_name_abbr = entity_name_abbr
        self.__is_reentrancy = is_reentrancy
        self.__is_root = is_root
        self.__no_edge = no_edge
        self.__node_order = node_order

    def add_order(self, order):
        self.__node_order = order

    def get_order(self):
        return self.__node_order

    def set_no_edge(self):
        self.__no_edge = True

    def is_no_edge(self):
        return self.__no_edge

    def set_root(self):
        self.__is_root = True

    def is_root(self):
        return self.__is_root

    def set_reentrancy(self):
        self.__is_reentrancy = True

    def is_reentrancy(self):
        return self.__is_reentrancy

    def add_parent(self, parent_node, edge_label):
        self.__parent_dict[parent_node] = edge_label

    def get_parent(self):
        return self.__parent_dict

    def get_index(self):
        return self.__index

    def get_name(self):
        return self.__name

    def set_name(self, name):
        self.__name = name

    def set_abbr(self, abbr):
        self.__abbr = abbr

    def get_abbr(self):
        return self.__abbr

    def is_entity(self):
        return len(self.__child_entity_node)

    def add_child_entity_node(self, child_entity_node):
        self.__child_entity_node.append(child_entity_node)

    def add_child_entity_list(self, child_entity_list):
        self.__child_entity_node = deepcopy(child_entity_list)

    def get_child_entity_node(self):
        return self.__child_entity_node

    def set_entity_name_abbr(self, entity_name_abbr):
        self.__entity_name_abbr = entity_name_abbr

    def get_entity_name_abbr(self):
        return self.__entity_name_abbr

    def __eq__(self, other): # If two objects' index are the same, we consider them as the same node.
        return self.__index == other.__index

    def __repr__(self):
        return self.__name

    def __str__(self):
        return "Index = " + str(self.__index) + ", abbr = " + self.__abbr + ", Name = " + str(self.__name) + ", Parent Nodes = " + str(self.__parent_dict) + ", Order = " + str(self.__node_order) + ", Child Entity Node = " + str(self.__child_entity_node) + ", Entity Name Abbr = " + str(self.__entity_name_abbr) + ", Reentrancy = " + str(self.__is_reentrancy)


class amr_string(object):

    def __init__(self):
        self.cur_amr = ""


def get_abbr(node, added_abbr):
    if node.get_name()[:2] == 'EN':  # For entity node, we use the real name (after EN) to create the abbr
        abbr = node.get_name()[2]
        entity_abbr = "n"
        entity_counter = added_abbr[entity_abbr]
        if entity_counter == 0:
            node.set_entity_name_abbr(entity_abbr)
        else:
            node.set_entity_name_abbr(entity_abbr + str(entity_counter + 1))
        added_abbr[entity_abbr] += 1

    elif node.get_name() == 'sdate-entity':
        abbr = node.get_name()[1]

    elif node.get_name() == 'ROOT':  # No need to create abbr for fake ROOT node
        abbr = ''

    elif node.get_name() == '-':
        node.set_no_edge()
        abbr = ''

    elif node.get_name() == '"GMT"':
        node.set_no_edge()
        abbr = ''

    elif '"' in node.get_name():
        node.set_no_edge()
        abbr = 'z'

    elif node.get_name() == 'interrogative':
        node.set_no_edge()
        abbr = ''

    elif node.get_name() in ('=', '&'):  # for special symbol, like: =,
        abbr = 's'

    elif '/' in node.get_name():
        node.set_name('"' + node.get_name() + '"')
        abbr = 'x'

    else:
        match = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', node.get_name()[0])
        if match is not None:
            # node.set_digit()
            node.set_no_edge()
            abbr = 'x'
        else:
            abbr = node.get_name()[0]
            uppercase_dict = {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e", "F": "f", "G": "g", "H": "h", "I": "i",
                              "J": "j", "K": "k", "L": "l", "M": "m", "N": "n", "O": "o", "P": "p", "Q": "q", "R": "r",
                              "S": "s", "T": "t", "U": "u", "V": "v", "W": "w", "X": "x", "Y": "y", "Z": "z"}
            if abbr in uppercase_dict.keys():
                abbr = uppercase_dict[abbr]

    return abbr


'''Adding abbreviation for each AMR node, like p for first person, p2 for second person'''


def add_node_abbr(node_dict, added_abbr):
    for node_index, node in node_dict.items():
        # print(node.get_name())
        # print(added_abbr)

        if node.get_name().count('-') >= 2:
            node_split_list = node.get_name().split('-')
            is_date = True
            for ele in node_split_list:
                match = re.match(r'^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$', ele)
                if match is None:
                    is_date = False
            if is_date:
                abbr = 'x'
            else:
                abbr = get_abbr(node, added_abbr)
        else:
            abbr = get_abbr(node, added_abbr)

        if not abbr:
            continue

        # print abbr
        counter = added_abbr[abbr]  # Get the frequency for the current abbr, like p

        if counter == 0:  # If we have used this abbr before, we simply use the first character to create the abbr, like p for person
            current_abbr = abbr
        else:  # If we already used p, then we will create the new abbr according to the frequency of the character.
            current_abbr = abbr + str(counter + 1)
        added_abbr[abbr] += 1
        node.set_abbr(current_abbr)
        # print(node)


'''For entity node, like ENperson, we need to map it to the original span (which token were merged into such node), then add these tokens to its child_entity_node node_list'''
def add_entity_child(node_dict, merge_index, tokens):

    country_dict = {"Zimbabwean": "Zimbabwe", "Bulgarian": "Bulgaria", "Kuwaiti": "Kuwait", "Qatari": "Qatar", "Rican": "Rica", "Georgian": "Georgia", "Colombian": "Colombia", "Mexican": "Mexico", "Nigerian": "Nigeria", "Chechen": "Chechnya", "Iraqis": "Iraq", "afghanistans": "Afghanistan", "Algerian": "Algeria", "Kurdish": "Kurdistan", "Mauritanian": "Mauritania", "Ukrainian": "Ukraine", "Kazakh": "Kazakhstan", "Canadian": "Canada", "Jordanian": "Jordan", "Palestinian": "Palestine", "Estonian": "Estonia", "Kenyan": "Kenya", "Israelis": "Israel", "Iranians": "Iran", "Australian": "Australia", "Israeli": "Israel", "Syrian": "Syria", "Nicaraguan": "Nicaragua", "Nicaraguans": "Nicaragua", "Cuban": "Cuba", "French": "France", "Russo": "Russia", "Libyan": "Libya", "Taiwanese": "Taiwan", "Albanian": "Albania", "German": "Germany", "Egyptian": "Egypt", "Thai": "Thailand", "Iraqi": "Iraq", "African": "Africa", "Swedish": "Sweden", "Yemenis": "Yemen", "Yemeni": "Yemen", "Chinese": "China", "Singaporean": "Singapore", "Malaysian": "Malaysia", "Indonesian": "Indonesia", "Vietnamese": "Vietnam", "Japanese": "Japan", "Russian": "Russia", "Korean": "Korea", "Koreans": "Korea", "Afghan": "Afghanistan", "Iranian": "Iran", "Tajik": "Tajikistan", "Brazilian": "Brazil", "British": "Britain", "Cambodian": "Cambodia", "Indian": "India", "Pakistani": "Pakistan"}
    religious_dict = {"Hindu": "Hinduism", "Islamic": "Islam", "Islamist": "Islamism"}
    world_dict = {"African": "Africa", "Asian": "Asia", "Iranians": "Iran", "Kashmiri": "Kashmir", "Kashmiris": "Kashmir", "Himalayan": "Himalayas", "Western": "West", "western": "West", "eastern": "East"}
    continent_dict = {"American": "America", "Americas": "America", "Asian": "Asia", "Asians": "Asia", "European": "Europe", "Europeans": "Europe"}

    for node_index, node in node_dict.items():
        # print(node.get_name())
        if node.get_name()[:2] == 'EN' or node.get_name() == 'sdate-entity':
            token_index_list = []
            i = node.get_index()
            is_single_entity = True

            is_country = False
            is_regroup = False
            is_worregion = False
            is_continent = False
            if node.get_name() == "ENcountry":
                is_country = True
            elif node.get_name() == "ENreligious-group":
                is_regroup = True
            elif node.get_name() == "ENworld-region":
                is_worregion = True
            elif node.get_name() == "ENcontinent":
                is_continent = True

            while i >= 0:
                if merge_index.count(i) != 0:
                    is_single_entity = False
                    if i not in token_index_list:
                        token_index_list.append(i)
                    if (i-1) not in token_index_list:
                        token_index_list.append(i-1)
                else:
                    break
                i = i - 1

            token_index_list.reverse()
            child_entity_list = list()

            # For ' in child entity, like op1 "Arab" :op2 "Interior" :op3 "Ministers" :op4 "'" :op5 "Council"
            for token_index in token_index_list:
                token = tokens[int(token_index)]
                # print(token)
                if token == '"':
                    continue
                elif (token == "'" or token == "'s") and child_entity_list:
                    child_entity_list[-1] = child_entity_list[-1] + token
                    continue
                elif token == "Russian" and tokens[int(token_index)+1] == "Federation":
                    pass
                elif token == "Libyan" and tokens[int(token_index)+1] == "Arab" and tokens[int(token_index)+2] == "Jamahiriya":
                    pass
                elif is_country and token in country_dict:
                    token = country_dict[token]
                elif is_continent and token in continent_dict:
                    token = continent_dict[token]
                elif is_regroup and token in religious_dict:
                    token = religious_dict[token]
                elif is_worregion and token in world_dict:
                    token = world_dict[token]
                child_entity_list.append(token)
            node.add_child_entity_list(child_entity_list)

            if is_single_entity:
                token = tokens[int(i)]
                # print(token)
                if token == "Saudis":
                    node.add_child_entity_node("Saudi")
                    node.add_child_entity_node("Arabia")
                else:
                    if is_country and token in country_dict:
                        token = country_dict[token]
                    elif is_continent and token in continent_dict:
                        token = continent_dict[token]
                    elif is_regroup and token in religious_dict:
                        token = religious_dict[token]
                    elif is_worregion and token in world_dict:
                        token = world_dict[token]
                    # node.add_child_entity_node(tokens[int(i)])
                    node.add_child_entity_node(token)

            # print(node)

"""
We traverse the graph in a DFS fashion to get a nested dictionary to represent a DAG
"""


def traverse(hierarchy, graph, names):
    for name in names:
        hierarchy[name] = traverse(OrderedDict(), graph, graph[name])
    return hierarchy


def is_unsplit_node(current_node, result_string):

    sub_dict = {"01": 1, "02": 2, "03": 3, "04": 4, "05": 5, "06": 6, "07": 7, "08": 8, "09": 9, "10": 10, "11": 11, "12": 12}
    child_name_list = current_node.get_child_entity_node()
    child_tuple_list = []

    # print(child_name_list)

    if len(child_name_list) == 1 and child_name_list[0].count('-') >= 2 and '--' not in child_name_list:
        child_name_list = child_name_list[0].split('-')
        for i in range(len(child_name_list)):
            if i == 0:
                child_tuple_list.append(("year", child_name_list[0]))
            elif i == 1:
                if child_name_list[1] in sub_dict:
                    child_tuple_list.append(("month", sub_dict[child_name_list[1]]))
                else:
                    child_tuple_list.append(("month", child_name_list[1]))
            elif i == 2:
                if child_name_list[2] in sub_dict:
                    child_tuple_list.append(("day", sub_dict[child_name_list[2]]))
                else:
                    child_tuple_list.append(("day", child_name_list[2]))

    elif len(child_name_list) == 1 and len(child_name_list[0]) == 8 and child_name_list[0] not in ("February", "November", "December"): # For 20080710, year 2008, month 7, day 10
        date = child_name_list[0]

        if '/' in date:
            date = date.split('/')
            child_tuple_list.append(("year", "20" + date[2]))
            child_tuple_list.append(("month", date[0]))
            child_tuple_list.append(("day", date[1]))
        else:
            child_tuple_list.append(("year", date[:4]))
            if date[4] == "0":
                child_tuple_list.append(("month", date[5]))
            else:
                child_tuple_list.append(("month", date[4:6]))
            if date[6] == "0":
                child_tuple_list.append(("day", date[7]))
            else:
                child_tuple_list.append(("day", date[6:8]))

    elif len(child_name_list) == 1 and len(child_name_list[0]) == 6 and child_name_list[0] != "August" :
        date = child_name_list[0]
        if 'pm' in child_name_list[0]:
            time_list = date[:-2].split(':')
            hour = str(int(time_list[0]) + 12)
            child_tuple_list.append(("time", '"' + hour + ':' + time_list[1] + '"'))
        elif 'am' in child_name_list[0]:
            child_tuple_list.append(("time", '"' + date[:-2] + '"'))
        else:
            if date[0] in ("0", "1"): # For 070000
                child_tuple_list.append(("year", "20"+date[:2]))
            elif date[0] in ("2", "3", "4", "5", "6", "7", "8", "9"): # For 100000
                child_tuple_list.append(("year", "19" + date[:2]))

            if date[2:4] != "00": # For 960107
                if date[2] == "0":
                    child_tuple_list.append(("month", date[3]))
                else:
                    child_tuple_list.append(("month", date[2:4]))
                if date[4] == "0":
                    if date[4:] == "00":
                        pass
                    else:
                        child_tuple_list.append(("day", date[5]))
                else:
                    child_tuple_list.append(("day", date[4:]))

    elif len(child_name_list) == 1 and "/" in child_name_list[0]: # For 9/11, month 9, day 11
        result = child_name_list[0].split("/")
        child_tuple_list.append(("month", result[0]))
        child_tuple_list.append(("day", result[1]))

    for i in range(len(child_tuple_list)):
        (edge_label, child_name) = child_tuple_list[i]
        result_string.cur_amr += " " + ":" + edge_label + " " + str(child_name)

    return child_tuple_list


def date_edge_label(child_name, is_pm):

    result_list = list()
    month_list = {"January": 1, "Jan": 1, "February": 2, "Feb": 2, "March": 3, "Mar": 3, "April": 4, "Apr": 4, "May": 5,
                  "June": 6, "Jun": 6, "July": 7, "Jul": 7, "August": 8, "Aug": 8, "September": 9, "Sep": 9,
                  "October": 10, "Oct": 10, "November": 11, "Nov": 11, "December": 12, "Dec": 12}
    season_list = ["Spring", "spring", "Summer", "summer", "Fall", "fall", "Winter", "winter"]
    time_list = ["AM", "PM"]

    if child_name in month_list:
        result_list.append(("month", month_list[child_name]))
    elif ":" in child_name:
        if is_pm:
            time_list = child_name.split(':')
            hour = str(int(time_list[0]) + 12)
            result_list.append(("time", '"' + hour + ':' + time_list[1] + '"'))
        else:
            result_list.append(("time", '"'+child_name+'"'))

    elif "GMT" in child_name:
        result_list.append(("timezone", '"' + child_name + '"'))
    elif "EDT" in child_name:
        result_list.append(("timezone", '"' + child_name + '"'))
    elif "ET" in child_name:
        result_list.append(("timezone", '"' + child_name + '"'))
    elif "PST" in child_name:
        result_list.append(("timezone", '"' + child_name + '"'))
    elif "UTC" in child_name:
        result_list.append(("timezone", '"' + child_name + '"'))
    elif "AEDT" in child_name:
        result_list.append(("timezone", '"' + child_name + '"'))
    elif "/" in child_name:
        child_name = child_name.split('/')
        result_list.append(("day", child_name[0]))
        result_list.append(("year", "19"+child_name[1]))
    elif child_name in time_list:
        result_list.append(("", ""))
    elif child_name in season_list:
        result_list.append(("season", child_name))
    elif child_name[-2:] in ("th", "st"):
        result_list.append(("century", child_name[:-2]))
    else:
        match = re.match(r'.*([1-3][0-9]{3})', child_name)
        if match is not None:
            result_list.append(("year", child_name))

    if not result_list:
        if child_name[0] == '0': # for :day 08
            result_list.append(("day", child_name[1]))
        else:
            result_list.append(("day", child_name))

    return result_list


def date_replace(current_node, prev_node_index, is_root, result_string):

    if is_root:
        result_string.cur_amr += ' ' + "(" + current_node.get_abbr() + ' / ' + current_node.get_name()[1:]
    else:
        result_string.cur_amr += ' ' + ":" + current_node.get_parent()[prev_node_index] + "(" + current_node.get_abbr() + ' / ' + current_node.get_name()[1:]

    date_order_dict = {}

    child_tuple_list = is_unsplit_node(current_node, result_string)

    is_pm = False
    if 'PM' in current_node.get_child_entity_node():
        is_pm = True

    if not len(child_tuple_list):
        for i in range(len(current_node.get_child_entity_node())):
            result_list = date_edge_label(current_node.get_child_entity_node()[i], is_pm)
            for (edge_label, child_name) in result_list:
                # print((edge_label, child_name))
                if edge_label == "year":
                    date_order_dict["year"] = (edge_label, child_name)
                elif edge_label == "month":
                    date_order_dict["month"] = (edge_label, child_name)
                elif edge_label == "day":
                    date_order_dict["day"] = (edge_label, child_name)
                elif edge_label == "time":
                    date_order_dict["time"] = (edge_label, child_name)
                elif edge_label == "timezone":
                    date_order_dict["timezone"] = (edge_label, child_name)
                elif edge_label == "season":
                    date_order_dict["season"] = (edge_label, child_name)
                elif edge_label == "century":
                    date_order_dict["century"] = (edge_label, child_name)

    for key, (edge_label, child_name) in date_order_dict.items():
        result_string.cur_amr += " " + ":" + edge_label + " " + str(child_name)


def entity_replace(current_node, prev_node_index, is_root, result_string):
    # print(current_node)
    # print(current_node.get_name())
    if is_root:
        result_string.cur_amr += ' ' + "(" + current_node.get_abbr() + ' / ' + current_node.get_name()[2:]
    else:
        result_string.cur_amr += ' ' + ":" + current_node.get_parent()[prev_node_index] + "(" + current_node.get_abbr() + ' / ' + current_node.get_name()[2:]

    if current_node.get_name() == 'ENurl-entity':
        result_string.cur_amr += " " + ":value " + " \"" + current_node.get_child_entity_node()[0] + "\""
    else:
        result_string.cur_amr += " " + ":name (" + current_node.get_entity_name_abbr() + " / name"

        for i in range(len(current_node.get_child_entity_node())):
            if i == len(current_node.get_child_entity_node()) - 1:
                result_string.cur_amr += " " + ":op" + str(i + 1) + " \"" + current_node.get_child_entity_node()[i] + "\"" + ")"
            else:
                result_string.cur_amr += " " + ":op" + str(i + 1) + " \"" + current_node.get_child_entity_node()[i] + "\""


def pretty(d, node_dict, prev_node_index, added_list, result_string):

    for i, (key, value) in enumerate(d.items()):
        current_node = node_dict[key]

        if current_node not in added_list:
            # print current_node
            if isinstance(value, dict):
                if len(value) == 0:
                    # if len(current_node.get_parent()) == 0 or current_node.get_parent().values()[0] == 'root':
                    if len(current_node.get_parent()) == 0 or current_node.is_root():
                        if current_node.is_entity():
                            if current_node.get_name() == 'sdate-entity':
                                date_replace(current_node, prev_node_index, True, result_string)
                            else:
                                entity_replace(current_node, prev_node_index, True, result_string)
                        else:
                            result_string.cur_amr += ' ' + "(" + current_node.get_abbr() + ' / ' + current_node.get_name()
                        result_string.cur_amr += ")"
                        added_list.append(current_node)

                    else:
                        if current_node.is_entity():
                            if current_node.get_name() == 'sdate-entity':
                                date_replace(current_node, prev_node_index, False, result_string)
                            else:
                                entity_replace(current_node, prev_node_index, False, result_string)
                            result_string.cur_amr += ")"

                        elif current_node.is_no_edge():
                            if current_node.get_parent()[prev_node_index] == 'li':
                                result_string.cur_amr += " " + ":" + current_node.get_parent()[prev_node_index] + "(" + current_node.get_abbr() + ' / ' + current_node.get_name()
                            else:
                                result_string.cur_amr += " " + ":" + current_node.get_parent()[prev_node_index] + " " + current_node.get_name()

                        else:
                            result_string.cur_amr += ' ' + ":" + current_node.get_parent()[prev_node_index] + "(" + current_node.get_abbr() + ' / ' + current_node.get_name()
                            result_string.cur_amr += ")"
                        added_list.append(current_node)

                else:
                    # if len(current_node.get_parent()) == 0 or current_node.get_parent().values()[0] == 'root':
                    if len(current_node.get_parent()) == 0 or current_node.is_root():
                        if current_node.is_entity():
                            if current_node.get_name() == 'sdate-entity':
                                date_replace(current_node, prev_node_index, True, result_string)
                            else:
                                entity_replace(current_node, prev_node_index, True, result_string)
                        else:
                            result_string.cur_amr += ' ' + "(" + current_node.get_abbr() + ' / ' + current_node.get_name()
                        added_list.append(current_node)
                        pretty(value, node_dict, key, added_list, result_string)
                        result_string.cur_amr += ")"
                    else:
                        if current_node.is_entity():
                            if current_node.get_name() == 'sdate-entity':
                                date_replace(current_node,prev_node_index, False, result_string)
                            else:
                                entity_replace(current_node, prev_node_index, False, result_string)
                        else:
                            result_string.cur_amr += ' ' + ":" + current_node.get_parent()[prev_node_index] + "(" + current_node.get_abbr() + ' / ' + current_node.get_name()
                        added_list.append(current_node)
                        pretty(value, node_dict, key, added_list, result_string)
                        # result_string + '{0})'.format('\t' * indent) + "\n"
                        result_string.cur_amr += ")"
        else:
            current_node = node_dict[key]
            result_string.cur_amr += " " + ":" + current_node.get_parent()[prev_node_index] + " " + current_node.get_abbr()


'''
Detect cyclic in a DAG, if it exists then return the path as a list
'''


def cyclic(g):
    ancestor_list = list()
    path = OrderedSet()

    def visit(vertex):
        path.add(vertex)
        for neighbour in g.get(vertex, ()):
            if neighbour in path or visit(neighbour):
                if not len(ancestor_list):
                    ancestor_list.append(neighbour)
                return True
        path.remove(vertex)
        return False

    return any(visit(v) for v in g), list(path), ancestor_list


def get_reward(node_list, node_names, tokens, merge_index, gold_amr, output_file=None):

    # print("Here")
    # print(node_list)
    # print(node_names)
    # print(tokens)
    # print(merge_index)

    '''Construct the skeleton of the graph, has_parent and node_dict'''
    graph = {name: set() for tuple in node_list for name in tuple if not isinstance(name, str)}
    has_parent = {name: False for tuple in node_list for name in tuple if not isinstance(name, str)}
    node_dict = {}

    '''Create all AMR_node object based on the node_list then put them into the node_dict'''
    fake_root_index = None
    for parent, child, edge_label in node_list:
        parent_node = AMR_node(parent, node_names[parent], {}, [])
        child_node = AMR_node(child, node_names[child], {}, [])
        if not parent in node_dict.keys():
            node_dict[parent] = parent_node
        if not child in node_dict.keys():
            node_dict[child] = child_node
        if node_names[parent] == "ROOT":
            fake_root_index = parent

    '''Construct the graph and has_parent dictionary.
           For graph dict: each node is the key, the value is a set of its child node_names, if it doesn't have, it will be set([]) instead
           For has_parent dict: each node is the key, the value is whether it has parent node (T/F)
       Then add each node's parent node and the corresponding edge_label to its parent_dict attribute'''
    for parent, child, edge_label in node_list:
        graph[parent].add(child)
        has_parent[child] = True
        for index, exist_node in node_dict.items():
            exist_node_index = exist_node.get_index()
            if exist_node_index == child:
                if exist_node.get_parent():
                    exist_node.set_reentrancy
                exist_node.add_parent(parent, edge_label)
                if edge_label[:2] == "op":
                    exist_node.add_order(int(edge_label[2:]))
                elif edge_label[:3] == "ARG":
                    if not edge_label[-1] == 'f':
                        exist_node.add_order(int(edge_label[3:]))

    new_graph = {}
    for parent, child in graph.items():
        if len(child) > 1:
            order_dict = {}
            for node_idx in child:
                current_node = node_dict[node_idx]
                order_dict[node_idx] = current_node.get_order()
            order_list = (sorted(order_dict.items(), key=lambda d: d[1]))
            new_graph[parent] = OrderedSet([tup[0] for tup in order_list])
        else:
            new_graph[parent] = OrderedSet(child)

    '''An alphabet for creating abbreviation for each AMR node, each abbr has frequency 0'''
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    added_abbr = {ele: 0 for ele in alphabet}

    add_node_abbr(node_dict, added_abbr)
    add_entity_child(node_dict, merge_index, tokens)

    # for node_index, node in node_dict.items():
    #     print(node)

    '''Construct root node_list based on the has_parent dict, usually the node_list only has one element'''
    roots = [name for name, parents in has_parent.items() if not parents]

    sys.setrecursionlimit(100)

    # print(new_graph)
    # exit()

    try:
        hierarchy = traverse(OrderedDict(), new_graph, roots)
    except:
        print("Exceed Maximum Recursion")
        cur_amr = "(r / root)"
        return evaluation.get_score_train(cur_amr, gold_amr)

    if len(hierarchy) == 0:
        cur_amr = "(r / root)"
        if output_file:
            output_file.write(cur_amr + '\n')
            output_file.write('\n')
        return evaluation.get_score_train(cur_amr, gold_amr)
    else:
        added_list = []
        prev_node_index = 999
        my_string = amr_string()

        # print(hierarchy)

        if fake_root_index:
            for i in range(len(node_list)):
                if node_list[i][0] == fake_root_index:
                    root_index = node_list[i][1]
                    node_dict[root_index].set_root()

            if len(hierarchy) > 1:
                new_hierarchy = {}
                new_first_child_list = []
                for parent, children in hierarchy.items():
                    if parent == fake_root_index:
                        new_hierarchy[parent] = children
                for parent, children in hierarchy.items():
                    if not parent == fake_root_index:
                        new_hierarchy[fake_root_index][root_index][parent] = children
                        if parent not in new_first_child_list:
                            new_first_child_list.append(parent)
                for node_index, node in node_dict.items():
                    for first_child_index in new_first_child_list:
                        if node_index == first_child_index:
                            node.add_parent(root_index, "ARG2")

                pretty(new_hierarchy[fake_root_index], node_dict, fake_root_index, added_list, my_string)

            else:
                for key, value in hierarchy[fake_root_index].items():
                    node_dict[key].set_root()
                    break
                pretty(hierarchy[fake_root_index], node_dict, prev_node_index, added_list, my_string)
        else:
            for key, value in hierarchy.items():
                node_dict[key].set_root()
                break
            pretty(hierarchy, node_dict, prev_node_index, added_list, my_string)

    if my_string.cur_amr[0] == " ":
        predicted_amr = my_string.cur_amr[1:]
    else:
        predicted_amr = my_string.cur_amr

    # if my_string.cur_amr[0] == " ":
    #     print(my_string.cur_amr[1:])
        # score, precision, recall = evaluation.get_score_train(my_string.cur_amr[1:], gold_amr)
    # else:
    #     print(my_string.cur_amr)
        # score, precision, recall = evaluation.get_score_train(my_string.cur_amr, gold_amr)
    if output_file:
        output_file.write(predicted_amr+'\n')
        output_file.write('\n')

    score, precision, recall = evaluation.get_score_train(predicted_amr, gold_amr)

    return score, precision, recall


