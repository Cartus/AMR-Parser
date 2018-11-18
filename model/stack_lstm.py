# -*- coding: utf-8 -*

from operator import itemgetter
from copy import deepcopy
from random import choice
import dynet as dy
import numpy as np
import model.action_2015 as act
# import model.action_2017 as act
import model.data_struct as ds


class ParserBuilder(object):

    def __init__(self, corpus, emb_file, tok_dict_pretrain, full_vocab, vocab_size_train, vocab_size_pretrain, unk_prob, layers, pretrain_dim, input_dim, pos_dim, lstm_input_dim, hidden_dim, action_dim, pred_dim, rel_dim, ent_dim, gen_dim, drop_out, reent_max, reent_nodes, merge_max, gen_max, forbid_cycle):

        self.pc = dy.ParameterCollection()
        self.corpus = corpus
        self.unk_prob = unk_prob
        self.dropout = drop_out

        action_size = corpus.act_dict.get_size() + 1
        pos_size = corpus.act_dict.get_size() + 10

        print('Rand word embedding size: ' + str(vocab_size_train))  # Should equal to the number of token types in the training corpus + UNK
        print('Pretrained word embedding size: ' + str(vocab_size_pretrain))  # Should equal to the size of train corpus (shrink_train) / train+test corpus (shrink_corpus) / train+test+emb_file (no_shrink)

        self.stack_lstm = dy.LSTMBuilder(layers, lstm_input_dim, hidden_dim, self.pc)
        self.buffer_lstm = dy.LSTMBuilder(layers, lstm_input_dim, hidden_dim, self.pc)
        self.action_lstm = dy.LSTMBuilder(layers, action_dim, hidden_dim, self.pc)

        self.p_tok = self.pc.add_lookup_parameters((vocab_size_train, input_dim))
        self.p_pred = self.pc.add_lookup_parameters((action_size, pred_dim))
        self.p_act = self.pc.add_lookup_parameters((action_size, action_dim))
        self.p_edge_label = self.pc.add_lookup_parameters((action_size, rel_dim))
        self.p_ent = self.pc.add_lookup_parameters((action_size, ent_dim))
        self.p_gen = self.pc.add_lookup_parameters((action_size, gen_dim))

        self.p_pos = self.pc.add_lookup_parameters((pos_size, pos_dim))
        self.p_pos2l = self.pc.add_parameters((lstm_input_dim, pos_dim))

        self.p_emb = self.pc.add_lookup_parameters((vocab_size_pretrain, pretrain_dim)) # For 1000 test.vectors (sample of pretrained embeddings)
        self.p_emb2l = self.pc.add_parameters((lstm_input_dim, pretrain_dim))
        self.embedding_initialize(emb_file, tok_dict_pretrain, full_vocab)

        self.p_parstate_bias = self.pc.add_parameters((hidden_dim, 1))
        self.p_act2parsact = self.pc.add_parameters((hidden_dim, hidden_dim))
        self.p_buf2parsact = self.pc.add_parameters((hidden_dim, hidden_dim))
        self.p_sems2parsact = self.pc.add_parameters((hidden_dim, hidden_dim))

        self.p_head_comp = self.pc.add_parameters((lstm_input_dim, lstm_input_dim))
        self.p_mod_comp = self.pc.add_parameters((lstm_input_dim, lstm_input_dim))
        self.p_label_comp = self.pc.add_parameters((lstm_input_dim, rel_dim))
        self.p_comp_bias = self.pc.add_parameters((lstm_input_dim, 1))

        self.p_pred_comp = self.pc.add_parameters((lstm_input_dim, pred_dim))
        self.p_pred_comp_bias = self.pc.add_parameters((lstm_input_dim, 1))

        self.p_ent_comp = self.pc.add_parameters((lstm_input_dim, ent_dim))
        self.p_ent_comp_bias = self.pc.add_parameters((lstm_input_dim, 1))

        self.p_tok2l = self.pc.add_parameters((lstm_input_dim, input_dim))
        self.p_inp_bias = self.pc.add_parameters((lstm_input_dim, 1))

        self.p_parse2next_act = self.pc.add_parameters((action_size, hidden_dim))
        self.p_act_bias = self.pc.add_parameters((action_size, 1))

        self.p_act_start = self.pc.add_parameters((action_dim, 1))
        self.p_buf_guard = self.pc.add_parameters((lstm_input_dim, 1))
        self.p_stack_guard = self.pc.add_parameters((lstm_input_dim, 1))

        self.p_W_satb = self.pc.add_parameters((1, hidden_dim * 2))
        self.p_bias_satb = self.pc.add_parameters((1))

        self.reent_max = reent_max
        self.reent_nodes = reent_nodes
        self.merge_max = merge_max
        self.forbid_cyc = forbid_cycle
        self.gen_max = gen_max

    def embedding_initialize(self, emb_file, tok_dict_pretrain, full_vocab):
        '''initialize with pre-trained word embedding'''

        print('loading pretrained word embeddings')
        kUNK = tok_dict_pretrain.string_convert("UNK")

        for line in open(emb_file, 'r'):
            line = line.strip().split(' ')
            if len(line) > 2:
                word, embedding = line[0], [float(f) for f in line[1:]]

                if word in full_vocab:
                    wid = tok_dict_pretrain.string_convert(word)
                    if wid == kUNK:
                        print("UNK tokens encountered")
                        exit()
                    self.p_emb.init_row(wid, embedding)
                else:
                    continue

        print('finish loading')

    def save_model(self, filename):
        '''save the model'''
        self.pc.save(filename)

    def load_model(self, filename):
        '''load the model'''
        self.pc.populate(filename)

    def parsing(self, sent_string, raw_sent, sent, pos_seq, tok_lemma_map, epsilon, oracle_actions=None):
        '''parse the given sentence'''

        dy.renew_cg()

        reent_node_dict = {}
        reent_num = 0
        gen_num = 0
        root_id = len(sent) - 1

        action_list = list()

        if oracle_actions:
            oracle_actions = list(oracle_actions)
            oracle_actions.reverse()
            build_training_graph = True
        else:
            build_training_graph = False

        if build_training_graph:
            self.stack_lstm.set_dropout(self.dropout)
            self.buffer_lstm.set_dropout(self.dropout)
            self.action_lstm.set_dropout(self.dropout)
        else:
            self.stack_lstm.disable_dropout()
            self.buffer_lstm.disable_dropout()
            self.action_lstm.disable_dropout()

        parstate_bias = dy.parameter(self.p_parstate_bias)

        head_comp = dy.parameter(self.p_head_comp)
        mod_comp = dy.parameter(self.p_mod_comp)
        label_comp = dy.parameter(self.p_label_comp)
        comp_bias = dy.parameter(self.p_comp_bias)

        pred_comp = dy.parameter(self.p_pred_comp)
        pred_comp_bias = dy.parameter(self.p_pred_comp_bias)

        ent_comp = dy.parameter(self.p_ent_comp)
        ent_comp_bias = dy.parameter(self.p_ent_comp_bias)

        semst2next_act = dy.parameter(self.p_sems2parsact)
        buf2next_act_att = dy.parameter(self.p_buf2parsact)
        act2next_act = dy.parameter(self.p_act2parsact)

        tok2lstm = dy.parameter(self.p_tok2l)

        pos2lstm = dy.parameter(self.p_pos2l)

        emb2lstm = dy.parameter(self.p_emb2l)

        inp_bias = dy.parameter(self.p_inp_bias)

        state2next_act = dy.parameter(self.p_parse2next_act)
        act_bias = dy.parameter(self.p_act_bias)

        W_satb = dy.parameter(self.p_W_satb)
        bias_satb = dy.parameter(self.p_bias_satb)

        stack_state = self.stack_lstm.initial_state()
        buffer_state = self.buffer_lstm.initial_state()
        action_state = self.action_lstm.initial_state()

        act_start = dy.parameter(self.p_act_start)
        action_state_list = list()
        action_state = action_state.add_input(act_start)
        action_state_list.append(action_state)

        buffer = list()
        buffer_state = buffer_state.add_input(dy.parameter(self.p_buf_guard))
        buffer_guard_state = buffer_state

        for i in range(len(sent)):
            word_embedding = dy.lookup(self.p_tok, sent[i])
            pos_embedding = dy.lookup(self.p_pos, pos_seq[i])
            pretrain_embedding = dy.lookup(self.p_emb, raw_sent[i], update=False)

            i_i = dy.rectify(dy.affine_transform([inp_bias, tok2lstm, word_embedding, pos2lstm, pos_embedding, emb2lstm, pretrain_embedding]))
            buffer_state = buffer_state.add_input(i_i)
            buffer.insert(0, (buffer_state, i_i, i))

        buffer.insert(0, (buffer_guard_state, dy.parameter(self.p_buf_guard), -999))
        # print(buffer)

        stack = list()
        stack_state = stack_state.add_input(dy.parameter(self.p_stack_guard))
        stack.append((stack_state, dy.parameter(self.p_stack_guard), -999))

        losses = list()
        partial = ds.JointParse()

        prev_act_enum = act.act_name.SHIFT
        prev2_act_enum = act.act_name.SHIFT
        prev3_act_enum = act.act_name.SHIFT
        prev_act_id = 999

        while len(buffer) > 1 or len(stack) > 2:

            valid_actions = list()
            valid_action_types = set()

            buffer_front_index = buffer[-1][2]
            stack_top_index = stack[-1][2]

            # print(buffer_front_index)
            # print(stack_top_index)

            for act_enum in self.corpus.act_types:
                is_forbidden = act.is_joint_action_forbidden(act_enum, prev_act_enum, prev2_act_enum, prev3_act_enum, len(buffer), len(stack), stack_top_index, buffer_front_index, sent_string, reent_node_dict, reent_num,
                                                         self.reent_max, self.reent_nodes, self.merge_max, self.forbid_cyc, self.gen_max, gen_num, partial)

                if not is_forbidden:
                    valid_action_types.add(act_enum)

            # print(valid_action_types)

            if act.act_name.PRED in valid_action_types:
                if buffer_front_index in tok_lemma_map.keys(): # this makes sure that current element is original token in the sent rather than generated nodes, because every token has its lemma.
                    if sent[buffer_front_index] == self.corpus.get_or_add_word_train("UNK"):
                        valid_actions.append(self.corpus.act_dict.string_convert(self.corpus.PR_UNK))
                    else:
                        lemma_id = tok_lemma_map[buffer_front_index]
                        if lemma_id in self.corpus.lemma_practs_map.keys():
                            valid_actions = deepcopy(self.corpus.lemma_practs_map[lemma_id])

            if prev_act_id != 999:
                for i in range(len(self.corpus.all_corpus_acts)):
                    act_type = self.corpus.all_corpus_acts[i]
                    if act_type in valid_action_types and act_type != act.act_name.PRED:
                        valid_actions.append(i)
            else:
                for i in range(len(self.corpus.all_corpus_acts)):
                    act_type = self.corpus.all_corpus_acts[i]
                    if act_type in valid_action_types and act_type != act.act_name.PRED:
                        valid_actions.append(i)

            # print([self.corpus.act_dict.index_convert(action) for action in valid_actions])

            alpha = list()
            buf_mat = list()
            for i in range(len(buffer)):
                b_fwh = buffer[i][0].output()
                buf_mat.append(b_fwh)
                s_b = dy.concatenate([stack[-1][0].output(), b_fwh])
                alpha.append(dy.rectify(bias_satb + W_satb * s_b))

            ae = dy.softmax(dy.concatenate(alpha))
            buffer_mat = dy.concatenate_cols(buf_mat)
            buf_rep = buffer_mat * ae

            rectified_parstate = dy.rectify(parstate_bias + semst2next_act * stack[-1][0].output() + buf2next_act_att * buf_rep + act2next_act * action_state_list[-1].output())

            if build_training_graph:
                pars_act = dy.dropout(dy.affine_transform([act_bias, state2next_act, rectified_parstate]), self.dropout)
            else:
                pars_act = dy.affine_transform([act_bias, state2next_act, rectified_parstate])

            log_probs = dy.log_softmax(pars_act, valid_actions)

            action_predict = max(enumerate(log_probs.vec_value()), key=itemgetter(1))[0]

            if oracle_actions is not None:
                if len(oracle_actions) == 0:
                    if np.random.uniform(0, 1) < epsilon:
                        action_idx = choice(valid_actions)
                    else:
                        action_idx = action_predict
                else:
                    action_idx = oracle_actions.pop()
            else:
                action_idx = action_predict

            action_list.append(action_idx)

            losses.append(dy.pick(log_probs, action_idx))
            # if str(dy.pick(log_probs, action_idx).scalar_value()) == '-inf':
            #     exit()

            action_embedding = self.p_act[action_idx]
            action_state_list.append(action_state_list[-1].add_input(action_embedding))

            label = self.p_edge_label[action_idx]

            chosen_act_enum = self.corpus.all_corpus_acts[action_idx]
            # print(chosen_act_enum)
            # print(self.corpus.act_dict.index_convert(action_idx))

            if chosen_act_enum == act.act_name.SHIFT:
                assert len(buffer) > 1

                _, tok_embed, tok_index = buffer.pop()

                stack_state = stack[-1][0].add_input(tok_embed)
                stack.append((stack_state, tok_embed, tok_index))

                partial.pos_index.add(tok_index)

            elif chosen_act_enum == act.act_name.LEFTLABEL:
                assert len(stack) > 1
                assert len(buffer) > 1

                head_state, head_rep, head_index = buffer.pop()
                _, mod_rep, mod_index = stack[-1]

                composed = dy.tanh(dy.affine_transform([comp_bias, head_comp, head_rep, mod_comp, mod_rep, label_comp, label]))

                buffer.append((head_state.add_input(composed), composed, head_index))

                par = ds.Parent(head_index, self.corpus.act_dict.index_convert(action_idx))
                parents = list()

                if mod_index in partial.edges.keys():
                    parents = partial.edges[mod_index]

                if len(parents) > 0:
                    reent_num += 1

                if not mod_index in reent_node_dict.keys():
                    reent_node_dict[mod_index] = 1
                else:
                    reent_node_dict[mod_index] += 1

                parents.append(par)
                partial.edges[mod_index] = parents

                if head_index == root_id:
                    partial.root_connected = True

            elif chosen_act_enum == act.act_name.RIGHTLABEL:
                assert len(stack) > 1
                assert len(buffer) > 1

                head_state, head_rep, head_index = stack.pop()
                _, mod_rep, mod_index = buffer[-1]

                composed = dy.tanh(dy.affine_transform([comp_bias, head_comp, head_rep, mod_comp, mod_rep, label_comp, label]))

                stack.append((head_state.add_input(composed), composed, head_index))

                par = ds.Parent(head_index, self.corpus.act_dict.index_convert(action_idx))
                parents = list()

                if mod_index in partial.edges.keys():
                    parents = partial.edges[mod_index]

                if len(parents) > 0:
                    reent_num += 1

                if not mod_index in reent_node_dict.keys():
                    reent_node_dict[mod_index] = 1
                else:
                    reent_node_dict[mod_index] += 1

                parents.append(par)
                partial.edges[mod_index] = parents

            elif chosen_act_enum == act.act_name.REDUCE:
                assert len(stack) > 1

                stack.pop()

            elif chosen_act_enum == act.act_name.SWAP:
                assert len(stack) > 2

                _, top_rep, top_index = stack.pop()
                _, next_top_rep, next_top_index = stack.pop()

                stack.append((stack[-1][0].add_input(top_rep), top_rep, top_index))
                stack.append((stack[-1][0].add_input(next_top_rep), next_top_rep, next_top_index))

            elif chosen_act_enum == act.act_name.PRED:
                assert len(buffer) > 1

                head_state, head_rep, head_index = buffer.pop()
                pred = self.p_pred[action_idx]

                composed = dy.tanh(dy.affine_transform([pred_comp_bias, head_comp, head_rep, pred_comp, pred]))

                buffer.append((buffer[-1][0].add_input(composed), composed, head_index))

                partial.pred_pos.add(head_index)
                partial.node_pos.add(head_index)
                partial.predicate_lemmas[head_index] = self.corpus.act_dict.index_convert(action_idx)

            elif chosen_act_enum == act.act_name.ENTITY:
                assert len(buffer) > 1

                head_state, head_rep, head_index = buffer.pop()
                ent = self.p_ent[action_idx]

                composed = dy.tanh(dy.affine_transform([ent_comp_bias, head_comp, head_rep, ent_comp, ent]))

                buffer.append((buffer[-1][0].add_input(composed), composed, head_index))

                partial.ent_pos.add(head_index)
                partial.node_pos.add(head_index)
                partial.entity_lemmas[head_index] = self.corpus.act_dict.index_convert(action_idx)

            elif chosen_act_enum == act.act_name.MERGE:
                assert len(buffer) > 1
                assert len(stack) > 1

                head_state, head_rep, head_index = buffer.pop()
                _, mod_rep, _ = stack.pop()

                composed = dy.tanh(dy.affine_transform([comp_bias, head_comp, head_rep, mod_comp, mod_rep]))

                buffer.append((buffer[-1][0].add_input(composed), composed, head_index))

                partial.mer_pos.add(head_index)

            elif chosen_act_enum == act.act_name.GENERATE:
                assert len(buffer) > 1

                gen = self.p_gen[action_idx]

                _, front_rep, front_index = buffer.pop()

                if prev_act_enum == act.act_name.GENERATE and prev2_act_enum == act.act_name.GENERATE:
                    next_front_index = front_index + 0.1
                elif prev_act_enum == act.act_name.GENERATE and prev2_act_enum != act.act_name.GENERATE:
                    next_front_index = front_index + 0.2
                else:
                    next_front_index = front_index + 0.4

                buffer.append((buffer[-1][0].add_input(gen), gen, next_front_index))
                buffer.append((buffer[-1][0].add_input(front_rep), front_rep, front_index))

                partial.gen_pos.add(next_front_index)
                partial.node_pos.add(next_front_index)
                partial.gen_lemmas[next_front_index] = self.corpus.act_dict.index_convert(action_idx)

            else:
                print("Crazy action!" + self.corpus.act_dict.index_convert(action_idx))
                exit(1)

            prev3_act_enum = prev2_act_enum
            prev2_act_enum = prev_act_enum
            prev_act_enum = chosen_act_enum
            prev_act_id = action_idx
            # print partial

        assert len(stack) == 2
        assert len(buffer) == 1

        return losses, partial, action_list
