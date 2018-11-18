import nltk
import sys
from nltk.stem import WordNetLemmatizer

reload(sys)  
sys.setdefaultencoding('utf8')

lemmatizer = WordNetLemmatizer()

input = sys.argv[1]
output = sys.argv[2]


with open(input) as f:
    align_file = f.readlines()


with open(output, 'w') as conll_file:
    num_instance = -1
    string_list = []
    pos_list = []
    final_dict_list = []
    for line in align_file:
        line = line.strip()
        if line.startswith("# ::tok"):
            num_instance += 1
            print(num_instance)
            span2node = {}
            edge_label = {}
            string_list.append(line[8:])
            # print(line)
            # print(string_list)
            pos_list.append(nltk.pos_tag(line[8:].split(" ")))

        elif line.startswith("# ::node"):
            if len(line.split("\t")) > 3:
                node = line.split("\t")[-2] + "+" +line.split("\t")[-3]
                span = line.split("\t")[-1]
                if span not in span2node:
                    span2node[span] = [node]
                else:
                    span2node[span].append(node)
            # else:
                # print line
                # print("AMR node without alignment")
                # print(num_instance)

        elif line.startswith("# ::edge"):
            parent_id = line.split("\t")[-2]
            child_id = line.split("\t")[-1]
            arc_label = line.split("\t")[-4]
            if child_id not in edge_label:
                edge_label[child_id] = [(parent_id, arc_label)]
            else:
                edge_label[child_id].append((parent_id, arc_label))

        elif not line:
            mix_dict = {}
            index2node = {}
            for key, value in span2node.items():
                span = key
                start = int(span.split("-")[0])
                end = int(span.split("-")[-1])
                if (end - start) == 1:
                    mix_dict[end] = value
                    # print(span)
                    # print(value)
                else:
                    mix_dict[key] = value

            # print(mix_dict)

            for key, value in mix_dict.items():
                isOnlyDep = True
                date_entity = False
                # url_entity = False
                if len(value) == 1:  #One word invokes one node
                    index2node[key] = [value[0], 0, "_", 0, "_"]

                if isinstance(key, int) and len(value) > 1: #One word invokes multiple node_names
                    # print("One word invokes multiple node_names")
                    # print(key, value)
                    # exit()
                    for ele in value: #Check if node_names are only consist of preds and dependents.
                        if '"' in ele:
                            # print(ele)
                            isOnlyDep = False
                        elif ele[:11] == 'date-entity':
                            # print("Interesting! We merge node_names to get a special data-entity node.")
                            # print(value)
                            date_entity = True
                        # elif ele[:10] == 'url-entity':
                        #     if len(value) > 2:
                        #         print("Interesting! We merge node_names to get a special url-entity node.")
                        #         print(value)
                        #         url_entity = True

                    if date_entity:
                        index2node[key] = ["_", 0, "_", 1, 's'+value[0]]
                        continue

                    # print(isOnlyDep)
                    if isOnlyDep: #Nodes only consist of deps
                        counter = key
                        for i in range(len(value)):
                            if i == 0:
                                index2node[counter] = [value[i], i+1, "_", 0, "_"]
                            else:
                                index2node[counter] = ["_", i+1, value[i], 0, "_"]
                            counter += 0.1
                    else:
                        if (value[1][:4] == 'name') and ('"' in value[2]):
                            # Nodes only consist of Entity: EntityLabel+name+"China"
                            if (len(value) == 3):
                                index2node[key] = ["_", 0, "_", 1, 'EN' + value[0]]
                            else:
                                # print(num_instance)
                                print("Span does not match the entity node. ")
                                # print(value)
                                index2node[key] = ["_", 0, "_", 1, 'EN' + value[0]]

                        elif (len(value) == 2) and ('"' in value[1]):
                            #Nodes only consist of Entity: EntityLabel+"China"
                            # print(value)
                            if value[0][:4] == 'name':
                                # print(num_instance)
                                print("Entity without labels. (Wrong alignments)")
                                # print(value)
                                index2node[key] = ["_", 0, "_", 1, 'x' + value[0]]
                            else:
                                index2node[key] = ["_", 0, "_", 1, 'EN' + value[0]]

                        else:
                            # print("Nodes consist of preds+dependents+entity(with/without name")
                            #Nodes consist of preds+dependents+entity(with/without name)
                            counter = key
                            for i in range(len(value)):
                                print(value)
                                if '"' in value[i]:
                                    continue
                                elif value[i][:4] == 'name':
                                    continue
                                else:
                                    if i == 0:
                                        # We need to check if the first predicate node is the entity node, like: Country+name+"China"
                                        if value[i+1][:4] == 'name':
                                            index2node[counter] = ["EN" + value[i], i+1, "_", i+1, "_"]
                                        elif '"' in value[i + 1]:
                                            # print(value)
                                            index2node[counter] = ["EN" + value[i], i+1, "_", i+1, "_"]
                                        else:
                                            index2node[counter] = [value[i], i+1, "_", i+1, "_"]

                                    else:
                                        if value[i+1][:4] == 'name':
                                            index2node[counter] = ["_", i+1, 'EN'+value[i], i+1, "_"]
                                        elif '"' in value[i+1]:
                                            # print(value)
                                            index2node[counter] = ["_", i+1, 'EN' + value[i], i+1, "_"]
                                        else:
                                            index2node[counter] = ["_", i+1, value[i], i+1, "_"]
                                counter += 0.1
                                # print(index2node)


                # if isinstance(key, str) and len(value) == 1:
                    # print("Interesting...")

                if isinstance(key, str) and len(value) > 1:
                    head = int(key.split("-")[0])
                    end = int(key.split("-")[-1])
                    span_len = end - head

                    for ele in value: #Check if node_names are only consist of preds and dependents.
                        if '"' in ele:
                            isOnlyDep = False
                        elif ele[:11] == 'date-entity':
                            # print("Interesting! We merge node_names to get a special data-entity node.")
                            # print(value)
                            date_entity = True

                    if date_entity:
                        for i in range(span_len):
                            if i == (span_len - 1): #The index of the Last word in the span
                                index2node[end] = ["_", 0, "_", i+1, 's'+value[0]]
                            else:
                                index2node[head+(i+1)] = ["_", 0, "_", i+1, "_"]
                        continue

                    if isOnlyDep: #Nodes only consist of deps
                        for i in range(span_len):
                            if i == (span_len - 1): #The index of the Last word in the span
                                counter = end
                                for j in range(len(value)):
                                    if j == 0:
                                        index2node[counter] = [value[j], i+1, "_", 0, "_"]
                                    else:
                                        index2node[counter] = ["_", i+1, value[j], 0, "_"]
                                    counter += 0.1
                            else:
                                index2node[head+(i+1)] = ["_", i+1, "_", 0, "_"]

                    else:
                        if (value[1][:4] == 'name') and ('"' in value[2]):
                            #Nodes only consist of Entity: EntityLabel+name+"New"+"York"+"City"
                            if len(value) == (2+span_len):
                                for i in range(span_len):
                                    if i == (span_len - 1):
                                        index2node[end] = ["_", 0, "_", i + 1, "EN" + value[0]]
                                    else:
                                        index2node[head + (i + 1)] = ["_", 0, "_", i + 1, "_"]
                            else:
                                # print(num_instance)
                                print("Span does not match the entity node. ")
                                # print(key)
                                # print(value)
                                for i in range(span_len):
                                    if i == (span_len - 1):
                                        index2node[end] = ["_", 0, "_", i + 1, "EN" + value[0]]
                                    else:
                                        index2node[head + (i + 1)] = ["_", 0, "_", i + 1, "_"]


                        elif value[0][:4] == 'name':
                            #Wrong alignment, we lost the entity label for the span, only 'name' left.
                            # print(num_instance)
                            print("Entity without labels (Wrong alignment).")
                            # print(value)
                            for i in range(span_len):
                                if i == (span_len - 1):
                                    index2node[end] = ["_", 0, "_", i + 1, "x"+value[0]]
                                else:
                                    index2node[head + (i + 1)] = ["_", 0, "_", i + 1, "_"]

                        elif (len(value) == (1+span_len)) and ('"' in value[2]):
                            #Nodes only consist of Entity: EntityLabel+"New"+"York"+"City"

                            for i in range(span_len):
                                if i == (span_len - 1):
                                    # print(value)
                                    index2node[end] = ["_", 0, "_", i+1, "en"+value[0]]
                                else:
                                    index2node[head+(i+1)] = ["_", 0, "_", i+1, "_"]

                        else:
                            #Nodes consist of preds+dependents+entity(with/without name)
                            for i in range(span_len):
                                if i == (span_len - 1):
                                    counter = end
                                    for j in range(len(value)):
                                        if j == 0:
                                            #We need to check if the first predicate node is the entity node, like: Country+name+"New"+"York"
                                            if value[j+1][:4] == 'name':
                                                index2node[counter] = ["EN"+value[j], i + j + 1, "_", i + j + 1, "_"]
                                            elif '"' in value[j+1]:
                                                index2node[counter] = ["EN" + value[j], i + j + 1, "_", i + j + 1, "_"]
                                            else:
                                                index2node[counter] = [value[j], i+j+1, "_", i+j+1, "_"]
                                        elif j == len(value)-1:
                                            if value[j][:4] == 'name':
                                                continue
                                            elif '"' in value[j]:
                                                continue
                                            else:
                                                # Wrong alignment, we lost the entity label for the span, only 'name' left.
                                                # print(num_instance)
                                                # print("Interesting! We have predicates after entity node. ")
                                                # print(value)
                                                index2node[counter] = ["_", i + j + 1, value[j], i + j + 1, "_"]
                                        else:
                                            if value[j][:4] == 'name':
                                                continue
                                            elif '"' in value[j]:
                                                continue
                                            elif value[j+1][:4] == 'name':
                                                index2node[counter] = ["_", i+j+1, "EN"+value[j], i+j+1, "_"]
                                            elif '"' in value[j+1]:
                                                # print(value)
                                                index2node[counter] = ["_", i + j + 1, "EN" + value[j], i + j + 1, "_"]
                                            else:
                                                index2node[counter] = ["_", i + j + 1, value[j], i + j + 1, "_"]
                                        counter += 0.1
                                else:
                                    index2node[head+(i+1)] = ["_", i+1, "_", i+1, "_"]


            # print(index2node)

            full_dict = {}
            tok_list = string_list[-1].split(" ")
            lemma_list = []

            for item in tok_list:
                lemma_list.append(lemmatizer.lemmatize(item))

            # print(lemma_list)

            for i in range(len(tok_list)):
                match = False
                index = i + 1
                for key, value in index2node.items():
                    if index == key:
                        full_dict[index] = value
                        match = True
                        continue
                if not match:
                    full_dict[index] = ["_", 0, "_", 0, "_"]

            for key, value in index2node.items():
                if key not in full_dict.keys():
                    full_dict[key] = value
            for key, value in full_dict.items():
                if isinstance(key, int):
                    # print(pos_list[-1][key-1])
                    value.insert(0, pos_list[-1][key-1][1])
                    value.insert(0, lemma_list[key-1])
                    value.insert(0, tok_list[key-1])
                else:
                    value.insert(0, "_")
                    value.insert(0, "_")
                    value.insert(0, "_")

            predicate_id_list = []
            predicate_list = []

            # print(full_dict)
            for item in sorted(full_dict.items()):
                # print(item)
                if item[1][3] != '_':
                    predicate_list.append(item[1][3])
                    predicate_id_list.append(item[1][3].split("+")[1])
                elif item[1][5] != '_':
                    predicate_list.append(item[1][5])
                    predicate_id_list.append(item[1][5].split("+")[1])
                elif item[1][7] != '_':
                    predicate_list.append(item[1][7])
                    predicate_id_list.append(item[1][7].split("+")[1])

            predicate2index = {}
            for i in range(len(predicate_id_list)):
                predicate2index[predicate_id_list[i]] = i+1

            # print(predicate2index)
            # print(edge_label)
            # print("Predicate node_list is: ")
            # print(predicate_list)

            edge_filter = {}
            for child_id, tuple_list in edge_label.items():
                if child_id not in predicate2index.keys():
                    continue
                else:
                    parent_id_sublist = []
                    for parent_tuple in tuple_list:
                        if parent_tuple[0] in predicate2index.keys():
                            parent_id_sublist.append((predicate2index[parent_tuple[0]], parent_tuple[1]))
                    if len(parent_id_sublist) == 0:
                        continue
                    edge_filter[child_id] = parent_id_sublist

            # print("Edge filter is: ")
            # print(edge_filter)
            # print(full_dict)

            final_dict = {}
            for id, sublist in full_dict.items():
                if not sublist[3] == "_":
                    child_index = sublist[3].split("+")[1]
                    node_name = sublist[3].split("+")[0]
                elif not sublist[5] == "_":
                    child_index = sublist[5].split("+")[1]
                    node_name = sublist[5].split("+")[0]
                elif not sublist[7] == "_":
                    child_index = sublist[7].split("+")[1]
                    node_name = sublist[7].split("+")[0]
                else:
                    child_index = None
                    node_name = None

                # print(child_index)
                # print(node_name)

                if child_index:
                    if child_index in edge_filter.keys():
                        # print(child_index)
                        # print(node_name)
                        parent_list = edge_filter[child_index]
                        # print("parent_list is: ")
                        # print(parent_list)
                        for i in range(len(predicate_id_list)+1):
                            edge_label_added = False
                            for tuple in parent_list:
                                if tuple[0] == i + 1:
                                    edge_label_added = True
                                    sublist.append(tuple[1])
                                    continue
                            if edge_label_added:
                                continue
                            else:
                                sublist.append("_")
                    else:
                        if not child_index == '0':
                            # print(num_instance)
                            # print("We have edge labels but do not have node alignment. Sad...")
                            # print("Node is: "+sublist[3])
                            for i in range(len(predicate_id_list)+1):
                                sublist.append("_")
                        else: #for the root node, which has child_index = 0
                            # print("The Root Node is: "+sublist[3])
                            for i in range(len(predicate_id_list) + 1):
                                if i == len(predicate_id_list):
                                    sublist.append("root")
                                else:
                                    sublist.append("_")

                        # for i in range(len(predicate_id_list)+1):
                        #     sublist.append("_")
                else:
                    for i in range(len(predicate_id_list)+1):
                        sublist.append("_")

                if not sublist[3] == "_":
                    sublist[3] = node_name
                elif not sublist[5] == "_":
                    sublist[5] = node_name
                elif not sublist[7] == "_":
                    sublist[7] = node_name

                final_dict[id] = sublist

            # print(id)
            # print(sublist)
            root_list = []
            for i in range(len(sublist)):
                if i == 0 or i == 1 or i == 3:
                    root_list.append('ROOT')
                elif i == 2:
                    root_list.append('NOTAG')
                elif i == 4 or i == 6:
                    root_list.append(0)
                else:
                    root_list.append('_')

            final_dict[len(final_dict)+1] = root_list

            final_dict_list.append(final_dict)

    # print(final_dict_list)
    for i in range(len(final_dict_list)):
        id = 1
        for item in sorted(final_dict_list[i].items()):
            conll_file.write(str(id)+" ")
            for j in range(len(item[1])):
                conll_file.write(str(item[1][j])+" ")
            conll_file.write("\n")
            id += 1
        conll_file.write("\n")
