#-*- coding: utf-8 -*
import sys


def list_compare(lhs, rhs):
    if len(lhs) != len(rhs):
        return False
    lhs.sort()
    rhs.sort()
    return cmp(lhs, rhs)


class Parent(object):

    def __init__(self, head, label):
        self.head = head
        self.label = label

    def __eq__(self, other):
        return self.head == other.head and self.label == other.label

    def __lt__(self, other):
        return self.head < other.head or self.label < other.label


class JointParse(object):

    def __init__(self):

        self.pos_index = set()
        self.node_pos = set()

        self.edges = {}
        self.predicate_lemmas = {}
        self.pred_pos = set()

        self.entity_lemmas = {}
        self.ent_pos = set()

        self.gen_lemmas = {}
        self.gen_pos = set()

        self.mer_pos = set()

        self.root_connected = None

    def contains_edge(self, child, parent):
        if child not in self.edges.keys():
            return False

        existing = self.edges[child]
        for par in existing:
            if par.head == parent:
                return True

        return False

    def __eq__(self, other):
        if len(self.edges) != len(other.edges):
            return False

        for index, parent_list in self.edges.items():
            if index not in other.edges.keys():
                return False
            other_list = other.edges[index]
            if list_compare(parent_list, other_list) == 0:
                return True
            else:
                return False

    def __str__(self):
        structure = "position indexes: " + "\n"
        for index in self.pos_index:
            structure += str(index) + " "
        structure += "\n"

        structure += "predicates: " + "\n"
        for pred_index, pred in self.predicate_lemmas.items():
            structure += str(pred_index) + ": " + pred + "\n"

        structure += "entities: " + "\n"
        for entity_index, entity in self.entity_lemmas.items():
            structure += str(entity_index) + ": " + entity + "\n"

        structure += "generated: " + "\n"
        for gen_index, gen in self.gen_lemmas.items():
            structure += str(gen_index) + ": " + gen + "\n"

        structure += "merge positions: " + "\n"
        for index in self.mer_pos:
            structure += str(index) + "\n"

        structure += "edges: " + "\n"
        for index, parent_list in self.edges.items():
            structure += str(index)
            for parent in parent_list:
                structure += "<-" + str(parent.head) + "[" + parent.label + "], "
            structure += "\n"

        return structure


class Dict(object):

    def __init__(self, frozen=False, map_unk=False, unk_id=-1):

        self.__frozen = frozen
        self.__map_unk = map_unk
        self.__unk_id = unk_id
        self.__words = list()
        self.__d = {}
        self.__freqs = {}

    def get_size(self):
        return len(self.__words)

    def get_dict(self):
        return self.__words

    def get_key_list(self):
        return [key for key in self.__d]

    def print_keys(self):
        string = ""
        for idx in self.__d:
            string += idx + "\n"
        return string

    def contains_word(self, word):
        if word not in self.__words:
            return False
        else:
            return True

    def freeze(self):
        self.__frozen = True

    def is_frozen(self):
        return self.__frozen

    def is_unk(self, word_id):
        if word_id == self.__unk_id:
            return True
        else:
            return False

    def set_unk(self, word):
        if not self.__frozen:
            sys.exit('Please call set_unk() only after dictionary is frozen')
        if self.__map_unk:
            sys.exit('Set UNK more than one time')

        self.__frozen = False
        self.__unk_id = self.string_convert(word)
        self.__frozen = True
        self.__map_unk = True

    def string_convert(self, word):
        if word not in self.__d.keys():
            if self.__frozen:
                if self.__map_unk:
                    return self.__unk_id
                else:
                    sys.exit('Unknown word encountered: '+ word + "\n")
            self.__words.append(word)
            self.__d[word] = len(self.__words)-1
            return self.__d[word]
        else:
            return self.__d[word]

    def index_convert(self, id):
        assert id < len(self.__words)
        return self.__words[id]

    def addFreq(self, word):
        if self.string_convert(word) == self.__unk_id:
            return
        if word not in self.__d.keys:
            sys.exit('Woah something wrong with the word: '+word)

        frequency = 1
        word_id = self.__d[word]
        if word_id in self.__freqs.keys():
            frequency = self.__freqs[word_id] + 1
        self.__freqs[word_id] = frequency

    def is_singleton(self, word_id):
        if word_id not in self.__freqs.keys:
            sys.exit('Unknown word with 0 freq: ' + self.index_convert(word_id))

        if self.__freqs[word_id] == 1:
            return True

        return False

    def clear(self):
        self.__words = list()
        self.__d = {}






