#!/usr/bin/env python3
# -*- coding: utf-8 -*

from __future__ import print_function
from copy import deepcopy
from model.stack_lstm import ParserBuilder
from model.reward_cal import reward_cal
import dynet as dy
import numpy as np
import model.evaluation as eval
import model.utils as utils
import numpy.random as RNG
import argparse
import model.corpus as corpus


def parsing_options():

    parser = argparse.ArgumentParser(description='Training transition-based AMR parser')
    parser.add_argument('--emb_file', default='data/sskip.100.vectors', help='path to pre-trained embedding')
    parser.add_argument('--train_file', default='data/train.transitions', help='path to training file')
    parser.add_argument('--dev_file', default='data/dev.transitions', help='path to development file')
    parser.add_argument('--lemma_practs', default='data/train.txt.pb.lemmas', help='lemmas mapped to PR() operations')
    parser.add_argument('--model', default='result/pretrain14.model', help='path to save pretrain model')
    parser.add_argument('--load_model', type=int, default=-1, help='set to -1 if we do not have pretrained model')
    parser.add_argument('--gold_AMR_dev', default='data/amr/tmp_amr/dev/amr.txt', help='Gold AMR graph for calculating SMATCH score during dev')

    parser.add_argument('--input_dim', type=int, default=32, help='dimension for word embedding')
    parser.add_argument('--action_dim', type=int, default=200, help='dimension for action embedding')
    parser.add_argument('--pos_dim', type=int, default=12, help='dimension for pos tag embedding')
    parser.add_argument('--rel_dim', type=int, default=20, help='dimension for relation embedding')
    parser.add_argument('--pred_dim', type=int, default=100, help='dimension for predicate embedding')
    parser.add_argument('--ent_dim', type=int, default=100, help='dimension for entity embedding')
    parser.add_argument('--gen_dim', type=int, default=100, help='dimension for generated node embedding')
    parser.add_argument('--hidden_dim', type=int, default=200, help='hidden dimension')
    parser.add_argument('--lstm_input_dim', type=int, default=100, help='lstm dimension')
    parser.add_argument('--pretrain_dim', type=int, default=100, help='pretrained word embedding dimension')
    parser.add_argument('--layers', type=int, default=2, help='number of LSTM layers')

    parser.add_argument("--reent_max", dest="reent_max", type=int, default=7, help="upper bound of all reentrancy of a graph")
    parser.add_argument("--reent_nodes", dest="reent_nodes", type=int, default=2, help="upper bound of the number of reentrancy nodes")
    parser.add_argument("--merge_max", dest="merge_max", type=int, default=11, help="upper bound of the number of consecutive merge operations") # For AMR-2014 corpus
    parser.add_argument("--gen_max", dest="gen_max", type=int, default=14, help="upper bound of the number of generate operations in a sentence")
    parser.add_argument("--forbid_cycle", dest="forbid_cycle", default=True, help="parser forbid actions to form cycles")

    parser.add_argument('--drop_out', type=float, default=0.2, help='dropout ratio')
    parser.add_argument('--unk_prob', type=float, default=0.2, help='probably with which to replace singletons with UNK in training data')
    parser.add_argument('--freq', type=int, default=1000, help='frequence of calculating the Smatch score of the dev set')
    parser.add_argument('--best_smatch', type=float, default=0, help='threshold to save the model')

    args = parser.parse_args()

    return args


def evaluation_dev(corpus, parser, best_SMATCH, e, gold_amr_dev):

    print('Evaluation on dev set')
    dev_size = corpus.num_sents_dev

    score_dic = {}
    precision_dic = {}
    recall_dic = {}

    for dev_id in range(dev_size):
        dev_sent_raw = corpus.tokens_dev_raw[dev_id]
        dev_sent = corpus.tokens_dev[dev_id]
        dev_pos = corpus.pos_dev[dev_id]
        dev_sent_string = corpus.tokens_string_dev[dev_id]
        tok_lemma_map_dev = corpus.tok_lemma_map_dev[dev_id]
        tok_lemma_string = corpus.tok_lemma_string_dev[dev_id]

        _, predicted_dev, action_list = parser.parsing(dev_sent_string, dev_sent_raw, dev_sent, dev_pos, tok_lemma_map_dev, 0)

        score, precision, recall = reward_cal(predicted_dev, corpus, dev_sent_string, tok_lemma_string, action_list, args.unk_prob, dev_id, gold_amr_dev[dev_id])

        score_dic[dev_id] = float(score)
        precision_dic[dev_id] = float(precision)
        recall_dic[dev_id] = float(recall)

    score_dev = sum(score_dic.values()) / dev_size
    precision_dev = sum(precision_dic.values()) / dev_size
    recall_dev = sum(recall_dic.values()) / dev_size

    print("SMATCH score: %.4f, Precision: %.4f, Recall: %.4f" % (score_dev, precision_dev, recall_dev))

    if score_dev > best_SMATCH:
         print("Saving model epoch%03d.model".format(e))
        save_as = '%s/epoch%03d.model' % (args.model, e)
        parser.save_model(save_as)


def train(corpus, args, parser, gold_amr_dev):

    trainer = dy.SimpleSGDTrainer(parser.pc)

    instances_processed = 0
    order = [i for i in range(corpus.num_sents)]

    print("start pretraining the model")

    ckt = 0

    for epoch_idx in range(20):

        RNG.shuffle(order)
        words = 0
        epoch_loss = 0.0

        for si in range(len(order)):

            # print("The ith instance: " + str(order[si]))
            e = instances_processed // len(order)

            train_sent_raw = corpus.tokens_train_raw[order[si]] # For pretrained embedding
            train_sent = corpus.tokens_train[order[si]] # For learnt embedding
            train_pos = corpus.pos_train[order[si]]
            train_gold_acts = corpus.correct_act_train[order[si]]
            train_sent_string = corpus.tokens_string_train[order[si]]
            tok_lemma_map_train = corpus.tok_lemma_map_train[order[si]]

            train_sent_unk = deepcopy(train_sent)
            train_gold_acts_unk = deepcopy(train_gold_acts)

            if args.unk_prob > 0:
                for idx in range(len(train_sent)):
                    if train_sent[idx] in singletons and np.random.uniform(0, 1) < args.unk_prob:
                        train_sent_unk[idx] = kUNK
                        lemma_id = tok_lemma_map_train[idx]
                        if lemma_id in corpus.lemma_practs_map.keys():
                            pr_actions = corpus.lemma_practs_map[lemma_id]
                            token_id = 0
                            for act_idx in range(len(train_gold_acts)):
                                if train_gold_acts[act_idx] == corpus.act_dict.string_convert("SS"):
                                    token_id += 1
                                elif corpus.act_dict.index_convert(train_gold_acts[act_idx])[:3] == "GEN":
                                    if train_gold_acts[act_idx + 1] in pr_actions and token_id == idx:
                                        train_gold_acts_unk[act_idx + 1] = corpus.act_dict.string_convert(corpus.PR_UNK)
                                        break
                                    elif train_gold_acts[act_idx + 2] in pr_actions and token_id == idx:
                                        train_gold_acts_unk[act_idx + 2] = corpus.act_dict.string_convert(corpus.PR_UNK)
                                        break
                                    token_id -= 1
                                else:
                                    if train_gold_acts[act_idx] in pr_actions and token_id == idx:
                                        train_gold_acts_unk[act_idx] = corpus.act_dict.string_convert(corpus.PR_UNK)
                                        break

            # print(train_sent_string)

            losses, _, _ = parser.parsing(train_sent_string, train_sent_raw, train_sent_unk, train_pos, tok_lemma_map_train, 0, train_gold_acts_unk)

            if losses:
                loss = -dy.esum(losses)
                if str(loss.scalar_value()) == 'inf':
                    print(order[si])
                    print(train_sent_string)
                    # exit()
                epoch_loss += loss.scalar_value()
                loss.backward()
                trainer.update()

            words += len(train_sent)
            instances_processed += 1

            if e < 10:
                if instances_processed % 5000 == 0:
                    evaluation_dev(corpus, parser, args.best_smatch, ckt, gold_amr_dev)
            elif e >= 10:
                if instances_processed % args.freq == 0:
                    evaluation_dev(corpus, parser, args.best_smatch, ckt, gold_amr_dev)

            ckt += 1

            if instances_processed % args.freq == 0 and instances_processed != 0:
                print('epoch %d: per-word loss: %.6f' % (e, epoch_loss / words))
                words = 0
                epoch_loss = 0.0


if __name__ == '__main__':

    args = parsing_options()

    corpus = corpus.Corpus()
    gold_amr_dev = eval.get_all_instance(args.gold_AMR_dev)
    # gold_amr_train = eval.get_all_instance(args.gold_AMR_train)

    root_symbol = "ROOT"
    kUNK = corpus.get_or_add_word_train(corpus.UNK)
    corpus.get_or_add_word_all(corpus.UNK)
    kROOT_SYMBOL = corpus.get_or_add_word_train(root_symbol)
    corpus.get_or_add_word_all(root_symbol)

    corpus.load_correct_actions(args.train_file)
    corpus.load_correct_actions_dev(args.dev_file)
    corpus.load_train_preds(args.lemma_practs)

    vocab_size_train = corpus.tok_dict_train.get_size() # UNK and ROOT have been added already

    vocab_size_pretrain, tok_dict_pretrain, full_vocab = utils.get_dict_pretrain(args.emb_file, corpus)

    corpus.load_raw_sent(args.train_file, 'train', tok_dict_pretrain)
    corpus.load_raw_sent(args.dev_file, 'dev', tok_dict_pretrain)

    assert vocab_size_train == corpus.tok_dict_train.get_size()
    assert vocab_size_pretrain == tok_dict_pretrain.get_size()

    parser = ParserBuilder(corpus, args.emb_file, tok_dict_pretrain, full_vocab, vocab_size_train, vocab_size_pretrain, args.unk_prob, args.layers, args.pretrain_dim, args.input_dim, args.pos_dim, args.lstm_input_dim, args.hidden_dim, args.action_dim, args.pred_dim, args.rel_dim, args.ent_dim, args.gen_dim, args.drop_out, args.reent_max, args.reent_nodes, args.merge_max, args.gen_max, args.forbid_cycle)

    training_vocab = set(corpus.tok_dict_train.get_key_list())
    singletons = set()
    counts = {}
    for _, sent in corpus.tokens_train.items():
        for word_idx in sent:
            if word_idx in counts.keys():
                counts[word_idx] += 1
            else:
                counts[word_idx] = 1

    for word, count in counts.items():
        if count == 1:
            singletons.add(word)

    if args.load_model >= 0:
        print("loading pretrained model")
        parser.load_model(args.model)
        pretrained_model = True
    else:
        pretrained_model = False

    if pretrained_model:
        evaluation_dev(corpus, parser, 1, 1, gold_amr_dev)
    else:
        train(corpus, args, parser, gold_amr_dev)