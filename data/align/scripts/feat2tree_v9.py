#!/usr/bin/python
# -*- coding: utf-8 -*-
from collections import defaultdict
from collections import Counter
from get_en_noun_gender import *
from get_new_rules import *
import sys
import re
import math
import copy
import heapq
import itertools
import operator
import random

logs = sys.stderr

D_CONCEPT = r'\*(OR|or)\*$'
D_ROLE = r':(OR|or)$'

INSTANCE = '/' # shorthand for ':instance'
REST = ':rest' # lumping keyword on the lhs
ADD = ':add' # restruct keyword on the rhs, syntax can be ":add x0" or ":add (:modal x0)"
DEFAULT_RULE_PROB = 0 # used to be -1000
TRANSITION_RULE_PROB = 0
GENERIC_STATE = 'q'

PRONOUN = 'i we you he she it they' 
ARG = r':(arg|ARG)\d+$' # :arg0, :arg1, etc. excluding :arg0-of, etc
OP = r':(op|OP)\d+$' # :op1, op2, etc.

# replace chars for latex
dreplace = {
'$' : '\$', 
'%' : '\%', 
'_' : '\_', 
'{' : '\{', 
'}' : '\}', 
'&' : '\&', 
'#' : '\#', 

'~' : '\~{}', 
'^' : '\^{}', 

'[' : '{[}', 
']' : '{]}', 

'*' : '\\textasteriskcentered', 
'\\' : '\\textbackslash{}', 
'|' : '\\textbar{}', 
'>' : '\\textgreater{}', 
'<' : '\\textless{}'
}


def replace_char(word):
    '''replace chars for latex, using dreplace dictionary'''
    newstr = ''
    for char in list(word):
        if char in dreplace:
            newstr += dreplace[char]
        else:
            newstr += char
    return newstr


def find_key(dic, val):
    '''return the first key of dictionary given value'''
    return [k for k, v in dic.iteritems() if v == val][0]


class Recursive_defaultdict(defaultdict):
    '''helper class using inheritance, copied from web'''
    def __init__(self):
        self.default_factory = type(self)

    def pp_indented(self, indent=0):
        l = []
        for k in self:
            if self[k]:
                if type(self[k]) == Recursive_defaultdict:
                    l.append('\t'*indent + str(k) + '\n' + self[k].pp_indented(indent+1))
                else:
                    l.append('\t'*indent + str(k) + '\n' + '\t'*(indent+1) + str(self[k]))
            else:
                l.append('\t'*indent + str(k))
        return '\n'.join(l)


class EdgeAssignment(object):
    '''for :rest feat'''
    def __init__(self, psrfeat, rulefeat):
        self.psrfeat = psrfeat
        self.rulefeat = rulefeat

    def __str__(self):
        return 'psrfeat:'+str(self.psrfeat) + '##rulefeat:' + str(self.rulefeat)


class NodeAssignment(object):

    def __init__(self, psr, rulenode):
        self.psr = psr
        self.rulenode = rulenode

    def __str__(self):
        return 'psr:' + str(self.psr) + '##rulenode:' + str(self.rulenode)


class Rule(object):

    UNKNOWN = 0
    RESTRUCT = 1
    DEFAULT  = 2
    STATETRANS = 3
    NORMAL = 4
    PREDPROB = 5
    REENTPROB = 6
    RECALL = 7
    AUTO = 8

    TYPE_DICT = defaultdict(int)
    TYPE_DICT['unknown'] = UNKNOWN
    TYPE_DICT['restruct'] = RESTRUCT
    TYPE_DICT['default'] = DEFAULT
    TYPE_DICT['statetrans'] = STATETRANS
    TYPE_DICT['normal'] = NORMAL
    TYPE_DICT['predprob'] = PREDPROB
    TYPE_DICT['reentprob'] = REENTPROB
    TYPE_DICT['recall'] = RECALL
    TYPE_DICT['auto'] = AUTO

    # NOTE: use logprob by default
    def __init__(self, lhsstate, lhs, rhsstate, rhs, prob, type, count=1, comment=''):
        self.lhsstate = lhsstate
        self.lhs = lhs
        self.rhsstate = rhsstate
        self.rhs = rhs
        self.prob = prob
        self.type = type
        self.count = count
        self.comment = comment

    def __str__(self):
        if self.rhsstate:
            rulestr = self.lhsstate + '.' + self.lhs.pp_rule() + \
                      ' -> ' + self.rhsstate + '.' + self.rhs.pp_rule()
        else:         
            rulestr = self.lhsstate + '.' + self.lhs.pp_rule() + \
                      ' -> ' + self.rhs.pp()
        if not options.ghkm:
            rulestr += ' # ' + str(self.prob)
            rulestr += ' ## ' + 'count:' + str(self.count)
            rulestr += ' ^ '+ 'type:' + find_key(Rule.TYPE_DICT, self.type)
        else:
            rulestr += ' ## ' + self.comment
 
        return rulestr

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.lhs.pp())


class Tree(object):
    "tree (including xrs patterns)"
    VARIABLE = -1

    def __init__(self, node, type, children, id, is_virtual=False):         
        self.node = node
        self.type = type
        self.children = children
        self.id = id
        self.is_virtual = is_virtual

    #NOTE: binarize w/o looking at 1) alignment; 2) syntactic or semantic head
    # if we consider the linearized yield of rule, result is same as wang et al. emnlp2007
    def binarize(self, direction='left'):
        if len(self.children) > 2:
            virt_node_name = self.node if self.node.endswith('_bar') else self.node + '_bar'
            if direction == 'left':
                virt_node = Tree(virt_node_name, None, self.children[:-1], None)
                self.children = [virt_node, self.children[-1]]
            elif direction == 'right':
                virt_node = Tree(virt_node_name, None, self.children[1:], None)
                self.children = [self.children[0], virt_node]
        # recurse
        for c in self.children:
            c.binarize(direction=direction)
       

    def assign_id(self, startid=-1):
        '''assign_id to tree nodes that are not variable nodes
        '''
        global global_tree_node_id
        if not self.id:
            self.id = global_tree_node_id
            global_tree_node_id += -1
        for c in self.children:
            c.assign_id()


    def __eq__(self, other):
        return self.id == other.id


    def __hash__(self):
        return hash(self.id)


    def gettriples(self):
        '''triple has the format: (selfid, featnodeid, featedge)
        '''
        triples = []
        if self.children:
            for child in self.children:
                triples.append( (self.ppthis(), child.ppthis(), '') )
                triples.extend(child.gettriples())
        else:
            # note without comma, [(1)] is [1]
            triples.append( ( self.ppthis(),) )
        return triples


    def leaves(self):
        if not self.children:
            return [self]
        ll = []
        for sub in self.children:
            ll += sub.leaves()
        return ll

    def numLeaves(self):
        return len(self.leaves())

    def surface(self):                                                  
        return ' '.join(str(i) for i in self.leaves())                   

    def __str__(self):
        return self.pp()

    def pp(self):
        '''pretty-print, recursive
        '''
        if self.type == Tree.VARIABLE:
            return self.node + '.' + 'x' + str(self.id)
        s = self.node
        if self.children:            
            s += '(' + " ".join([sub.pp() for sub in self.children]) + ')'
        return s

    def pp_internal(self):
        '''internal printout
        '''
        s = str(self.id)
        if self.children:            
            s += '(' + " ".join([sub.pp_internal() for sub in self.children]) + ')'
        return s


    def pp_qtree2(self):
        if self.children:
            return '[.' + replace_char(str(self.node)) + ' ' + ' '.join(c.pp_qtree2() for c in self.children) + ' ]'
        else:
            return replace_char(str(self.node))

    def pp_qtree(self):        
        return '\Tree ' + self.pp_qtree2()


class Feat(object):
    VARIABLE = -1

    def __init__(self, edge, node, id=None):
        self.edge = edge
        self.node = node
        self.id   = id
        self.alignset = set()
        alignsplit = edge.split('~')
        if len(alignsplit) > 1:
            self.alignset |= set(int(i) for i in alignsplit[1].split('e.')[1].split(','))
            self.edge = alignsplit[0]

    def __str__(self):
        return self.edge + '_' + str(self.node)

    def __eq__(self, other):
        return self.node == other.node and self.edge == other.edge

    def __hash__(self):
        #print >> logs, 'in feat __hash__'
        return hash(self.node)


class FeatGraph(object):
    '''amr feature structure is edge-labeled graph'''

    #TODO: can a virtual node be a variable node? virtual ndoe?? variable node???
    VARIABLE = -1

    def __init__(self, id, val, type, feats=None, is_virtual=False, pi='', pi_edge=''):
        self.id = id
        self.val = val
        self.type = type
        self.feats = feats
        self.is_virtual = is_virtual
        self.pi = pi
        self.pi_edge = pi_edge
        # yanggao20130912: change alignset to be a set of tuples, for reentrancy case!
        self.alignset = set()
        alignsplit = val.split('~')
        if len(alignsplit) > 1:
            self.alignset |= set( int(i) for i in alignsplit[1].split('e.')[1].split(',') )
            self.val = alignsplit[0]

    def get_alignment(self, tuples):
        if self.alignset:
            return
        for tup in tuples:
            amr_tuple = tuple(tup[:-1])
            if self.pi and (self.pi.val, self.pi_edge, self.val) == amr_tuple:
                self.alignset = set(int(i) for i in tup[-1].split('e.')[1].split(','))
                return
        for f in self.feats:
            f.node.get_alignment(tuples) 

    def getterminal(self, nt_list):
        if (not self.feats) and (self.val not in [nt.val for nt in nt_list]):
            return [(self.pi.val, self.pi_edge, self.val)]
        ret = []
        for f in self.feats:
            if f.edge == INSTANCE:
                ret.append((self.val, INSTANCE, f.node.val))
            else:
                ret.extend(f.node.getterminal(nt_list))
        return ret

    #NOTE: have to do copy.copy(), otherwise changing self.alignset
    def getspan(self):
        ret = copy.copy(self.alignset)
        for f in self.feats:
            # assume feat alignment is not recursive
            ret |= f.alignset | f.node.getspan()
        return ret


    #NOTE: have to do copy.copy(), otherwise changing self.alignset
    def getspan_except(self, othernode):
        if self == othernode:
            return set()
        ret = copy.copy(self.alignset)
        for f in self.feats:
            ret |= f.alignset | f.node.getspan_except(othernode)
        return ret


    #TODO: check if we need singleton graph, as in tree case
    def gettriples(self):
        '''triple has the format: (selfid, featnodeid, featedge)
        '''
        triples = []
        triples.extend((str(self), str(feat.node), feat.edge)\
                              for feat in self.feats)
        for feat in self.feats:
            triples.extend(feat.node.gettriples())
        return triples

    def __str__(self):
        '''assume @ does not exist in val
           meaningful (with self.val) and
           unique (with self.id) represen
           for node, and can differentiate
           (i / i) by id
        '''
        return self.val + '@' + str(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        #print >> logs, 'in featgraph __hash__'
        return hash(self.id)

    def get_size(self):
        s = 1
        for f in self.feats:
            s += 1
            s += f.node.get_size()
        return s   

     
    #ygao20130130
    def graph2tree1(self):
        '''naive graph-to-tree conversion
        '''
        #print >> logs, 'self.val' + self.val
        if not self.feats:
            return Tree(self.val, None, [], None)
        subs = []         
        for feat in self.feats:
            sub = feat.node.graph2tree1()
            if not sub.node:
                sub.node = feat.edge
            else:
                sub = Tree(feat.edge, None, [sub], None)
            subs.append(sub)
        ret = Tree(None, None, subs, None)
        #print >> logs, 'ret.pp' + ret.pp()
        return ret


    #ygao20130130
    def graph2tree(self):
        #print >> logs, 'self' + self.pp()
        ret = self.graph2tree1()
        ret.node = 'TOP'
        return ret


    def pp_internal(self):
        '''features:
           1) one-line output
           2) all corefering nodes are fully specified
        '''
        if not self.feats:
            return str(self.id)
        s = str(self.id) + ' ' + ' '.join(feat.edge + ' ' + 
            feat.node.pp_internal() for feat in self.feats)
        return '(' + s.strip() + ')'


    def pp_rule(self):
        '''pp rule amr, no checking for printed_nodes
        '''
        if not self.feats:
            return self.val
        feats_str_list = []
        for ind, feat in enumerate(self.feats):
            node_repr = feat.node.pp_rule()
            feats_str_list.append(feat.edge + ' ' + node_repr)
        s = ' '.join(feats_str_list)
        return '(' + s.strip() + ')'

    # NOTE: yanggao20130814 added alignset printout
    def pp(self, printed_nodes = set([])):
        '''features:
           1) one-line output
           2) corefering nodes are fully specified once and once only
        '''
        if not self.feats or self in printed_nodes:
            if self.alignset:
                return self.val + '~e.' + ','.join(str(i) for i in sorted(self.alignset))
            else:
                return self.val
        s = self.val + ' '
        feats_str_list = []
        printed_nodes = printed_nodes | set([self])
        for ind, feat in enumerate(self.feats):
            node_repr = feat.node.pp(printed_nodes)
            printed_nodes |= set(feat.node.get_nonterm_nodes()) 
            if feat.alignset:
                feats_str_list.append(feat.edge + '~e.' + ','.join(str(i) for i in sorted(feat.alignset)) + ' ' + node_repr)
            else:
                feats_str_list.append(feat.edge + ' ' + node_repr)
        s += ' '.join(feats_str_list)
        return '(' + s.strip() + ')'


    def pp_indented(self, indent=0, printed_nodes = set([])):
        '''features:
           1) same indentation for features under the same node
           2) corefering nodes are fully specified once and once only
        '''

        if not self.feats or self in printed_nodes:
            if self.alignset:
                return self.val + '~e.' + ','.join(str(i) for i in sorted(self.alignset))
            else:
                return self.val
        pre_feat_str = '(' + self.val + ' '
        pre_feat_space = indent + len(pre_feat_str)
        delimiter = '\n' + ' '*pre_feat_space
        feats_str_list = []
        printed_nodes = printed_nodes | set([self])
        for ind, feat in enumerate(self.feats):
            node_repr = feat.node.pp_indented(len(feat.edge + ' ') + pre_feat_space, printed_nodes)
            printed_nodes |= set(feat.node.get_nonterm_nodes()) 
            if feat.alignset:
                feats_str_list.append(feat.edge + '~e.' + ','.join(str(i) for i in sorted(feat.alignset)) + ' ' + node_repr)
            else:
                feats_str_list.append(feat.edge + ' ' + node_repr)
        return pre_feat_str + delimiter.join(feats_str_list) + ')'


    def proc_damr(self):
        #print 'visiting', self.val
        for i in self.feats:
            i.node.proc_damr()

        opfeats = [i for i in self.feats if i.edge.startswith(':op')]
        if self.feats and re.match(D_CONCEPT, self.feats[0].node.val) and opfeats:
            conj_feats = [i for i in self.feats[1:] if not i.edge.startswith(':op')]
            newnode = FeatGraph(None, 'y999', None, [self.feats[0]] + opfeats)
            new_or_feat = Feat(':or-op', newnode)
            self.feats = [new_or_feat] + conj_feats


    def is_damr(self):
        for i in self.feats:
            # special edge, contain at least two alternatives
            if i.edge.lower() in [':or-op', ':or'] and len(i.node.feats) > 2:
                return True
            if i.node.is_damr():
                return True
        return False


    def get_simple_amr_from_damr(self):
        if not self.feats:
            #print 'simple return', self, [self]
            return [self]

        # result to be returned
        newnodes = []

        # store features to be multiplied
        feat_list = []
        for f in self.feats:
            if f.edge == ':or-op':
                new_edges_all_op = []
                for op_f in f.node.feats[1:]:
                    new_edges_all_op.extend( [ i.feats for i in op_f.node.get_simple_amr_from_damr() ] )
                feat_list.append( new_edges_all_op )
            elif f.edge == ':or':
                new_edges_all_or = []
                for ff in f.node.feats[1:]:
                    new_edges = [ Feat(ff.edge, i) for i in ff.node.get_simple_amr_from_damr() ]
                    new_edges_all_or.extend( new_edges )
                feat_list.append(new_edges_all_or)
            else:
                new_edges = [ Feat(f.edge, i) for i in f.node.get_simple_amr_from_damr() ]
                feat_list.append(new_edges)
        #print 'feat product'
        for i in itertools.product(*feat_list):
            #print ' '.join(str(j) for j in get_linear(i))
            newnode = FeatGraph(self.id, self.val, None, get_linear(i))
            newnodes.append(newnode)
        
        #print 'simple return', self, newnodes
        
        return newnodes


    def getfeats(self):
        return self.feats

    def get_child_by_edge(self, edgename):
        edge_list = [i.edge for i in self.feats]
        if edgename in edge_list:
            ind = edge_list.index(edgename)
            return self.feats[ind].node
        return None

    def get_unique_constants(self):
        '''get all unique concepts and rels for
           filtering rules according to each amr input
        '''
        ret = set()
        if self.type != FeatGraph.VARIABLE and (not self.feats) and self.val != '':
            ret.add(self.val)
        for feat in self.feats:
            rel_rest = re.match(REL_REST, feat.edge)
            if rel_rest and rel_rest.group(2):
                ret.add(REST)
                ret.add(rel_rest.group(2))
            else:
                ret.add(feat.edge)
            ret |= feat.node.get_unique_constants()
        return ret     


    def get_nonterm_nodes(self):
        ret = []
        if self.feats:
            ret.append(self)
        for f in self.feats:
            ret.extend(f.node.get_nonterm_nodes())
        return ret

  
    def assign_id_rule(self):
        '''two differences from assigning id to input amr
           1) start from -1, since variable node x0 has id 0
           2) decrease from -1
        '''
        global global_rule_node_id
        if self.id == None:
            self.id = global_rule_node_id
            global_rule_node_id += -1
            for f in self.feats:
                f.node.assign_id_rule()
 
    def assign_id(self):
        global global_input_node_id
        if self.id == None:
            self.id = global_input_node_id
            global_input_node_id += 1
            for f in self.feats:
                f.node.assign_id()

    def assign_id_nonrecurs(self):
        global global_input_node_id
        self.id = global_input_node_id
        global_input_node_id += 1


    def is_cyclic(self, path_id=set([])):
        '''detect cycle by checking if self.id
           appears in its direct ancestors
           note that in (w / want :ARG0 (i / i) :ARG1 i),
           we need to escape the second i
           basically, escape all nodes under 'INSTANCE'
        '''
        if self.id in path_id:
            #print 'self.id', self.id
            #print 'path_id', path_id
            return True
        for ind, f in enumerate(self.feats):
            if f.edge != INSTANCE:
                ret = f.node.is_cyclic(path_id|set([self.id]))
                if ret:
                    return ret
        return False

    #TODO: create id when doing this corefy, using a dictionary!! similarly for tree, create dictionary, then for virtual nodes just extend it
    def corefy(self, all_nt):
        '''make the coref i under :ARG1 in
           (w / want :ARG0 (i / i) :ARG1 i)
           pointing to the primary subgraph
           i.e., (i / i) under :ARG0

           identify coref node by these criteria:
           1) has no feats
           2) val same as a nonterm node
           3) not under the INSTANCE arg, since we may
              have (i / i) where the second i is not coref
           4) assumes that property value cannot have the
              form of [a-zA-Z]\d*, so not same as nonterm
        '''
        if not self.feats:
            for nt in all_nt:
                if self.val == nt.val:
                    global global_input_id
                    print >> logs, '\namr', global_input_id, 'corefy'
                    print >> logs, 'referent triple: (', self.pi.val, self.pi_edge, self.val, ')'
                    #print >> logs, 'nt downstream', nt.feats[0].edge, nt.feats[0].node.val
                    #print >> logs, 'nt upstream', nt.pi_edge, nt.pi
                    #print >> logs, 'ref upstream', self.pi_edge, self.pi

                    if options.align:
                        # return a non-recursive copy
                        return FeatGraph(None, self.val, None, [])

                    if options.ghkm:
                        nt.alignset |= self.alignset
                        return nt

                    # not doing coref preprocessing in two cases
                    global global_is_damr
                    if not options.replace_coref or global_is_damr:
                        return nt

                    # replace coref
                    # if nt is being referred to, it has to have at least one feat
                    orig_concept = nt.feats[0].node.val
                    new_concept = None
                    if nt.pi and self.pi.val in [i.node.val for i in nt.pi.feats ] and \
                         self.pi_edge.lower() in [':arg0', ':arg1'] and \
                         re.match(ARG, self.pi.pi_edge) and \
                         re.match(ARG, nt.pi_edge):
                        print >> logs, 'control pattern, no change'
                        return nt
                    elif nt.pi and nt.pi.pi and nt.pi.pi.feats and nt.pi.pi.feats[0].node and \
                         self.pi.val in [i.node.val for i in nt.pi.pi.feats ] and \
                         nt.pi.pi.feats[0].node.val in ['and', 'or'] and \
                         re.match(OP, self.pi.pi_edge) and \
                         re.match(OP, nt.pi.pi_edge):
                        print >>logs, 'conjunction pattern, no change'
                        return nt
                    elif orig_concept in PRONOUN.split():
                        # cannot keep nt, because orig_concept may be at the root of cycle
                        print >> logs, 'refer to pronoun, change to pronoun concept'
                        new_concept = orig_concept
                    elif orig_concept == 'and':
                        print >> logs, 'refer to a collection joined by "and", change to "they"'
                        new_concept = 'they'
                    else:
                        # query the gender for the concept (and name, if available)
                        querystr = orig_concept
                        name_child = nt.get_child_by_edge(':name')
                        if name_child:
                            op1_node = name_child.get_child_by_edge(':op1')
                            if op1_node:
                                querystr += '|||' + op1_node.val.replace('"', '')
                        gender = get_en_noun_gender(querystr)
                        print >> logs, 'querying gender with concept and name of referred node: ' + querystr 
                        print >> logs, 'gender ' + gender
                        if gender == 'F':
                            new_concept = 'fem_general'
                        elif gender == 'M':
                            new_concept = 'masc_general'
                        elif gender == 'U':
                            new_concept = 'it_general'
                    if not new_concept:
                        new_concept = 'it_general'

                    print >> logs, 'replacing reentrant with pronoun ' + new_concept
                    new_node = FeatGraph(None, 'x999', None, [])
                    new_node.feats.append(Feat('/', FeatGraph(None, new_concept, None, [])))
                    return new_node


        for ind, f in enumerate(self.feats):
            # don't mistake the second i in
            # (w / want :ARG0 (i / i) :ARG1 i) as coref
            if f.edge != INSTANCE:
                self.feats[ind].node = f.node.corefy(all_nt)
        return self


    def rest_to_end(self):
        '''if :rest exists in rule lhs, move it to the
           end of its level s.t. it is checked last
        '''
        for f in self.feats:
            f.node.rest_to_end()
        featlist = [i.edge for i in self.feats]
        for ind, f in enumerate(featlist):
            if re.match(REL_REST, f):
                self.feats.append(self.feats.pop(ind))


class PartialSemRef(object):

    def __init__(self, arg):
        '''two types of arg:
           1) one FeatGraph node
           2) a set of features from :rest
        '''
        self.arg = arg


    def is_term(self):
        return len(self.getfeats()) == 0


    def getfeats(self):
        if type(self.arg) == FeatGraph:
            return self.arg.feats
        return self.arg


    def is_lookahead_ok(self, concept_lookahead):
        '''find concepts through :or-op, can be recursive
        '''
        for f in self.getfeats():
            if f.edge == INSTANCE:
                if f.node.val == concept_lookahead:
                    return True
                return False
            elif f.edge == ':or-op':
                for op_f in f.node.feats[1:]:
                    op_psr = PartialSemRef(op_f.node)
                    if op_psr.is_lookahead_ok(concept_lookahead):
                        return True
        return False
 

    def __str__(self):
        # note: sort first!
        if type(self.arg) == FeatGraph:
            return str(self.arg)
        return '{' + ','.join(sorted(str(i) for i in self.arg)) + '}'

    def __eq__(self, other):
        #print 'compare', self, other, type(self.arg), type(other.arg)
        if type(self.arg) != type(other.arg):
            #print 'different type, return False'
            return False
        if type(self.arg) == FeatGraph:
            #print 'node type'
            #ret = (self.arg == other.arg)
            #print 'return node check', ret
            return self.arg == other.arg
        if len(self.arg) != len(other.arg):
            #print 'set length diff, return False'
            return False
        # set comparison
        #ret = (self.arg == other.arg)
        #print 'return set check', ret
        return self.arg == other.arg

    def __hash__(self):
        # TODO: weird, __eq__ is called, yet this is not!!
        #print 'in psr __hash__'
        return hash(type(self.arg))


def get_list_ind(l, e):
    '''one liner to get element index from list
    '''
    return l.index(e) if e in l else -1


#TODO: delete this class and merge with DerivationNode
#TODO: or use as tmp structure
class DerivationNode_Align(object):
    ''' a special edge-labelled graph
        DerivationNode_Align is a node when I sit there, I can pull rules from it
    '''
    def __init__(self, amr, tree):
        self.amr = amr
        self.tree = tree
        self.hpes = []

    def __str__(self):
        return 'q' + self.tree.node + '.' + str(self.amr)

    def get_rules(self):
        '''bfs to get rules from the derivation forest rooted at this node
        '''
        openq = [self]
        closedq = []
        rules = []
        while openq:
            curr = openq.pop()
            for h in curr.hpes:
                if options.debug:
                    rules.append(str(h.rule)+ ' ## pi:' + str(h.pi)+'{'+ '_'.join(str(i) for i in h.pi.amr.feats) +'}' + ' children:' + ' '.join(str(i)+'{'+'_'.join(str(j) for j in i.amr.feats)+'}' for i in h.children))
                else:
                    rules.append(h.rule)
                for c in h.children:
                    if c not in openq and c not in closedq:
                        openq.append(c)
            closedq.append(curr)
        return rules 
      
    def __eq__(self, other):
        return self.amr == other.amr and self.tree == other.tree 

    def __hash__(self):
        return hash(self.amr)


class DerivationNode(object):

    def __init__(self, state, psr):
        self.state = state
        self.psr = psr
        self.hpes = []
        # store num_deriv for this node, for dynamic programming
        # TODO: delete num_deriv and visited, should still work for damrs
        self.num_deriv = None
        self.visited = False

    def __eq__(self, other):
        #print 'compare derivtionnode', self, other,\
         #     (self.psr == other.psr and self.state == other.state)
        #return self.state == other.state and self.psr == other.psr
        return self.state == other.state and self.psr == other.psr

    #TODO: psr as hash???
    def __hash__(self):
        # when either __eq__ or __cmp__ works,
        # __eq__ is preferred, read python online man
        return hash(self.psr)

    def __str__(self):
        return '[' + self.state + '.' + str(self.psr) + ']'

    def pp(self):
        return str(self)

    def surface(self):
        return str(self)

    def leaves(self):
        return [self]

    #TODO: ugly, should use bfs instead of keeping num_deriv variable
    def get_derivation_number(self):
        if self.num_deriv != None:
            return self.num_deriv
        tot = 0
        for hpe in self.hpes:
            children_deriv_counts = [i.get_derivation_number() for i in hpe.children]
            if not children_deriv_counts:
                tot += 1
            else:
                tot += reduce(operator.mul, children_deriv_counts)
        self.num_deriv = tot
        return tot    

    #TODO: compare efficiency of this and bfs slower version???
    def get_derivation_forest(self):
        ret = []
        for hpe in self.hpes:
            ret.append(str(hpe))
        for hpe in self.hpes:
            for c in hpe.children:
                if not c.visited:
                    ret.extend(c.get_derivation_forest())
        self.visited = True
        return ret


class Hyperedge(object):
    #TODO: make sure rule matching is ok with third arg being children
    def __init__(self, rule, pi, children):
        # pi is parent node in top-down derivation
        # consequent node in bottom-up sense
        self.pi = pi
        self.children = children
        #TODO: derive comp_rhs???
        self.comp_rhs = None
        self.oldvecs = set()
        if rule:
            self.rule = rule
        else:
            self.rule = self.get_rule()

    #TODO: efficient comparison?
    def __eq__(self, other):
        return str(self) == str(other)
        """print 'compare', self, other
        if self.pi != other.pi:
            return False
        elif self.rule != other.rule:
            return False
        elif len(self.children) != len(other.children):
            return False
        else:
            for i, j in zip(self.children, other.children):
                if i != j:
                    return False
            return True"""

    def __hash__(self):
        return hash(len(self.children))

    def get_rhs_string(self):
        return self.comp_rhs.surface()

    def get_rhs_tree(self):
        return str(self.comp_rhs)

    # TODO: update get_output_tree and get_output_string later
    def __str__(self):
        '''str in the cdec format
        '''
        feats = ['Rule='+str(self.rule.prob), 'DerivSize=1', find_key(Rule.TYPE_DICT, self.rule.type)+'=1']
        tup = (str(self.pi), self.get_rhs_string(), ' '.join(feats), self.get_rhs_tree(), str(self.rule))
        return ' ||| '.join(tup)
   
   
    # TODO: have a strict definition of restruct rule 
    # TODO: creating default t and nt rules, without doing it explicitly 
    def get_rule(self):
        comment = 'source amr: ' + self.pi.amr.pp() + '  source tree: ' + self.pi.tree.pp()
        lhsstate = 'q' + self.pi.tree.node
        lhs_amr = factor_amr(self.pi.amr, self.children)
        if len(self.children) == 1 and self.children[0].tree == self.pi.tree:
            rhs_amr = factor_amr(self.children[0].amr, self.children)
            rhsstate = 'q' + self.children[0].tree.node
            rule = Rule(lhsstate, lhs_amr, rhsstate, rhs_amr, 0.0, Rule.AUTO, comment=comment)
        else:
            rhs_tree = factor_tree(self.pi.tree, self.children)
            rule = Rule(lhsstate, lhs_amr, None, rhs_tree, 0.0, Rule.AUTO, comment=comment)
        return rule
  
     
class kbest_item(object):

    def __init__(self, hpe, vector):
        self.hpe = hpe
        self.vector = vector
        # only negate curr hpe score, since total score is recursively calculated
        self.score = -self.hpe.rule.prob + sum( kbest[self.hpe.children[ind]][subvec].score for ind, subvec in enumerate(self.vector) )
        self.out_tree = None

    def __str__(self):
        return 'hpe:' + str(self.hpe) + '\tvector:' + str(self.vector) + '\tscore:' + str(self.score)     

    def __cmp__(self, other):
        return cmp((self.score, self.hpe), (other.score, other.hpe))

    # TODO: faster hashing?
    def __hash__(self):
        return hash(self.score)

    def get_tree(self):
        if not self.out_tree:
            self.out_tree, vec = compose_output_tree(self.hpe.comp_rhs, copy.copy(self.vector))
        return self.out_tree

    def get_output_tree(self):
        return ' ||| '.join([self.get_tree().pp(), 'Rule=' + str(-self.score if self.score != 0 else 0.0) + ' ' + 'DerivSize=1', str(-self.score if self.score != 0 else 0.0)])

    def get_output_string(self):
        return ' ||| '.join([self.get_tree().surface(), 'Rule=' + str(-self.score if self.score != 0 else 0.0) + ' ' + 'DerivSize=1', str(-self.score if self.score != 0 else 0.0)])

# comment starting with '#', or blank line
COMMENT = re.compile(r'\s*#[^\n]*(\n\s*#[^\n]*)*\n\s*|\n')
def get_input(s):
    '''read multiple lines of input and parse them into a list of amrs'''
    ret = []
    #print 'instr', s, '**'
    #print list(s)
    #print ' '.join(str(i[0])+'-'+i[1] for i in enumerate(list(s)))
    pos = 0
    while pos < len(s):
        comment_match = COMMENT.match(s, pos)
        if comment_match:
            pos = comment_match.end()
            comment_symbol = comment_match.group().strip()
            #print 'matched comment', comment_symbol, 'pos now', pos
            continue

        pos, input = input_amrparse(s, pos)
        if input:
            ret.append(input)
        #print 'parsed', input, 'now pos', pos
    #print 'print input amrs, size', len(ret)
    #for i in ret:
     #   print i.pp()
      #  print 'internal', i.pp_internal()
    return ret


NODE_BEGIN_AMR     = re.compile(r'\s*\(\s*')
NODE_END_AMR       = re.compile(r'\s*\)\s*')
# permissive node end checking: (c / cat)) and (c / cat are both allowed, and will be normalized as (c / cat)
#NODE_END_AMR       = re.compile(r'\s*\)[\s\)]*\s*')
# allow anything inside a pair of double quotes
# like in "16:30" in (:time "16:30"), but not allowing space inside ""
# TODO: yanggao20130816 modified to allow alignment like "jon"~e.6
#NODE_AMR           = re.compile(r'\s*[^\s\(\)]+\s*')
NODE_AMR           = re.compile(r'\s*"[^"]*"\s*|\s*[^\s\(\)/:]+\s*')
X_NODE_AMR         = re.compile(r'^\s*x\d+\s*$') # in rule
# :rest with lookahead: qs.(:rest=[/ increase-01] x0 :ARG1 x1) -> S(qnp.x1 qvp.x0)
# TODO: ygao20130130 relax constraint by comment out following, see if it is ok
REL_NORM = r'\s*:[a-zA-Z][^\s\(]*\s+'
#REL_NORM = r'\s*:[a-zA-Z][\w-]*\s*'
#REL_NORM = r'\s*:[a-zA-Z]\S*\s*'
REL_INST = r'\s*%s\s*'%INSTANCE
REL_REST = r'\s*%s\s*(=\s*\[\s*%s\s*(\S+)\s*\]\s*)?'%(REST, INSTANCE) # :rest w/ or w/o lookahead
REL_LABEL_AMR      = re.compile(r'%s|%s|%s'%(REL_REST, REL_INST, REL_NORM))

def input_amrparse(s, pos = 0, depth = 0):
    '''return a (pos, FeatGraph) pair
    '''
    #print >> logs, 'in input_amrparse'
    #print >> logs, 's\t' + s + '\ttotal len\t' + str(len(list(s)))
    #print >> logs, 'curr pos\t' + str(pos) + '\tworking on\t' + s[pos:pos+20]

    comment_match = COMMENT.match(s, pos)
    if comment_match:
        pos = comment_match.end()
        comment_symbol = comment_match.group().strip()
	#print 'matched comment', comment_symbol, 'pos now', pos

    node_match = NODE_AMR.match(s, pos)
    if node_match:
        pos = node_match.end()
        node_symbol = node_match.group().strip()
        #print 'matched node', node_symbol, 'pos now', pos
        node = FeatGraph(None, node_symbol, None, [])
        return pos, node

    nb_match = NODE_BEGIN_AMR.match(s, pos)
    if nb_match:
        pos = nb_match.end()
        #print 'matched nb, pos now', pos
        pos, node = input_amrparse(s, pos, depth+1)
        #print 'after node matching in nb, pos', pos

        if not node:
	    return pos, None

        while pos < len(s):
            ne_match = NODE_END_AMR.match(s, pos)
            if ne_match:
                pos = ne_match.end()
                #print 'matched ne, pos now', pos
                return pos, node

            rel_match = REL_LABEL_AMR.match(s, pos)
            if rel_match:
                pos = rel_match.end()
                rel_symbol = rel_match.group().strip()
                #print 'matched rel', rel_symbol, 'now pos', pos
                rel = ''.join(rel_symbol.split())
                pos, newnode = input_amrparse(s, pos, depth+1)
                if not newnode:
                    print >> logs, 'error, return pos', pos
                    return pos, None
                node.feats.append(Feat(rel, newnode))
                newnode.pi, newnode.pi_edge = node, rel
            else:
                print >> logs, 'does not match ne or rel, pos', pos
                return pos, None	

    return pos, None


def rule_amrparse(s, pos = 0, depth = 0):
    '''return a (pos, FeatGraph) pair
    '''
    #print 's', s, '\tpos',pos,'\tworking on', \
     #     s[pos:], '\ttotal len' ,len(list(s))

    node_match = NODE_AMR.match(s, pos)
    if node_match:
        pos = node_match.end()
        node_symbol = node_match.group().strip()
        #print 'matched node', node_symbol, 'pos now', pos

        # x0, x1 in (x0 / eat :ARG0 x1) 
        if X_NODE_AMR.match(node_symbol):
            val = node_symbol
            id = int(node_symbol[1:])
            type = FeatGraph.VARIABLE
        # cat in (/ cat) or
        # imperative in (:mode imperative) or
        # - in (:polarity -)
        else:
            val = node_symbol
            id = None
            type = None
        node = FeatGraph(id, val, type, [])
        return pos, node

    nb_match = NODE_BEGIN_AMR.match(s, pos)
    if nb_match:
        pos = nb_match.end()
        #print 'matched nb, pos now', pos
        # usually headless feature structure on rule lhs,
        # such as (:time x0 :rest x1), yet restructuring
        # rules may have head on rhs, such as
        # q.(/ possible :domain x0 :rest x1) -> 
        # q.(x0 :add (:modal x1))
        pos, node = rule_amrparse(s, pos, depth+1)
        # headless feature structure
        if not node:
            node = FeatGraph(None, '', None, [])
        #print 'after node matching in nb, pos', pos
 
        while pos < len(s):
            ne_match = NODE_END_AMR.match(s, pos)
            if ne_match:
                pos = ne_match.end()
                break

            rel_match = REL_LABEL_AMR.match(s, pos)
            if rel_match:
                pos = rel_match.end()
                rel_symbol = rel_match.group().strip()
                #print 'matched rel', rel_symbol, 'now pos', pos
                #TODO: ygao20120820: do it more properly
                #rel = ''.join(rel_symbol.split())
                rel = rel_symbol
                pos, newnode = rule_amrparse(s, pos, depth+1)              
                node.feats.append(Feat(rel, newnode))
               
        #print 'feats', '\t'.join(i.edge + ' ' + str(i.node)
         #     for i in node.feats)

        return pos, node   

    return pos, None


# for both ptbparse and xrsparse
CONST_TREE      = re.compile(r'\s*([^\s\(\)]+)\s*')
NODE_BEGIN_TREE = re.compile(r'\s*\(\s*')
NODE_END_TREE   = re.compile(r'\s*\)\s*')
# for xrsparse
#VAR_XRS        = re.compile(r'\s*([^\s\(\)]+)\.x(\d+)\s*[$\s\)]') # does not match, due to the bug that $ cannot coexist with other char in the [] syntax
VAR_XRS        = re.compile(r'\s*([^\s\(\)]+)\.x(\d+)\s*$|\s*([^\s\(\)]+)\.x(\d+)\s*(?=[\s\)])')
def ptbparse(s, pos = 0, depth = 0):
    '''variable-free, ptb style
       input: ( (S (NP (NN parsing)) (VP (VBZ is) (NP (NN fun)))) )
       output: Tree object, same as xrsparse output
    '''
    c_match = CONST_TREE.match(s, pos)
    if c_match:
        pos = c_match.end()
        #print "matched, pos = m.end(): ", pos, 'prefix', s[:pos]
        c_symbol = c_match.group().strip()
        #print 'const',c_symbol
        node = Tree(c_symbol, None, [], None)
        return pos, node

    nb_match = NODE_BEGIN_TREE.match(s, pos)
    if nb_match:
        pos = nb_match.end()
        pos, tmp = ptbparse(s, pos, depth)
        if tmp:
            node = tmp
            while pos < len(s):
                ne_match = NODE_END_TREE.match(s, pos)
                if ne_match:
                    pos = ne_match.end()
                    break
                pos, newnode = ptbparse(s, pos, depth+1)              
                node.children.append(newnode)
            return pos, node   
    return pos, None


def xrsparse(s, pos = 0, depth = 0):
    '''return a (pos, tree) pair
    '''
    #print 's ', s, '\tpos ',pos,'\tworking on ', s[pos: len(s)]

    node = None

    # variable match has to be done before terminal match
    v_match = VAR_XRS.match(s, pos)
    if v_match:
        pos = v_match.end()
        v_symbol = v_match.group(0).strip()
        #print 'variable', v_symbol
        if v_match.group(1):
            nt, i = v_match.group(1), v_match.group(2)
        elif v_match.group(3):
            nt, i = v_match.group(3), v_match.group(4)

        #print 'nt, i', nt, i
        node = Tree(nt, Tree.VARIABLE, [], int(i))
        return pos, node

    c_match = CONST_TREE.match(s, pos)
    if c_match:
        pos = c_match.end()
        #print "matched, pos = m.end(): ", pos, 'prefix', s[:pos]
        c_symbol = c_match.group().strip()
        #print 'const',c_symbol
        node = Tree(c_symbol, None, [], None)

    nb_match = NODE_BEGIN_TREE.match(s, pos)
    if nb_match:
        pos = nb_match.end()
 
        while pos < len(s):
            ne_match = NODE_END_TREE.match(s, pos)
            if ne_match:
                pos = ne_match.end()
                break
            pos, newnode = xrsparse(s, pos, depth+1)              
            node.children.append(newnode)
    return pos, node   


def nitrogen_AMRrestruct(amr, inlist):
    ''' return a new amr!
    '''
    debug = False
    if debug:
        print 'in restruct, amr', amr.pp()
        print 'in restruct, amr internal', amr.pp_internal()
        print 'in restruct, inlist', \
              ' '.join(str(i[0]) + ' ' + str(i[1]) for i in inlist)

    #TODO: currently only insert something like ":modal x0"
    # need to check constant if insert "/ possible"
    mother_psr = None
    if amr.type == FeatGraph.VARIABLE:
        for ind, psr in inlist:
            #print 'considering', ind, psr
            if ind == amr.id:
                mother_psr = psr
                #print 'mother_psr is variable, matches', mother_psr
                break
    # another case is qnn.invest-01 -> qnn.investment
    elif not amr.feats:
        if debug: print 'return new amr from restruct', amr.pp(), amr.pp_internal()
        return amr
    
    # traverse features of the rule
    newfeats = []
    for f in amr.feats:
        if f.edge == ADD:
            newfeats.extend(f.node.getfeats())
        else:
            newfeats.append(f)
   
    # only need to recurse for newfeats coming from rule side
    for f in newfeats:
        f.node = nitrogen_AMRrestruct(f.node, inlist)
    # note: 'z9' is val for restructed node everywhere, does not cause confusion because we compare equality by id, not val
    newnode = FeatGraph(None, 'z9', None, list(mother_psr.getfeats())+newfeats) 
    newnode.assign_id_nonrecurs()
    if debug: print 'return new amr from restruct', newnode.pp(), newnode.pp_internal()
    return newnode


def matchfeats(psr, rulefeats):
    '''return a set of mappings, each of which is a tuple of variable assignments'''
    debug = False
    if debug:
        print '/////////////////////// in matchfeats'
        print 'psrfeats\n', ' '.join(str(f) for f in psr.getfeats())
        print 'rulefeats\n', ' '.join(str(f) for f in rulefeats)

    # result to be returned
    mappings = set()
    assignment_dict = get_assignment_dict(psr, rulefeats)
    if assignment_dict:
        mappings |= get_mappings(psr, rulefeats, assignment_dict)
    return mappings 


def get_assignment_dict(psr, rulefeats):
    '''traverse psr to get all possible assignments
       carefully guide through the :or and :or-op structure
    '''
    debug = False
    # all possible assignments
    assignment_dict = Recursive_defaultdict()

    for psrfeat in psr.getfeats():

        # case 1: :or-op, have to at least match one of the feats under :opx
        if psrfeat.edge == ':or-op':
            assignment_dict[psrfeat] = get_assignment_dict_or_op(PartialSemRef(psrfeat.node), psrfeat, rulefeats)

        # case 2: :or, have to at least match one of the feats under :or
        elif psrfeat.edge == ':or':
            assignment_dict[psrfeat] = get_assignment_dict_or(PartialSemRef(psrfeat.node), psrfeat, rulefeats)
 
        # case 3: ordinary case with no disjunctive AMR, nonrecursive
        else:
            assignment_dict[psrfeat] = set()
            for rulefeat in rulefeats:
                sub_mappings = match_one_to_one(psr, psrfeat, rulefeat) 
                assignment_dict[psrfeat] |= sub_mappings
            if not assignment_dict[psrfeat]:
                return None 

    if debug:
        print '++++++++++++++++++++++++++++++++'
        print 'assignment_dict'
        print assignment_dict.pp_indented()
        print '++++++++++++++++++++++++++++++++'

    return assignment_dict


def get_assignment_dict_or_op(psr, psrfeat, rulefeats):
    '''get assignment for :or-op structure, can be recursive
    '''
    # result to be returned
    assignment_dict = Recursive_defaultdict()

    # TODO: assert that psrfeat is :or-op
    for op_feat in psrfeat.node.feats[1:]:        
        for sub_op_feat in op_feat.node.feats:
            if sub_op_feat.edge == ':or-op':
                assignment_dict[op_feat][sub_op_feat] = get_assignment_dict_or_op(PartialSemRef(sub_op_feat.node), sub_op_feat, rulefeats)
            elif sub_op_feat.edge == ':or':
                assignment_dict[op_feat][sub_op_feat] = get_assignment_dict_or(PartialSemRef(sub_op_feat.node), sub_op_feat, rulefeats)
            else: 
                assignment_dict[op_feat][sub_op_feat] = set()
                for rulefeat in rulefeats:
                    sub_mappings = match_one_to_one(PartialSemRef(op_feat.node), sub_op_feat, rulefeat)
                    assignment_dict[op_feat][sub_op_feat] |= sub_mappings
    return assignment_dict


def get_assignment_dict_or(psr, psrfeat, rulefeats):
    '''get assignment for :or structure, can be recursive
    '''
    # result to be returned
    assignment_dict = Recursive_defaultdict()

    # TODO: assert that psrfeat is :or
    for f in psrfeat.node.feats[1:]:
        if f.edge == ':or-op':
            assignment_dict[f] = get_assignment_dict_or_op(PartialSemRef(f.node), f, rulefeats)
        elif f.edge == ':or':
            assignment_dict[f] = get_assignment_dict_or(PartialSemRef(f.node), f, rulefeats)
        else: 
            assignment_dict[f] = set()
            for rulefeat in rulefeats:
                sub_mappings = match_one_to_one(PartialSemRef(psrfeat.node), f, rulefeat)
                assignment_dict[f] |= sub_mappings
    return assignment_dict
 

# TODO: remove psr and check :rest at legalize???
def match_one_to_one(psr, psrfeat, rulefeat):
    '''match one psrfeat with one rulefeat
       return set of var assignments, or None
    '''
    debug = False
    if debug:
        print '////////in match_one_to_one'
        print 'psr', psr
        print 'rulefeat', rulefeat, '\npsrfeat', psrfeat

    # every psrfeat can match :rest, sometimes with lookahead check
    rel_rest = re.match(REL_REST, rulefeat.edge)
    if rel_rest:
        concept_lookahead = rel_rest.group(2)     
        if concept_lookahead:
            if not psr.is_lookahead_ok(concept_lookahead):
                return set()
        mapping = ( EdgeAssignment(psrfeat, rulefeat) , )
        return set([ mapping ])

    if psrfeat.edge == rulefeat.edge:
        # recurse
        subpsr = PartialSemRef(psrfeat.node)
        return nitrogen_AMRmatch(subpsr, rulefeat.node)
    return set()


def get_mappings(psr, rulefeats, assignment_dict):
    # apply set addition and multiplication to get linear mappings
    linearized_mappings = linearize(assignment_dict)
    # self-consistent and consistent with rule
    legal_mappings = finalize(linearized_mappings, psr, rulefeats)
    return legal_mappings


def get_terminal_nodes(feats):
    ret = []
    for f in feats:
        if not f.node.feats:
            ret.append(f.node)
        else:
            ret.extend( get_terminal_nodes(f.node.feats) )
    return ret


def finalize(mappings, psr, rulefeats):
    '''legal, in terms of reentrancy, rulefeats and psrfeats coverage'''
    debug = False
    terminal_nodes_rule = get_terminal_nodes(rulefeats)
    if debug:
        print 'input rulefeats', ' '.join(str(f) for f in rulefeats)
        print 'terminal_nodes', ' '.join(str(n) for n in terminal_nodes_rule)
    legal_mappings = set()
    for mapping in mappings:
        if debug:
            print 'in legalize, considering', mapping
            print ' '.join(str(i) for i in mapping)
        # all terminal rulenodes get assignment
        node_assignments = [i for i in mapping if type(i) == NodeAssignment]
        edge_assignments = [i for i in mapping if type(i) == EdgeAssignment]
        terminal_nodes_psr = [i.rulenode for i in node_assignments] + list( set(i.rulefeat.node for i in edge_assignments) )
        if Counter(terminal_nodes_psr) != Counter(terminal_nodes_rule):
            if debug: print 'ERROR: not one-to-one mapping with rule nodes (except :rest)!'
            continue
        elif len( set(i.psr for i in node_assignments) ) != len( set(i.rulenode for i in node_assignments) ):
            if debug: print 'ERROR: assigning different psr nodes to the same rule node!'
            continue

        if edge_assignments:
            new_psr = PartialSemRef( set(i.psrfeat for i in edge_assignments) )
            if debug: print 'new_psr', new_psr
            new_na = NodeAssignment(new_psr, edge_assignments[0].rulefeat.node)
            node_assignments.append(new_na)
            mapping = tuple(node_assignments)

        if debug: print 'legal mapping', ' '.join(str(i) for i in mapping)
        legal_mappings.add(mapping) 

    return legal_mappings       


def linearize(assignment_dict):
    '''recursive linearization of assignment_dict, to get overall mapping
    '''
    debug = False

    if debug:
        print '++++++++++++++++++++++++++++++++'
        print 'start linearize, considering assignment_dict'
        print assignment_dict.pp_indented()
        print '++++++++++++++++++++++++++++++++'

    # result to be returned
    linearized_mappings = set()

    # list of mappings per feat
    all_feat_mappings = []

    for f in assignment_dict:
        #print 'linearizing feat', f
        if f.edge == ':or-op':
            all_op_mappings = []
            for op_f in assignment_dict[f]:
                all_op_mappings.append( linearize(assignment_dict[f][op_f]) )
            if debug: print 'all_op_mappings', all_op_mappings
            # empty tuple, knowing that the final product will be empty tuple
            if not all_op_mappings:
                return linearized_mappings
            all_feat_mappings.append(   tuple(itertools.chain(*all_op_mappings) )   )
        # no recursion, based on the assumption that :or and :or-op will not be directly under :or
        elif f.edge == ':or':
            or_result = tuple(itertools.chain(*assignment_dict[f].values()))
            if not or_result:
                return linearized_mappings
            all_feat_mappings.append(or_result)
        else:
            #v = assignment_dict[f]
            #if type(v) == set:
             #   all_feat_mappings.append(v)
            #elif type(v) == Recursive_defaultdict:
             #   print 'recurse from normal feat'
                #all_feat_mappings.append(  linearize(v) )
            all_feat_mappings.append( assignment_dict[f] )

    hier_mappings = itertools.product(*all_feat_mappings)

    for h in hier_mappings:
        if debug: 
            print '^^^^^^^^considering hier_mapping'
            print h
        linearized = get_linear(h)
        if debug:
            print 'linearized'
            print ' '.join(str(i) for i in linearized)
        linearized_mappings.add(linearized)

    #if debug:
     #   print '++++++++++++++++++++++++++++++++'
      #  print 'end linearize, considering assignment_dict'
       # print assignment_dict.pp_indented()
        #print '++++++++++++++++++++++++++++++++'

    #print 'return linearized_mappings', linearized_mappings
    return linearized_mappings


def get_linear(col):
    if type(col) not in [list, tuple, set]:
        return (col,)
    ret = ()
    for i in col:
        ret += get_linear(i)
    return ret


def nitrogen_AMRmatch(psr, rulelhs):
    '''match two graphs: psr and rulelhs, return a set of mappings'''
    debug = False
    if debug:
        print '-----------------------in nitrogen_AMRmatch'
        print 'psr', psr, \
              'feats', ' '.join(str(i) for i in psr.getfeats())
        print 'rulelhs', rulelhs, \
              'feats', ' '.join(str(i) for i in rulelhs.getfeats())

    # result to be returned
    mappings = set()

    # rulelhs has no feats, i.e., is either variable like x0, or concept
    if not rulelhs.feats:
        # case 1: match rulelhs x0 with eat, or (e / eat)
        # case 2: match rulelhs eat with eat
        if rulelhs.type == FeatGraph.VARIABLE or \
           psr.is_term() and psr.arg.val == rulelhs.val:
            mapping = ( NodeAssignment(psr, rulelhs), )
            mappings.add( mapping )

    # rulelhs has feats, recursive match to get mappings
    elif psr.getfeats():
        mappings |= matchfeats(psr, rulelhs.feats)
    
    return mappings


def get_rules_to_match(state, rules):
    #print 'in get_rules_to_match', state

    if state == GENERIC_STATE:
        ret = []
        # disallow q state AMR to match rules like:
        # qvp_pass.x0 -> qvp.(x0 :add (:passive +))
        # qvp.x0 -> qvp_pres.x0
        # qs1.x0 -> S(qs.x0 P(.))
        for i in itertools.chain.from_iterable(rules.values()):
            if i.lhs.type != FeatGraph.VARIABLE:
                ret.append(i)
        return ret
    elif state in rules:     
        return rules[state]
    return []

# not used
def get_rules_to_match_bk(state, rules):
    if state == GENERIC_STATE:
        # chain a list of lists
        rules_to_match = itertools.chain.from_iterable(rules.values())
    elif state in rules:
        # TODO: itertools.chain more efficient than l1 + l2??? 
        rules_to_match = itertools.chain(rules[GENERIC_STATE], rules[state])
    else:
        rules_to_match = rules[GENERIC_STATE]
    return rules_to_match


def derive_from_rule(dnode, df, rules):

    debug = False
    derived = False

    if debug:
        print '////////////////////////////////////////'
        print 'in derive_from_rule, trying dnode', dnode

    rules_to_match = get_rules_to_match(dnode.state, rules)
    for rule in rules_to_match:
        if debug: print 'trying to match rule', rule

        mappings = nitrogen_AMRmatch(dnode.psr, rule.lhs)
        for mapping in mappings:
            var_tuples = [(i.rulenode.id, i.psr) for i in mapping if i.rulenode.type == FeatGraph.VARIABLE ]
            if debug:
                print 'matched rule', rule
                print 'mapping', mapping
                print 'var_tuples', '\t'.join(str(i[0])+'__'+str(i[1]) for i in var_tuples) 

            # restruct
            if rule.type == Rule.RESTRUCT:
                new_amr = nitrogen_AMRrestruct(copy.deepcopy(rule.rhs), var_tuples)
                new_psr = PartialSemRef(new_amr)
                if debug:
                    print 'to restruct', dnode, 'with rule', rule                
                    print 'after restruct, new_psr', new_psr
                new_dnode = DerivationNode(rule.rhsstate, new_psr)
                new_dnode_derived, new_dnode = derive(new_dnode, df, rules)
                # only if the new_dnode gets derived do we call dnode derived
                # and create hyperedge. this is recursive definition
                if new_dnode_derived:
                    # transition like qvp.x0 -> vp(to(to) qvp.x0) leads to infinite loop
                    if new_dnode == dnode:
                        continue      
                    h = Hyperedge(rule, dnode, [new_dnode])
                    dnode.hpes.append(h)
                    derived = True

            # translate
            else:
                composed_rhs = compose_tree(rule.rhs, var_tuples)
                new_dnodes = []
                new_dnodes_derived = True
                is_infinite_loop = False
                for new_dnode in get_dnodes(composed_rhs):
                    if new_dnode == dnode:
                        is_infinite_loop = True
                        break
                    new_dnode_derived, new_dnode = derive(new_dnode, df, rules)
                    new_dnodes.append(new_dnode)
                    if not new_dnode_derived:
                        new_dnodes_derived = False
                        break
                if is_infinite_loop:
                    continue
                # only if all new_dnodes get derived do we call dnode derived
                # and create hyperedge. this is recursive definition                    
                if new_dnodes_derived:
                    h = Hyperedge(rule, dnode, new_dnodes)
                    h.comp_rhs = composed_rhs
                    dnode.hpes.append(h)
                    derived = True

            #break # break at the first mapping of first matched rule

    return derived, dnode


def derive(dnode, df, rules):
    '''three attempts:
       1) first attempt, try to match real input rules
       2) if 1) fails, convert state to universal state and try again
          case a: terminal AMR, when we don't have rules to match
                  qvbd.eat, use this conversion: qvbd.x0 -> q.x0
                  to get q.eat, then we may match qvb.eat -> VB(eat),
                  qvbz.eat -> VBZ(eats), etc.
          case b: nonterminal AMR, when we don't have rules to match
                  qnp.(e / eat :ARG0 (c / cat)), use this conversion:
                  qnp.x0 -> q.x0 to get q.(e / eat :ARG0 (c / cat)),
                  then we may match qs.(e / eat :ARG0 x0) -> S(...)
       3) if 2) fails, construct a default rule on the fly
          case a: terminal AMR, generate the predicate w/o sense index
          case b: nonterminal AMR, monotonic order of args
    '''
    #print 'b4 checking dict'
    #for psr in df:
     #   print psr
      #  for dnode in df[psr]:
       #     print dnode
    #print
    for dnode_i in df[dnode.psr]:
        if dnode_i == dnode:            
            #print dnode, 'has entry as', dnode_i
            if dnode_i.hpes:
                return True, dnode_i
            else:
                return False, dnode_i

    derived, dnode = derive_from_rule(dnode, df, rules)

    # TODO: see if this variable is passed
    if ( options.state_trans == 'unlimited' or (not derived and options.state_trans == 'limited') ) and dnode.state != GENERIC_STATE:

        # TODO: should we use dnode.psr, or the deepcopy of it??? the key is that this is not a one-shot solution, and we may need to backup to default rules
        new_dnode = DerivationNode(GENERIC_STATE, dnode.psr)
        #print 'new_dnode after state transition', new_dnode

        derived, new_dnode = derive(new_dnode, df, rules)

        if derived:
            # universal state q, like qvp.x0 -> q.x0
            # x0 can match eat or (e / eat :ARG0 (c / cat))
            newlhs = FeatGraph(0, 'x0', FeatGraph.VARIABLE, [])
            newrhs = Tree(GENERIC_STATE, Tree.VARIABLE, [], 0) # q.x0
            # TODO: provenence feature based on Rule.STATETRANS? but seems that it is the only option for the AMR!
            newrule = Rule(dnode.state, newlhs, None, newrhs, TRANSITION_RULE_PROB, Rule.STATETRANS)
            #print 'newrule for state transition', newrule

            h = Hyperedge(newrule, dnode, [new_dnode])
            dnode.hpes.append(h)
            #return derived, dnode
    if not derived:
        #print 'go to default', dnode
        derived, dnode = derive_from_default(dnode, df, rules)

    df[dnode.psr].add(dnode)

    return derived, dnode


SENSE_AMR = re.compile(r'.+-\d+$')
def derive_from_default(dnode, df, rules):
    '''construct rules on the fly'''

    if dnode.psr.is_term():
        if not 't' in default_rule_opts:
            if options.debug: print >> logs, 'cannot generate terminal: ' + str(dnode)
            return False, dnode
        #print 'default rule for term', dnode
        newlhs = dnode.psr.arg
        wordtrans = dnode.psr.arg.val

        # strip off double quotes for opx valule
        # :op1 "Max" -> Max
        if wordtrans[0] == wordtrans[-1] == '"':
            wordtrans = wordtrans[1:-1]
        # TODO: poor man's solution: strip off 
        # sense index as in want-01 and include-91
        # missing out sense info
        #if SENSE_AMR.match(wordtrans):
         #   wordtrans = wordtrans.rsplit('-',1)[0]

        newrhs = Tree(dnode.state, None, [Tree(wordtrans, None, [], None)], None)
        newrule = Rule(dnode.state, newlhs, None, newrhs, DEFAULT_RULE_PROB, Rule.DEFAULT)
        #TODO: third member used to be newrhs
        h = Hyperedge(newrule, dnode, [])
        dnode.hpes.append(h)

        return True, dnode
    
    else:
        if not 'nt' in default_rule_opts:
            if options.debug: print >> logs, 'cannot generate nonterm: ' + str(dnode)
            return False, dnode
        #print 'default rule for nonterm', dnode
        new_dnodes = []
        new_dnodes_derived = True
        #TODO: like wise: check all forest and printable forest
        for ind, feat in enumerate(dnode.psr.getfeats()):
            new_dnode = DerivationNode(GENERIC_STATE, PartialSemRef(feat.node))
            new_dnode_derived, new_dnode = derive(new_dnode, df, rules)
            if new_dnode_derived:
                new_dnodes.append(new_dnode)
            else:
                new_dnodes_derived = False

        if new_dnodes_derived:

            newlhs = FeatGraph(None, '', None, [])
            newrhs = Tree(dnode.state, None, [], None) 
            for ind, feat in enumerate(dnode.psr.getfeats()):
                newlhs.feats.append(Feat(feat.edge, FeatGraph(ind, 'x'+str(ind), FeatGraph.VARIABLE, [])))
                newrhs.children.append(Tree(GENERIC_STATE, Tree.VARIABLE, [], ind))
            newrule = Rule(dnode.state, newlhs, None, newrhs, DEFAULT_RULE_PROB, Rule.DEFAULT)

            new_composed_rhs = Tree(dnode.state, None, new_dnodes, None)
            #TODO: third member used to be new_composed_rhs
            h = Hyperedge(newrule, dnode, new_dnodes)
            dnode.hpes.append(h)

            #print 'newrule', newrule
            #print 'new_hpe', h

            return True, dnode

        return False, dnode



START_STATE = re.compile(r'\s*[a-zA-Z][\w-]*\s*\n\s*')  # 'q', 'qvp_pass'
RULE        = re.compile(r'\s*[^\n]+(?:\s*->[^\n]+\n)+\s*')
RULE_STATE  = r'\s*[a-zA-Z][\w-]*\.\s*' # 'q.', 'NP.', 'qvp_pass.'
# ygao20121011: no longer require brackets on RHS for restruct
# rule matching, but make sure that RHS is not variable node,
# so that we have "qnn.write-06 -> qnn.writing" as restruct rule,
# otherwise qnn.writing will be treated as constant
# TODO: matching is two-step as I cannot figure out how to
# exclude a string pattern in regex
RESTRUCT_RULE = re.compile(r'(%s)(.+)'%RULE_STATE)
#RESTRUCT_RULE = re.compile(r'(%s)(\(.+\))'%RULE_STATE)

# matched in this order:
# LHS_RHS.. -> RHS_COMMENT.. -> RHS_PROB..
LHS_RHS_SPLIT = re.compile(r'\s*->\s*')
RHS_COMMENT_SPLIT = re.compile(r'\s+##\s+')
RHS_PROB_SPLIT = re.compile(r'\s+#\s+')

def get_grammar(s):
    sstate = GENERIC_STATE
    ruledict = defaultdict(set)

    pos = 0
    while pos < len(s):
        #print s[pos:pos+20]
        #print 'pos', pos, 's', s
        comment_match = COMMENT.match(s, pos)
        if comment_match:
            pos = comment_match.end()
            comment_symbol = comment_match.group().strip()
            #print 'matched comment', comment_symbol, 'pos now', pos
            continue

        ss_match = START_STATE.match(s, pos)
        if ss_match:
            #print 'start state match, ', ss_match.group().strip()
            pos = ss_match.end()
            if ss_match.group().strip() != GENERIC_STATE:
                sstate = ss_match.group().strip()
            continue

        rule_match = RULE.match(s, pos)
        if rule_match:
            #print 'rule matched'
            pos = rule_match.end()
            rulestr = rule_match.group().strip()
            #print 'rulestr', rulestr
            rulesplit = re.split(LHS_RHS_SPLIT, rulestr)
            #print 'rulesplit', rulesplit
            # no regex to detect lhsstate, since we are
            # sure it is before the first dot split
            lhsstate, lhsstr = rulesplit[0].strip().split('.', 1)
            #print 'to rule_amrparse', lhsstr
            _, lhs = rule_amrparse(lhsstr)
            lhs.assign_id_rule()
            #TODO: test if the global_rule_node_id works for restruct rules
            lhs.rest_to_end() # make :rest the last feat to match
            #print '^^^^^^^^^^^^^rule lhs'
            #print lhs.pp_indented()
            #print lhs.pp_internal()

            # construct a rule for each of the multiple rhs
            for i in rulesplit[1:]:
                i = i.strip()

                rhs_comment_split = re.split(RHS_COMMENT_SPLIT, i)

                main = rhs_comment_split[0]

                rhs_prob_split = re.split(RHS_PROB_SPLIT, main)
                structstr = rhs_prob_split[0]
                if len(rhs_prob_split)==2:
                    #prob = math.log( float(rhs_prob_split[1]) )
                    prob = float(rhs_prob_split[1])  
                else:              
                    # using log prob
                    prob = 0.0

                rr_match = RESTRUCT_RULE.match(structstr, 0)
        
                # rhs is a featgraph, for restructuring rules
                if rr_match and (not X_NODE_AMR.match(rr_match.group(2))):
                    #print 'rr_match'
                    rhsstate = rr_match.group(1).strip()[:-1]
                    rhsamr = rr_match.group(2)
                    #print 'rhsstate', rhsstate
                    #print 'rhsamr', rhsamr
                    _, rhs = rule_amrparse(rhsamr)
                    #print 'before assign_id_rule, rhs internal', rhs.pp_internal()
                    rhs.assign_id_rule()
                    #print 'after assign_id_rule, rhs internal', rhs.pp_internal()
                    type = Rule.RESTRUCT
                else:
                    rhsstate = None
                    #print 'to xrsparse:', structstr.strip()
                    _, rhs = xrsparse(structstr.strip())
                    #print 'tree', rhs.pp()
                    #print 'dot for tree'
                    #print to_dot_graph(rhs)
                    type = Rule.NORMAL

                count = 1

                if len(rhs_comment_split) == 2:
                    comment = rhs_comment_split[1]
                    split = comment.split(' ^ ')
                    for i in split:
                        if i.startswith('count:'):
                            count = int(i.split('count:')[1])
                        # if differs from previous def, follow explicit def here
                        if i.startswith('type:'):
                            typestr = i.split('type:')[1].strip()
                            if not typestr:
                                typestr = 'unknown'
                            type = Rule.TYPE_DICT[typestr]                

                ruledict[lhsstate].add( Rule(lhsstate, lhs, rhsstate, rhs, prob, type, count) )



    return (sstate, ruledict)


def to_dot_graph(obj):
    '''format for each line
       case graph: "p" -> "possible" [label ="instance"];
       case tree:  "S" -> "NP" [label =""];
       case singleton tree: "qmd.x0";
    '''
    #print 'returned triple', obj.gettriples()
    return 'digraph g {\n' + '\n'.join('"' + \
           i[0] + '"' + ' -> ' + '"' + i[1] + '"' + \
           ' [label =' + '"' + i[2] + '"' + '];' \
           if len(i)==3 else '"' + i[0] + '"' + ';'
           for i in obj.gettriples()) + '\n}\n'


def compose_output_tree(tree, vec):
    '''get output tree from a kbest derivation
    '''
    if tree.__class__.__name__ == 'DerivationNode':
        return kbest[tree][vec.pop(0)].get_tree(), vec
    # xrstree, terminal
    elif not tree.children:
        return tree, vec
    # xrstree, nonterm
    ret = Tree(tree.node, None, [], None)
    for c in tree.children:
        cout, vec = compose_output_tree(c, vec)
        ret.children.append(cout)
    return ret, vec


def compose_tree(xrstree, inlist):

    #print 'in compose_tree', xrstree.pp(), 'inlist', ' '.join('(' + str(i[0]) + ', ' + str(i[1]) + ')' for i in inlist)
    '''result is xrstree with subnodes replaced by derivationnodes;
       or a single derivationnode; inlist is constant, a listed
       item is not consumed by any node. so I allow one thing
       to go to two places, like S(NP.x0 VP(V.x1 PRO.x0))
       nitrogen style
       when do we need such nodes: qs.(/ x0 :ARG0 x1 :ARG1 x1) -> S(NP.x1 VP(V.x0 PRO-REFLEXIVE.x1))
       for "the boy likes himself"
       qs.(/ kill :ARG0 x1 :ARG1 x1) -> V(suicide)
       need a rule to say PRO-REFLEXIVE.boy -> PRO(himself)
    '''
    if xrstree.type == Tree.VARIABLE:
        for ind, psr in inlist:
            if ind == xrstree.id:
                return DerivationNode(xrstree.node, psr) 
        #TODO announce error here, since we require sth that does not exist on lhs
    ret = Tree(xrstree.node, None, [], None)
    for c in xrstree.children:
        ret.children.append(compose_tree(c, inlist))
    return ret


def get_dnodes(tree):
    ret = []
    if tree.__class__.__name__ == 'DerivationNode':
        ret.append(tree)
    else:
        for c in tree.children:
            ret.extend(get_dnodes(c))
    return ret 


def get_kbest(k, dnode):
    lazy_jth_best(dnode, k-1)
    return kbest[dnode]   


def lazy_jth_best(v, j):
    '''cube growing implementation w/o buffer
       v is a derivationnode; j is a scalar
       almost the same terminology as paper,
       just change D to kbest and cand to cands
    '''
    #print 'in lazy_jth, v', str(v), 'j', j
    if v not in cands:
        cands[v] = []
        heapq.heapify(cands[v])
        for e in v.hpes:
            #print 'considering hpe', str(e)
            fire(e, [0]*len(e.children), cands[v])

    #print 'after init, size for cands v', str(v), len(cands[v]), 'kbest, v', len(kbest[v])

    while len(kbest[v]) <= j and cands[v]:
        item = heapq.heappop(cands[v])
        #print 'item popped', str(item)
        # no buffer is used, since no lm issue
        kbest[v].append(item)
        pushsucc(item, cands[v])
    #print 'finish lazy_jth for v', str(v), len(cands[v]), 'kbest, v', len(kbest[v])
    #print '------------------'

def fire(e, jvec, cand):
    '''recursively invoke lazy_jth_best, thus the name
    '''
    for ind, sub_j in enumerate(jvec):
        u = e.children[ind]
        lazy_jth_best(u, sub_j)
        if len(kbest[u]) <= sub_j:
            return
    kb_item = kbest_item(e, jvec)
    heapq.heappush(cand, kb_item)

def pushsucc(kb_item, cand):
    '''kb_item wraps up (e, j) in paper
    '''
    #print 'in pushsucc, kb_item', kb_item 
    e = kb_item.hpe
    jvec = kb_item.vector
    for i in xrange(len(jvec)):
        new_jvec = jvec[:i] + [jvec[i]+1] + jvec[i+1:]
        #print 'new_jvec', new_jvec, 'for e', str(e)
        if tuple(new_jvec) not in e.oldvecs:
            fire(e, new_jvec, cand)
            e.oldvecs.add(tuple(new_jvec))


# not used
def get_derivation_forest(dnode):
    ''' slow version! not used
        bfs on the derivation hypergraph
        output in cdec forest format
        [lhs] ||| [rhs-nonterm]* rhs-term* [||| feat=val*] 
    '''
    start_triple = '[S] ||| ' + str(dnode)
    ret = [start_triple]
    queue = [dnode]
    black = [] # finished processing
    while queue:
        curr = queue.pop(0)
        #print 'popping', curr
        for hpe in curr.hpes:
            #print 'appending', hpe
            ret.append(str(hpe))
            for c in hpe.children:
                #print 'c', c
                if (c not in queue) and (c not in black):
                    queue.append(c)
        black.append(curr)
    return ret


def get_filtered_rules(rules, input_amr):
    '''filter rules for each input amr
    '''
    in_constants = input_amr.get_unique_constants() | set([REST])
    # note: since restruct rules introduce new amr to input, have to examine
    # all restruct rules first to finalize in_constants
    for state in rules:
        for rule in rules[state]:
            if rule.type == Rule.RESTRUCT:
                lhs_constants = rule.lhs.get_unique_constants()
                if lhs_constants.issubset(in_constants):
                    in_constants |= rule.rhs.get_unique_constants()

    filtered_rules = defaultdict(set)
    for state in rules:
        for rule in rules[state]:
            lhs_constants = rule.lhs.get_unique_constants()
            if lhs_constants.issubset(in_constants):
                filtered_rules[state].add(rule)

    #print 'finally unique const', ' '.join(in_constants)
    return filtered_rules


#TODO; ugly, should use bfs instead of keeping ceo_dict
ceo_dict = {}
def get_ceo(amr):
    if amr in ceo_dict:
        return ceo_dict[amr]
    if not amr.feats:
        return [amr]

    # result to be returned
    newnodes = []

    # store features to be multiplied
    feat_list = []
    for f in amr.feats:
        if f.edge == ':or-op':
            new_edges_all_op = []
            for op_f in f.node.feats[1:]:
                new_edges_all_op.extend( [ i.feats for i in get_ceo(op_f.node) ] )
            feat_list.append( new_edges_all_op )
        elif f.edge == ':or':
            new_edges_all_or = []
            for ff in f.node.feats[1:]:
                new_edges = [ Feat(ff.edge, i) for i in get_ceo(ff.node) ]
                new_edges_all_or.extend( new_edges )
            feat_list.append(new_edges_all_or)
        else:
            new_edges = [ Feat(f.edge, i) for i in get_ceo(f.node) ]
            feat_list.append(new_edges)
    for i in itertools.product(*feat_list):
        newnode = FeatGraph(amr.id, amr.val, None, get_linear(i))
        newnodes.append(newnode)

    ceo_dict[amr] = newnodes 

    return newnodes


def get_ceo_count(amr, ceo_count_dict):
    if amr in ceo_count_dict:
        return ceo_count_dict[amr]
    if not amr.feats:
        return 1

    all_count_list = []
    for f in amr.feats:
        if f.edge in [':or-op', ':or']:
            all_count_list.append( sum( [ get_ceo_count(ff.node, ceo_count_dict) for ff in f.node.feats[1:] ] ) )
        else:
            all_count_list.append( get_ceo_count(f.node, ceo_count_dict) )
    tot = reduce( operator.mul, all_count_list ) 
    ceo_count_dict[amr] = tot

    return tot


def merge_dict_set(d1, d2, merge=lambda x,y:x|y):
    """
    ygao modified from web to have set union in lambda, maybe nonrecursive
 
    Merges two dictionaries, non-destructively, combining 
    values on duplicate keys as defined by the optional merge
    function.  The default behavior replaces the values in d1
    with corresponding values in d2.  (There is no other generally
    applicable merge strategy, but often you'll have homogeneous 
    types in your dicts, so specifying a merge technique can be 
    valuable.)

    Examples:

    >>> d1
    {'a': 1, 'c': 3, 'b': 2}
    >>> merge(d1, d1)
    {'a': 1, 'c': 3, 'b': 2}
    >>> merge(d1, d1, lambda x,y: x+y)
    {'a': 2, 'c': 6, 'b': 4}

    """
    result = dict(d1)
    for k,v in d2.iteritems():
        if k in result:
            result[k] = merge(result[k], v)
        else:
            result[k] = v
    return result


def factor_amr(amr, l):
    #print 'to factor amr', amr, 'with list', ' '.join(str(i) for i in l)
    #print 'amr internal', amr.pp_internal()
    if get_list_ind([c.amr for c in l], amr) != -1:
        return FeatGraph(0, 'x0', FeatGraph.VARIABLE, [])

    new_amr = FeatGraph(amr.id, amr.val, None, [])
    for f in amr.feats:
        amr_ind = get_list_ind([c.amr for c in l], f.node)
        # recurse
        if amr_ind == -1:
            new_amr.feats.append( Feat(f.edge, factor_amr(f.node, l) ) )
        # create variable node
        else:
            new_amr.feats.append( Feat(f.edge, FeatGraph(amr_ind, 'x'+str(amr_ind), FeatGraph.VARIABLE, []) ) )
    return new_amr


# NOTE: tree is already a deepcopy, ok to modify
def factor_tree(tree, l):
    '''the opposite of compose_tree
    '''
    #print 'to factor tree', tree, 'with list', ' '.join(str(i) for i in l)
    new_tree = Tree(tree.node, None, [], tree.id)
    for t in tree.children:
        t_ind = get_list_ind([c.tree for c in l], t)
        if t_ind == -1:
            new_tree.children.append( factor_tree(t, l) )
        else:
            new_tree.children.append( Tree('q'+t.node, Tree.VARIABLE, [], t_ind) )
    return new_tree


def get_node_align(amr, tree, node_align_dict, amr_outspan = set(), tree_startpos = 0):
    get_node_align_for_amr(amr, tree, node_align_dict, amr_outspan, tree_startpos)
    for ind_f, f in enumerate(amr.feats):
        # escape trivial amr nodes that are unaligned, 
        # such as 'thing' in (/ thing :arg1-of xxx)
        if not f.node.getspan():
            continue
        # NOTE: reentrancy-aware getspan_except, don't include span of reentrant node!
        sibling_span = set( itertools.chain( *(ff.node.getspan_except(f.node) for ind, ff in enumerate(amr.feats) if ind != ind_f) ) ) \
                           | set( itertools.chain( *(ff.alignset for ff in amr.feats) ) )
        f_outspan = amr_outspan | sibling_span
        get_node_align(f.node, tree, node_align_dict, f_outspan, tree_startpos)


#TODO: consider edge alignment such as :topic
#TODO: change DerivationNode_Align to DerivationNode only!
def get_node_align_for_amr(amr, tree, node_align_dict, amr_outspan, tree_startpos):
    ''' input: amr-tree-alignment triple, fill in node_align_dict
    '''
    #debug = True
    debug = False

    # stop at tree pos level
    if not tree.children:
        return

    tree_len = tree.numLeaves()
    tree_endpos = tree_startpos + tree_len - 1
    tree_span = set(range(tree_startpos, tree_endpos+1))
    amr_span = amr.getspan()

    if debug:
        print '------in get_node_align_for_amr, consider amr', amr.pp(), 'tree', tree.pp()
        print 'amr_outspan', amr_outspan
        print 'tree_span', tree_span
        print 'amr span', amr.getspan()
        print 'amr alignset', amr.alignset

    if amr_span & tree_span:
        sub_tree_startpos = tree_startpos
        for c_tree in tree.children:
            get_node_align_for_amr(amr, c_tree, node_align_dict, amr_outspan, sub_tree_startpos)
            sub_tree_startpos += c_tree.numLeaves()

        # frontier node check adopted from ghkm, equivalent to node alignment check in hanneman et al., ssst2011
        if amr_span.issubset(tree_span) and not (amr_outspan & tree_span):
            node_align_dict[amr].add(tree)


def derive_from_alignment(amr, tree, node_align_dict, df):
    # TODO: programs that call it now make sure amr/tree is in node_align_dict BUT should ideally do a check here
    #debug = True
    debug = False
    if debug:
        print 'in derive_from_alignment'
        print 'amr', amr.pp()
        print 'tree', tree.pp()

    # already have entry in df, avoid duplicates
    for dn in df[amr]:
        if dn.tree == tree:
            return dn
 
    dnode = DerivationNode_Align(amr, tree)
    # populate hyperedges under dnode
    if options.binarize and len(amr.feats)>=2 and len(tree.children)>=2:
        dnode = derive_binarized(dnode, node_align_dict, df)
    if not dnode.hpes:
        dnode = derive_natural(dnode, node_align_dict, df)
    df[amr].add(dnode)
    return dnode


#def sync_bin(amr, tree, node_align_dict, direction):
 #   if direction == 'left':
  #      tree_one = tree[-1]
   #     for (amr_other, tree_other) in node_align_dict.iteritems():
    #        if tree_one == tree_other:
                 

# TODO: binarization with :topic~e.3
def derive_binarized(dnode, node_align_dict, df):
    amr, tree = dnode.amr, dnode.tree

    debug = False
    #debug = True
    if debug:
        print 'in derive_binarized'
        print 'amr', amr.pp()
        print 'tree', tree.pp()

    for direction in 'left right'.split():
        #new_amr, new_tree = sync_bin(amr, tree, direction)
        # TODO: tree.children[0] or tree.children[-1] may be aligned to more than one feat, or may be unaligned
        for ind, f in enumerate(amr.feats):
            if direction == 'left' and tree.children[-1] in node_align_dict[f.node] or direction == 'right' and tree.children[0] in node_align_dict[f.node]:
                vamr_feats = list(some_f for some_i, some_f in enumerate(amr.feats) if some_i != ind)
                if debug: print 'vamr_feats after pop', ' '.join(str(i) for i in vamr_feats)
                # head in vnode, go ahead to construct binarized amr and tree          
                if INSTANCE in list(f.edge for f in vamr_feats):
                    #TODO: how to avoid creating duplicate virtual tree/amr??? change these id to match or create??? or check combination of children, multiple ways of arriving at same virtual tree/amr???
                    vamr = get_virtual_amr(amr.val, amr.type, vamr_feats)
                    if direction == 'left':
                        vtree_children = tree.children[:-1]
                        #TODO: to avoid using is_virtual, try to have this amr form like set of feats???
                        dnode_other = derive_from_alignment(f.node, tree.children[-1], node_align_dict, df)
                    elif direction == 'right':
                        vtree_children = tree.children[1:]
                        dnode_other = derive_from_alignment(f.node, tree.children[0], node_align_dict, df)
                    vtree = get_virtual_tree(tree.node, tree.type, vtree_children)
                    vdnode = derive_from_alignment(vamr, vtree, node_align_dict, df)
                    # provide another view of the current node
                    vamr_parent = FeatGraph(amr.id, amr.val, None, [f, Feat(':rest', vamr)])
                    if direction == 'left':
                        vtree_parent = Tree(tree.node, None, [vtree, tree.children[-1]], tree.id)
                    elif direction == 'right':
                        vtree_parent = Tree(tree.node, None, [tree.children[0], vtree], tree.id)
                    vdnode_parent = DerivationNode_Align(vamr_parent, vtree_parent)
               
                    hpe = Hyperedge(None, vdnode_parent, [vdnode, dnode_other])
                    if debug:
                        print 'hpe from bin, pi', hpe.pi
                        print 'children', ' '.join(str(c) for c in hpe.children)
                        print 'rule', hpe.rule
                    dnode.hpes.append(hpe)

    return dnode


# NOTE: to avoid duplicate tree in binarization
def get_virtual_tree(vtree_nodename, vtree_type, vtree_children):
    global global_vtree_dict
    for tree_other in global_vtree_dict:
        if tree_other.children == vtree_children:
            return tree_other
    global global_tree_node_id
    new_vtree = Tree(vtree_nodename, vtree_type, vtree_children, global_tree_node_id, is_virtual=True)
    global_vtree_dict[new_vtree] = global_tree_node_id
    global_tree_node_id += -1
    return new_vtree


# NOTE: to avoid duplicate amr in binarization
def get_virtual_amr(vamr_nodename, vamr_type, vamr_feats):
    global global_vamr_dict
    for amr_other in global_vamr_dict:
        if amr_other.feats == vamr_feats:
            return amr_other
    global global_rule_node_id
    new_vamr = FeatGraph(global_rule_node_id, vamr_nodename, vamr_type, vamr_feats, is_virtual=True)
    global_vamr_dict[new_vamr] = global_rule_node_id
    global_rule_node_id += -1
    return new_vamr


def derive_natural(dnode, node_align_dict, df):
    '''with actual tree/amr, no virtual nodes
    '''
    #debug = True
    debug = False

    if debug:
        print '===================='
        print 'in derive_natural'
        print 'amr', dnode.amr, dnode.amr.pp()
        print 'tree', dnode.tree.pp()

    sub_dnode_list = get_sub_dnode_lists(dnode, dnode.amr, node_align_dict, df)
    for mapping_tup in set(get_linear(i) for i in sub_dnode_list):
        
        hpe = Hyperedge(None, dnode, list(mapping_tup))
        if debug:
            print '---------'
            print 'hpe from natural, pi', hpe.pi
            print 'children', ' '.join(str(c) for c in hpe.children)
            print 'rule', hpe.rule
        dnode.hpes.append(hpe)
    return dnode


def get_sub_dnode_lists(dnode, amr, node_align_dict, df, depth=0):
    debug = False
    if debug: print 'in get_sub_dnode_lists, dnode', dnode, 'amr', amr
    if depth > options.composition_depth:
        return []
    l = []
    # descend amr
    for f in amr.feats:
        subl = []
        if node_align_dict[f.node]:
            for tree_other in node_align_dict[f.node]:
                if not dnode or tree_other.id <= dnode.tree.id or dnode.tree.is_virtual:
                    sub_dnode = derive_from_alignment(f.node, tree_other, node_align_dict, df)
                    subl.append(sub_dnode)
                    subl.extend( get_sub_dnode_lists(sub_dnode, f.node, node_align_dict, df, depth+1) )
        else:
            subl.extend( get_sub_dnode_lists(None, f.node, node_align_dict, df, depth) )
        l.append(subl)
    ret1 = list(itertools.product(*l))
    # keep amr, descend tree
    # example: qtop.x0 -> top(qs.x0 .(.))
    # this is optional, can be turned off
    ret2 = []
    #for tree_other in node_align_dict[amr]:
     #   if tree_other.id < dnode.tree.id or dnode.tree.is_virtual:
      #      sub_dnode = derive_from_alignment(amr, tree_other, node_align_dict, df)
       #     ret2.append((sub_dnode,))
        #    ret2.extend( get_sub_dnode_lists(sub_dnode, amr, node_align_dict, df, depth) )
    return ret1[:50] + ret2[:50]


def get_alignment(amr, tuples):
    for f in amr.feats:
        for tup in tuples:
            amr_tuple = tuple(tup[:-1])
            alignset = set(int(i) for i in tup[-1].rsplit('e.', 1)[1].split(','))
            if len(amr_tuple) == 2 and (amr.val, f.edge) == amr_tuple:
                f.alignset = alignset
            elif len(amr_tuple) == 3 and (amr.val, f.edge, f.node.val) == amr_tuple:
                f.node.alignset = alignset
        get_alignment(f.node, tuples)


if __name__ == '__main__':

    from optparse import OptionParser
    parser = OptionParser(usage="usage: python MY-NAME GRAMMAR(with .grammar suffix) INPUT(with .amr suffix) [options (-h for details)]")
    #TODO: add a -u switch to output unique kbest strings with just rules for kbest rescoring (as opposed to forest rescoring); cdec unique kbest is buggy without lm!
    parser.add_option("-k", "--kbest", dest="k", type=int, help="k-best based on rules. without rule prob, this is random k", default=1000)
    parser.add_option("-r", "--range", dest="range", type=str, help="amr input(s) to generate, starting from 0, form a range with dash, concatenate discontinuous ranges with comma. default is all. example: 0-2,9,19-20 => [0,1,2,9,19,20]", default="all")
    parser.add_option("-o", "--output", dest="output", type=str, help="options: any combination of [forest,tree,string], any order, separated by comma", default="forest,tree,string")
    parser.add_option("-d", "--debug", dest="debug", action="store_true", help="print stuff", default=False)
    # by default only construct default rules for terminal concept, and print non-generatable nonterminals
    parser.add_option("", "--defaultrule", dest="default_rule", type=str, help="use default rule for terminal or nonterminal derivationnode when cannot match, options: any combination of [t,nt] in any order, or simply None", default="t")
    parser.add_option("", "--statetrans", dest="state_trans", type=str, help="state transition from non-generic state to generic state to match more rules, options: None or limited or unlimited", default="limited")
    parser.add_option("", "--replacecoref", dest="replace_coref", action="store_true", help="replace coreferent node with pronoun", default=False)
    parser.add_option("", "--ceo", dest="ceo", action="store_true", help="simple amrs encoded in a disjunctive amr", default=False)
    #TODO: write module for composed rules
    parser.add_option("", "--ghkm", dest="ghkm", action="store_true", help="get a set of ghkm rules", default=False)
    parser.add_option("", "--align", dest="align", action="store_true", help="alignment", default=False)
    parser.add_option("", "--binarize", dest="binarize", action="store_true", help="binarization", default=False)
    parser.add_option("", "--compdep", dest="composition_depth", type=int, help="composition depth", default=0)

    options, args = parser.parse_args()

    print >> logs, 'args ' + str(args)
    print >> logs, 'options ' + str(options)

    if options.align:
        global_input_id = -1
        while True:
            #TODO: lowercasing in wrapper sh, not here
            line = sys.stdin.readline().strip().lower()
            if not line:
                break
            amr_str, align_str = line.split('\t')
            # TODO: support both edge alignments and node alignments
            _, amr = input_amrparse(amr_str)

            global_input_id += 1
            amr.corefy(amr.get_nonterm_nodes())

            #TODO: delete it, this is nonsense
            #global_rule_node_id = -1
            #amr.assign_id_rule()
            global_input_node_id = 0
            amr.assign_id()
            # TODO: carefully match r__:arg1__e.25,6 c__/__cause-01__e.12 c__:arg0
            # TODO: but not u__:value__"www.time.com/time/nation/article/0,8599,1632736,00.html" 
            tups = list(tuple(i.split('__')) for i in align_str.split() if re.match(r'.+e\.[\d,]+$', i) )
            get_alignment(amr, tups)
            print amr.pp()
        sys.exit()

    # TODO: check if this policy works for both rule extraction and application!
    # NOTE: policy assigning id to graph nodes and tree nodes
    # 1) for input amr, start from 0 and increase by 1;
    # 2) for rule amr, rule tree, start from -1 and decrease by 1;
    # 3) in rule extraction mode, for both amr and tree, start from -1 and decrease by 1;
    if options.ghkm:
        global_input_id = -1
        while True:
            #TODO: lowercasing in wrapper sh, not here
            line = sys.stdin.readline().strip().lower()
            if not line:
                break
            global_input_id += 1
            aligned_amr_str, tree_str = line.split('\t')
            # TODO: support both edge alignments and node alignments
            _, tree = ptbparse(tree_str)
            if not tree:
                print >> logs, 'tree parsing failure, discard'
                continue
            global_tree_node_id = -1
            #print 'b4 right bin', tree.pp()
            #tree.binarize('right')
            #tree.binarize('left')
            tree.assign_id()
            #print 'after assign_id, tree internal', tree.pp_internal()
            _, aligned_amr = input_amrparse(aligned_amr_str)
            if not aligned_amr:
                print >> logs, 'amr parsing failure, discard'
                continue
            aligned_amr.corefy(aligned_amr.get_nonterm_nodes())

            # purpose of assigning id:
            # 1. to provide a unique internal representation
            # of concepts and property values, cases:
            # (d / do :ARG1 (d2 / do) :mode imperative)
            # (n / name :op1 "Kramer" :op2 "vs." :op3 "Kramer")
            # 2. to speed up comparison (as apposed to string)
            #global_input_node_id = 0
            global_rule_node_id = -1
            aligned_amr.assign_id_rule()

            if aligned_amr.is_cyclic():
                print >> logs, 'cycle, discard'
                continue            

            if options.debug:
                print 'aligned_amr', aligned_amr.pp() 
                print 'aligned_amr indented', aligned_amr.pp_indented() 
                print 'aligned_amr internal', aligned_amr.pp_internal() 
                print 'tree internal', tree.pp_internal() 

            df = defaultdict(set)
            na_dict = defaultdict(set)
            #TODO: get a dict for all tree / amr, not just virtual ones??? if it is overall, use default dict, otherwise hash to a number and compare hash???
            global_vtree_dict = defaultdict()
            global_vamr_dict = defaultdict()
            get_node_align(aligned_amr, tree, na_dict)
            if options.debug:
                print '----------\nprint node_align_dict'
                for a in na_dict:
                    print '///////'
                    print 'amr', a
                    print 'tree', ' '.join(str(i) for i in na_dict[a])
                print '///////'
           
            top_dnode = derive_from_alignment(aligned_amr, tree, na_dict, df)

            print '# sent', global_input_id + 1
            #print 'q' + top_dnode.tree.node
            #TODO: yanggao20130916: keep only uniq rules from binarization, this is buggy because seemingly duplicate rules may come from different AMR nodes
            all_rules_raw = top_dnode.get_rules()
            #all_rules_final = list(i for i in all_rules_raw if ':rest' not in str(i)) + list(set(i for i in all_rules_raw if ':rest' in str(i))) 
            #print '\n'.join(str(i) + ' ## ' + i.comment for i in all_rules_final)
            print '\n'.join(str(i) for i in all_rules_raw)
            print 
        sys.exit() 


    default_rule_opts = []
    if options.default_rule.lower() != 'none':
        default_rule_opts = options.default_rule.split(',')

    f_grammar = open(args[0])
    
    #ygao20130228
    #f_forest = open(args[1], 'w')

    # read grammar
    # global_rule_node_id is assigned to constant FeatGraph nodes on lhs and rhs (in the case of restruct rule)
    # ignore variable nodes such as x0, x1, which will be replaced by input FeatGraph nodes anyway
    global_rule_node_id = -1
    sstate, all_rules = get_grammar( f_grammar.read().lower() )
    #if options.debug:
     #   print '\n---\ngrammar loaded in\n'
      #  print sstate
       # for state in all_rules:
        #    print '------------------'
         #   print state
          #  for rule in all_rules[state]:
           #     print rule
            #    print 'lhs internal', rule.lhs.pp_internal()

    global_input_id = -1
    while True:
        #TODO: lowercasing in wrapper sh, not here
        line = sys.stdin.readline().lower()
        if not line:
            break

        global_input_id += 1
        print >> logs, '\n======================\namr', global_input_id

        pos, input = input_amrparse(line)
        if not input:
            print >> logs, 'amr', global_input_id, 'parsing error, output blank line'
            print '[S] |||'+'\n'
            continue

        # proc_damr introduces new nodes & edges, do it before assign_id
        print >> logs, '\n---\ndamr preprocessing...'
        input.proc_damr()

        global_is_damr = input.is_damr()

        # perform simple resolution for long-distance
        # reentrancy, by changing referent to pronoun, etc. 
        # may introduce new pronoun concept, therefore
        # doing this before rule filtering
        print >> logs, '\n---\ncoref preprocessing...'
        input.corefy(input.get_nonterm_nodes())

        # purpose of assigning id:
        # 1. to provide a unique internal representation
        # of concepts and property values, cases:
        # (d / do :ARG1 (d2 / do) :mode imperative)
        # (n / name :op1 "Kramer" :op2 "vs." :op3 "Kramer")
        # 2. to speed up comparison (as apposed to string)
        global_input_node_id = 0
        input.assign_id()

        if input.is_cyclic():
            print >> logs, '\ncycle detected, output blank line'
            print '[S] |||'+'\n'
            continue

        ceo_count_dict = {}
        print >> logs, 'ceo count', get_ceo_count(input, ceo_count_dict)
        #simple_amrs = get_ceo(input)
        #simple_amrs = input.get_simple_amr_from_damr()
        #if len(simple_amrs) > 1:
         #   print >> logs, '\n---\namr', global_input_id, 'is disjunctive, encoding simple amr', len(simple_amrs), '\n'
        #TODO: may use up the memory
        #if options.ceo:
         #   for sa in simple_amrs: 
          #      print sa.pp()
                #print sa.pp_indented()
                #print sa.pp_internal()
            #continue

        # after corefy, ':arg0 i' will become ':arg0 (i / i)'
        print >> logs, '\n---\nafter preproc, input indented\n'
        print >> logs, input.pp_indented()
        print >> logs, '\ninput internal\n'
        print >> logs, input.pp_internal()

        # rules that vary with input: 1) filtered rules 2) green rules
        filtered_rules = get_filtered_rules(all_rules, input)
        _, green_rules = get_grammar('\n'.join(i.lower() for i in get_new_rules(input)) + '\n')

        if options.debug:
            print >> logs, '\n---\ngrammar filtered in\n'
            print >> logs, sstate
            for state in filtered_rules:
                print >> logs, '------------------'
                print >> logs, state
                for rule in filtered_rules[state]:
                    print >> logs, rule
                    #print 'lhs internal', rule.lhs.pp_internal()
                    #if type(rule.rhs) == FeatGraph:
                     #   print 'rhs internal', rule.rhs.pp_internal()

            print >> logs, '\n---\ngreen rules\n'
            for state in green_rules:
                print >> logs, '------------------'
                print >> logs, state
                for rule in green_rules[state]:
                    print >> logs, rule
                    #print 'lhs internal', rule.lhs.pp_internal()
                    #if type(rule.rhs) == FeatGraph:
                     #   print 'rhs internal', rule.rhs.pp_internal()
        # combine filtered rules and green rules
        combined_rules = merge_dict_set(filtered_rules, green_rules)

        df = defaultdict(set)

        top_dnode = DerivationNode(sstate, PartialSemRef(input))
        #print top_dnode

        derive(top_dnode, df, combined_rules)

        if False:
        #if options.debug:
            print '\n---\nprint df as dictionary\n'
            for psr in df:
                print '+++psr+++++++++++++++++\n', psr
                for dnode in df[psr]:
                    print '......dnode\n', dnode
                    print '\n'.join(str(j) for j in dnode.hpes)
                print

        #num_deriv = top_dnode.get_derivation_number()
        #print >> logs, '\n---\nnum derivations for amr', str(global_input_id) + ':' + str(num_deriv) + '\n'
        #if num_deriv == 0:
         #   print '[S] |||'+'\n'
          #  continue

        #output derivation forest
        print '[S] ||| ' + str(top_dnode)
        print '\n'.join( top_dnode.get_derivation_forest() )
        print    
  
        if options.debug:

            #kbest, global, map derivation node to kbest_items
            # format: kbest[dnode] = [kbest_item+]
            kbest = defaultdict(list)

            # cands, global, map derivation node to a min heap of
            # kbest_items
            cands = defaultdict()    

            out_trees = [kb_item.get_output_tree() for kb_item in get_kbest(options.k, top_dnode)]
            unique_trees = set(out_trees)   
            #out_strings = [kb_item.get_output_string() for kb_item in get_kbest(options.k, top_dnode)]
            #unique_strings = set(out_strings)

            print '\n---\nall trees: {0}\tunique trees: {1}\n'.format(len(out_trees), len(unique_trees))
            #print 'all strings: {0}\tunique strings: {1}\n'.format(len(out_strings), len(unique_strings))  
            print '\n'.join(out_trees)

            #if 'tree' in options.output and 'string' in options.output:
             #   print '\n\n'.join(t + '\n' + s for t, s in zip(out_trees, out_strings))
            #elif 'tree' in options.output:
             #   print '\n'.join(out_trees)
            #elif 'string' in options.output:            
             #   print '\n'.join(out_strings)
