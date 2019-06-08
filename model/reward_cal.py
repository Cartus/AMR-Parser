# -*- coding: utf-8 -*

import model.SMATCH as smatch


def reward_cal(predicted, corpus, sent_string, tok_lemma_string, action_list, unk_prob, index, gold_amr, output_file=None):
    tokens = list()
    for pos_idx in sorted(predicted.pos_index):
        if pos_idx - int(pos_idx) == 0:
            tokens.append(sent_string[pos_idx])

    merge_index = list()
    for merge_idx in sorted(predicted.mer_pos):
        merge_index.append(int(merge_idx))

    node_list = list()
    for child_idx, parent_list in predicted.edges.items():
        for parent in parent_list:
            node_list.append((float(parent.head), float(child_idx), parent.label[3:-1]))

    node_names = {}
    if unk_prob > 0:
        for pred_idx, pred_name in predicted.predicate_lemmas.items():
            if pred_name == "PR(UNK)":
                # print(tok_lemma_string)
                lemma_name, lemma_pos = tok_lemma_string[pred_idx]

                if "'" in lemma_name or ":" in lemma_name:  # For 've-01 and 2:00
                    print("Special UNK token: " + lemma_name)
                    if lemma_name[1] == "'":
                        node_names[pred_idx] = lemma_name.lower()
                    else:
                        node_names[pred_idx] = '"' + lemma_name + '"'
                        continue

                if lemma_pos[:2] == "VB":
                    if lemma_name[-3:] == "ing" and lemma_name != "bring":
                        node_names[pred_idx] = lemma_name[:-3].lower() + "-01"
                    else:
                        node_names[pred_idx] = lemma_name.lower() + "-01"
                else:
                    if lemma_pos == "RB" and lemma_name[-3:] == "lly":
                        node_names[pred_idx] = lemma_name[:-2].lower()
                    elif lemma_pos == "NN" and (lemma_name[-4:] == "tion" or lemma_name[-3:] == "ing"):
                        node_names[pred_idx] = lemma_name[:-3].lower() + "e"
                    else:
                        node_names[pred_idx] = lemma_name.lower()
                        # print(node_names[pred_idx])
            else:
                node_names[pred_idx] = pred_name[3:-1]

    else:
        for pred_idx, pred_name in predicted.predicate_lemmas.items():
            node_names[pred_idx] = pred_name[3:-1]

    for ent_idx, ent_name in predicted.entity_lemmas.items():
        node_names[ent_idx] = ent_name[4:-1]

    for gen_idx, gen_name in predicted.gen_lemmas.items():
        node_names[gen_idx] = gen_name[4:-1]

    try:
        score, precision, recall = smatch.get_reward(node_list, node_names, tokens, merge_index, gold_amr, output_file)
    except:
        print(index)
        # print(node_list)
        # print(node_names)
        # print(tokens)
        # print(merge_index)
        # print([corpus.act_dict.index_convert(act) for act in action_list])
        print(gold_amr)
        score = 0.0
        precision = 0.0
        recall = 0.0

    return float(score), float(precision), float(recall)

