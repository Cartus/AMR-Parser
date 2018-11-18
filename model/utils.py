#-*- coding: utf-8 -*

import model.data_struct as ds


def get_dict_pretrain(emb_file, corpus):

    tok_dict_pretrain = ds.Dict()
    kUNK = tok_dict_pretrain.string_convert("UNK")
    tok_dict_pretrain.string_convert("ROOT")

    full_vocab = set(corpus.tok_dict_all.get_key_list())

    print('creating dictionary of pretrain embeddings')

    for line in open(emb_file, 'r'):
        line = line.split(' ')
        if len(line) > 2:
            if line[0] in full_vocab:
                tok_dict_pretrain.string_convert(line[0])
            else:
                continue

    print('finish creating')

    tok_dict_pretrain.freeze()
    tok_dict_pretrain.set_unk("UNK")
    vocab_size_pretrain = tok_dict_pretrain.get_size()

    print("UNK index in tok_dict_pretrain: " + str(kUNK))
    print("UNK index in tok_dict_all: " + str(corpus.tok_dict_all.string_convert("UNK")))

    return vocab_size_pretrain, tok_dict_pretrain, full_vocab