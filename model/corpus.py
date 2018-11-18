#-*- coding: utf-8 -*
import model.data_struct as ds
import model.action_2015 as act
# import model.action_2017 as act


class Corpus(object):

    def __init__(self):
        self.UNK = "UNK"

        self.correct_act_train = {}
        self.tokens_train = {}
        self.tokens_string_train = {}
        self.pos_train = {}
        self.tok_lemma_map_train = {}
        self.tok_lemma_string_train = {}
        self.num_sents = 0

        # self.correct_act_dev = {}
        self.tokens_dev = {}
        self.tokens_string_dev = {}
        self.pos_dev = {}
        self.tok_lemma_map_dev = {}
        self.tok_lemma_string_dev = {}
        self.num_sents_dev = 0

        self.act_dict = ds.Dict()
        self.act_types = set()
        self.all_corpus_acts = list()
        self.PR_UNK = "PR(UNK)"

        self.token_vocab_size = 0
        self.pos_vocab_size = 0

        self.tok_dict_train = ds.Dict()
        self.pos_dict = ds.Dict()
        self.lemma_dict = ds.Dict()

        '''For using pretrain embedding'''
        self.tok_dict_all = ds.Dict()
        self.tokens_train_raw = {}
        self.tokens_dev_raw = {}

        self.lemma_practs_map = {}

    def load_correct_actions(self, file):
        action_file = open(file, 'r')
        f = [l.strip() for l in action_file]

        assert self.token_vocab_size == 0
        assert self.pos_vocab_size == 0
        num_tokens = 0

        current_sent_tok = list()
        current_sent_string = list()
        current_sent_pos = list()
        current_sent_lemmas = {}
        current_tok_lemma_string = {}

        sent_idx = -1
        input_line = False
        first_ex = True

        for line in f:
            line.replace("-RRB-", "_RRB_")
            line.replace("-LRB-", "_LRB_")

            if not line:
                if not first_ex:
                    self.tokens_train[sent_idx] = current_sent_tok
                    self.tokens_string_train[sent_idx] = current_sent_string
                    self.pos_train[sent_idx] = current_sent_pos
                    self.tok_lemma_map_train[sent_idx] = current_sent_lemmas
                    self.tok_lemma_string_train[sent_idx] = current_tok_lemma_string

                else:
                    first_ex = False

                sent_idx += 1
                input_line = True

                current_sent_tok = list()
                current_sent_string = list()
                current_sent_pos = list()
                current_sent_lemmas = {}
                current_tok_lemma_string = {}

            elif input_line:
                if sent_idx % 1000 == 0:
                    print(str(sent_idx) + "...")

                pair_list = line.split(" ")

                for tok_pos_pair in pair_list:

                    if not tok_pos_pair.startswith("ROOT"):
                        tok_pos_pair = tok_pos_pair[:-1]

                    postag_char_idx = tok_pos_pair.find("`")
                    # pred_char_idx = tok_pos_pair.rfind("~")
                    pred_char_idx = tok_pos_pair.rfind("`")

                    assert postag_char_idx != -1
                    assert pred_char_idx != -1

                    pos = tok_pos_pair[postag_char_idx+1:pred_char_idx]
                    pos_id = self.pos_dict.string_convert(pos)
                    self.pos_vocab_size = self.pos_dict.get_size()
                    current_sent_pos.append(pos_id)

                    token = tok_pos_pair[:postag_char_idx]
                    self.tok_dict_all.string_convert(token)
                    tok_id = self.tok_dict_train.string_convert(token)
                    self.token_vocab_size = self.tok_dict_train.get_size()
                    num_tokens += 1
                    current_sent_tok.append(tok_id)
                    current_sent_string.append(token)

                    pred = tok_pos_pair[pred_char_idx+1:]
                    self.lemma_dict.string_convert(pred)
                    current_sent_lemmas[len(current_sent_tok)-1] = self.lemma_dict.string_convert(pred)
                    current_tok_lemma_string[len(current_sent_tok)-1] = (pred, pos)

                input_line = False

            elif not input_line:
                act_idx = self.act_dict.string_convert(line)
                if sent_idx not in self.correct_act_train.keys():
                    self.correct_act_train[sent_idx] = [act_idx]
                else:
                    self.correct_act_train[sent_idx].append(act_idx)

        if len(current_sent_tok) > 0:
            self.tokens_train[sent_idx] = current_sent_tok
            self.tokens_string_train[sent_idx] = current_sent_string
            self.pos_train[sent_idx] = current_sent_pos
            self.tok_lemma_map_train[sent_idx] = current_sent_lemmas
            self.tok_lemma_string_train[sent_idx] = current_tok_lemma_string
            sent_idx += 1

        action_file.close()
        self.num_sents = sent_idx

        print("done reading training actions file")
        print("#sents: " + str(self.num_sents))
        print("#tokens: " + str(num_tokens))
        print("#types: " + str(self.token_vocab_size))
        print("#POStags: " + str(self.pos_vocab_size))
        print("#actions: " + str(self.act_dict.get_size()))
        print("#preds: " + str(self.lemma_dict.get_size()))

    def get_some_act_label(self, act_labels_dict):
        for idx in range(len(self.all_corpus_acts)):
            aname = self.all_corpus_acts[idx]
            if aname not in act_labels_dict.keys():
                act_string = self.act_dict.index_convert(idx)
                act_labels_dict[aname] = act_string

    def get_or_add_word_train(self, word):
        return self.tok_dict_train.string_convert(word)

    def get_or_add_word_all(self, word):
        return self.tok_dict_all.string_convert(word)

    def load_correct_actions_dev(self, file):
        action_file = open(file, 'r')
        f = [l.strip() for l in action_file]

        self.tok_dict_train.freeze()
        self.tok_dict_train.set_unk(self.UNK)

        self.act_dict.freeze()
        self.act_dict.set_unk(self.PR_UNK)

        act.get_all_acts(self.act_dict, self.all_corpus_acts, self.act_types)

        some_label = {}
        self.get_some_act_label(some_label)

        self.lemma_dict.freeze()
        self.lemma_dict.set_unk(self.UNK)

        current_sent = list()
        current_sent_string = list()
        current_posseq = list()
        current_sent_lemmas = {}
        current_tok_lemma_string = {}

        sent_idx = -1
        inp_line = False
        first_ex = True

        num_tokens = 0

        for line in f:
            # print line
            line.replace("-RRB-", "_RRB_")
            line.replace("-LRB-", "_LRB_")

            if not line:
                if not first_ex:
                    self.tokens_dev[sent_idx] = current_sent
                    self.tokens_string_dev[sent_idx] = current_sent_string
                    self.pos_dev[sent_idx] = current_posseq
                    self.tok_lemma_map_dev[sent_idx] = current_sent_lemmas
                    self.tok_lemma_string_dev[sent_idx] = current_tok_lemma_string

                else:
                    first_ex = False

                sent_idx += 1
                input_line = True

                current_sent = list()
                current_posseq = list()
                current_sent_string = list()
                current_sent_lemmas = {}
                current_tok_lemma_string = {}

            elif input_line:
                if sent_idx % 1000 == 0:
                    print(str(sent_idx) + "...")

                pair_list = line.split(" ")

                for tok_pos_pair in pair_list:

                    if not tok_pos_pair.startswith("ROOT"):
                        tok_pos_pair = tok_pos_pair[:-1]

                    postag_char_idx = tok_pos_pair.find("`")
                    # pred_char_idx = tok_pos_pair.rfind("~")
                    pred_char_idx = tok_pos_pair.rfind("`")
                    # print(pred_char_idx)

                    # if postag_char_idx == -1:
                    #     print(tok_pos_pair)
                    #     exit()
                    assert postag_char_idx != -1
                    assert pred_char_idx != -1

                    pos = tok_pos_pair[postag_char_idx+1:pred_char_idx]
                    pos_id = self.pos_dict.string_convert(pos)
                    self.pos_vocab_size = self.pos_dict.get_size()
                    current_posseq.append(pos_id)

                    token = tok_pos_pair[:postag_char_idx]
                    self.tok_dict_all.string_convert(token)
                    tok_id = self.tok_dict_train.string_convert(token)
                    self.token_vocab_size = self.tok_dict_train.get_size()
                    num_tokens += 1
                    current_sent.append(tok_id)
                    current_sent_string.append(token)

                    pred = tok_pos_pair[pred_char_idx+1:]
                    self.lemma_dict.string_convert(pred)
                    current_sent_lemmas[len(current_sent)-1] = self.lemma_dict.string_convert(pred)
                    current_tok_lemma_string[len(current_sent)-1] = (pred, pos)

                input_line = False

        if len(current_sent) > 0:
            self.tokens_dev[sent_idx] = current_sent
            self.pos_dev[sent_idx] = current_posseq
            self.tok_lemma_map_dev[sent_idx] = current_sent_lemmas
            self.tokens_string_dev[sent_idx] = current_sent_string
            self.tok_lemma_string_dev[sent_idx] = current_tok_lemma_string
            sent_idx += 1

        action_file.close()
        self.num_sents_dev = sent_idx

        self.tok_dict_all.freeze()

        print("done reading training actions file")
        print("#sents: " + str(self.num_sents_dev))
        print("#tokens: " + str(num_tokens))
        print("#types: " + str(self.token_vocab_size))
        print("#POStags: " + str(self.pos_vocab_size))
        print("#actions: " + str(self.act_dict.get_size()))
        print("#action types: " + str(len(self.act_types)))
        print("#preds: " + str(self.lemma_dict.get_size()))

    def load_train_preds(self, file):
        print("Start loading preds")

        pred_file = open(file, 'r')
        f = [l.strip() for l in pred_file]

        for line in f:
            isfirst = True
            lemma_id = 0
            pred_acts = list()

            lemma_act_list = line.split("\t")

            for ele in lemma_act_list:
                # print(ele)
                # print(self.lemma_dict.get_dict())
                if isfirst:
                    if self.lemma_dict.contains_word(ele):
                        lemma_id = self.lemma_dict.string_convert(ele)
                    else:
                        print("lemma not found " + ele)
                    isfirst = False
                else:
                    if self.act_dict.contains_word(ele):
                        pred_acts.append(self.act_dict.string_convert(ele))
                    else:
                        print("predicate act " + ele + "not found")

            self.lemma_practs_map[lemma_id] = pred_acts

        pred_file.close()
        print("#lemmas with associated PR acts = " + str(len(self.lemma_practs_map)))

    def load_raw_sent(self, file, options, tok_dict_pretrain):

        if options == "train":
            train = True
        else:
            train = False

        action_file = open(file, 'r')
        f = [l.strip() for l in action_file]

        current_sent_tok = list()

        sent_idx = -1
        input_line = False
        first_ex = True

        for line in f:
            line.replace("-RRB-", "_RRB_")
            line.replace("-LRB-", "_LRB_")

            if not line:
                if not first_ex:
                    if train:
                        self.tokens_train_raw[sent_idx] = current_sent_tok
                    else:
                        self.tokens_dev_raw[sent_idx] = current_sent_tok
                else:
                    first_ex = False

                sent_idx += 1
                input_line = True

                current_sent_tok = list()

            elif input_line:
                if sent_idx % 1000 == 0:
                    print(str(sent_idx) + "...")

                pair_list = line.split(" ")

                for tok_pos_pair in pair_list:

                    if not tok_pos_pair.startswith("ROOT"):
                        tok_pos_pair = tok_pos_pair[:-1]

                    postag_char_idx = tok_pos_pair.find("`")

                    token = tok_pos_pair[:postag_char_idx]
                    tok_id = tok_dict_pretrain.string_convert(token)
                    current_sent_tok.append(tok_id)

                input_line = False

            elif not input_line:
                continue

        if len(current_sent_tok) > 0:
            if train:
                self.tokens_train_raw[sent_idx] = current_sent_tok
            else:
                self.tokens_dev_raw[sent_idx] = current_sent_tok
            sent_idx += 1

        action_file.close()

        print("done loading raw sent")
        print("#sents: " + str(sent_idx))