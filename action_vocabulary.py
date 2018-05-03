"""A action vocabulary for a seq-2-act neural model."""
import collections
import numpy
import os
import sys
import theano
from theano.ifelse import ifelse
from theano import tensor as T


class ActionVocabulary:
    """A vocabulary of words, and their embeddings.

    By convention, the end-of-sentence token '</s>' is 0, and
    the unknown word token 'UNK' is 1.
    """
    END_OF_SENTENCE = '</s>'
    END_OF_SENTENCE_INDEX = 0
    UNKNOWN = 'add_unk:-:UNK'
    UNKNOWN_INDEX = 1
    NUM_SPECIAL_SYMBOLS = 2

    def __init__(self, action_list, entity_action_list, structure_emb_size, semantic_emb_size, float_type=numpy.float64,
                 unk_cutoff=0):
        """Create the action vocabulary.

        Args:
          action_list: List of actions that occurred in the database.
          emb_size: dimension of action embeddings
          float_type: numpy float type for theano
        """
        self.action_list = [self.UNKNOWN] + action_list
        self.entity_action_list = entity_action_list
        self.action_to_index = dict((x[1], x[0]) for x in enumerate(self.action_list + self.entity_action_list))
        self.structure_list = self.get_structure_list()
        self.structure_to_index = dict((x[1], x[0]) for x in enumerate(self.structure_list))
        self.semantic_list = self.get_semantic_list()
        self.semantic_to_index = dict((x[1], x[0]) for x in enumerate(self.semantic_list))

        self.structure_emb_size = structure_emb_size
        self.semantic_emb_size = semantic_emb_size
        self.emb_size = structure_emb_size + semantic_emb_size
        self.float_type = float_type

        # Embedding matrix
        init_val = 0.1 * numpy.random.uniform(-1.0, 1.0, (self.size(), self.emb_size)).astype(theano.config.floatX)

        init_structure_val = 0.1 * numpy.random.uniform(-1.0, 1.0, (self.structure_size(), \
                                            self.structure_emb_size)).astype(theano.config.floatX)

        init_semantic_val = 0.1 * numpy.random.uniform(-1.0, 1.0, (self.semantic_size(), \
                                            self.semantic_emb_size)).astype(theano.config.floatX)

        index_matrix_value = numpy.zeros((len(self.action_list+self.entity_action_list), 2)).astype(int)

        for ii in range(len(self.action_list+self.entity_action_list)):
            if ii < len(self.action_list):
                action = self.action_list[ii]
            else:
                action = self.entity_action_list[ii-len(self.action_list)]
            structure, semantic = self.unpack_action(action)
            structure_i = self.structure_to_index[structure]
            semantic_i = self.semantic_to_index[semantic]
            index_matrix_value[ii] = [structure_i, semantic_i]

        self.index_matrix = theano.shared(
            name='index_matrix',
            value=index_matrix_value,
        )

        self.semantic_emb_mat = theano.shared(
            name='semantic_emb_mat',
            value=init_semantic_val)

        self.structure_emb_mat = theano.shared(
            name='structure_emb_mat',
            value=init_structure_val)

        print('size of structure item: %d, size of semantic item %d' % (len(self.structure_list), len(self.semantic_list)))

    def get_action_list(self):
        return self.action_list + self.entity_action_list

    def get_entity_action_list(self):
        return self.entity_action_list

    def get_structure_list(self):
        ret = []
        ret_set = set()
        for action in self.action_list + self.entity_action_list:
            end = action.index(':-:')
            structure_item = action[:end]
            if structure_item not in ret_set:
                ret_set.add(structure_item)
                ret.append(structure_item)
        return ret


    def get_semantic_list(self):
        ret = []
        ret_set = set()
        for action in self.action_list + self.entity_action_list:
            start = action.index(':-:') + 3
            if ':_:' not in action:
                end = len(action)
            else:
                end = action.index(':_:')
            semantic_item = action[start:end]
            if semantic_item not in ret_set:
                ret_set.add(semantic_item)
                ret.append(semantic_item)
        return ret


    def structure_size(self):
        return len(self.structure_list)

    def semantic_size(self):
        return len(self.semantic_list)

    def get_theano_embedding(self, i):
        """Get theano embedding for given action index."""
        triple_index = self.index_matrix[i]
        structure_i = T.dot(triple_index, [1, 0]).sum()
        semantic_i = T.dot(triple_index, [0, 1]).sum()
        return T.concatenate([self.structure_emb_mat[structure_i], self.semantic_emb_mat[semantic_i]])

    def get_theano_params(self):
        """Get theano parameters to back-propagate through."""
        return [self.structure_emb_mat] + [self.semantic_emb_mat]

    def get_theano_all(self):
        """By default, same as self.get_theano_params()."""
        return self.get_theano_params() + [self.index_matrix]

    def get_index(self, action):
        if action.startswith('add_entity'):
            action = self.normalize_entity_action(action)
        if action in self.action_to_index:
            return self.action_to_index[action]
        else:
            print('action not in action_list + entity_list: ', action)
        return self.action_to_index[self.UNKNOWN]

    def get_action(self, i):
        if i < len(self.action_list):
            return self.action_list[i]
        else:
            return self.entity_action_list[i-len(self.action_list)]

    def action_seq_to_indices(self, action_seq):
        actions = action_seq.split(' ')
        indices = [self.get_index(action) for action in actions]
        return indices

    def indices_to_action_seq(self, indices):
        return ' '.join(self.get_action(i) for i in indices)

    def size(self):
        return len(self.action_list)

    def all_size(self):
        return len(self.action_list+self.entity_action_list)

    def unpack_action(self, action):
        index1 = action.index(':-:')
        structure = action[:index1]
        semantic = action[index1+3:]
        return structure, semantic

    def normalize_entity_action(self, entity_action):
        '''add_entity_node:-:mississippi:=:river'''
        if ':=:' in entity_action:
            split1 = entity_action.index(':-:')
            split2 = entity_action.index(':=:')
            part1 = entity_action[:split1]
            part3 = entity_action[split2+3:]
            ret_entity_action = part1 + ':-:' + part3
            return ret_entity_action
        elif ':_' in entity_action:
            split1 = entity_action.index(':-:')
            split2 = entity_action.index(':_')
            part1 = entity_action[:split1]
            part3 = entity_action[split2 + 1:]
            ret_entity_action = part1 + ':-:' + part3
            return ret_entity_action
        else:
            return entity_action


    def action_is_end(self, domain, i):
        if i >= self.all_size():
            return False
        action = self.get_action(i)
        if domain == 'geoquery':
            if action and action.startswith('return'):
                return True
            return False
        elif domain == 'atis':
            if action and action == 'end_action:-:end':
                return True
            return False
        return False

    @classmethod
    def normalize_entity_action_cls(cls, entity_action):
        #print('entity_action:', entity_action)
        if ':=:' in entity_action:
            split1 = entity_action.index(':-:')
            split2 = entity_action.index(':=:')
            part1 = entity_action[:split1]
            part3 = entity_action[split2 + 3:]
            ret_entity_action = part1 + ':-:' + part3
            return ret_entity_action
        elif ':_' in entity_action:
            split1 = entity_action.index(':-:')
            split2 = entity_action.index(':_')
            part1 = entity_action[:split1]
            part3 = entity_action[split2 + 1:]
            ret_entity_action = part1 + ':-:' + part3
            return ret_entity_action
        else:
            return entity_action

    @classmethod
    def from_sentences(cls, sentences, structure_emb_size, semantic_emb_size, unk_cutoff=0, **kwargs):
        """Get list of all words used in a list of sentences.

                  Args:
                    sentences: list of sentences
                    emb_size: size of embedding
                    unk_cutoff: Treat words with <= this many occurrences as UNK.
                """
        action_list = []
        entity_list = []
        entity_set = set()
        counts = collections.Counter()
        for s in sentences:
            counts.update(s.split(' '))
        for a in counts:
            if counts[a] > unk_cutoff:
                if a.startswith('add_entity'):
                    normalized_a = cls.normalize_entity_action_cls(a)
                    if normalized_a not in entity_set:
                        entity_set.add(normalized_a)
                        entity_list.append(normalized_a)
                else:
                    action_list.append(a)
        print('Extracted action vocabulary of size %d, entity vocabulary of size %d' % (len(action_list), len(entity_list)))
        return cls(action_list, entity_list, structure_emb_size, semantic_emb_size, **kwargs)

    @classmethod
    def from_databases_for_atis(cls, databases):
        action_list = []
        entity_list = []
        number_list = ['$0', '$1', '$2', '$3']
        character_list = ['$A', '$B', '$C', '$D', '$E', '$F', '$G', '$H', '$I', '$J']
        entity_name_list = []
        normalized_entity_set = set()
        binary_list = []
        for base in databases:
            if base.startswith('entity:'):
                entity = base[7:].strip()
                if entity not in entity_name_list:
                    entity_name_list.append(entity)
            elif base.startswith('unary:'):
                unary = base[6:].strip()
                action = 'add_type_node:-:' + unary
                if action not in action_list:
                    action_list.append(action)
            elif base.startswith('binary'):
                parts = base.split('\t')
                binary = parts[2]
                action = 'add_edge:-:' + binary
                if action not in action_list:
                    action_list.append(action)

        for character in character_list:
            action = 'ope_for:-:' + character
            action_list.append(action)
            action = 'ope_return:-:' + character
            action_list.append(action)
            action = 'return:-:' + character
            action_list.append(action)
            action = 'arg_node:-:' + character
            action_list.append(action)
            action = 'add_node:-:' + character
            action_list.append(action)
            action = 'ope_arg:-:' + character
            action_list.append(action)

        for number in number_list:
            action = 'ope_for:-:' + number
            action_list.append(action)
            action = 'ope_return:-:' + number
            action_list.append(action)
            action = 'return:-:' + number
            action_list.append(action)
            action = 'arg_node:-:' + number
            action_list.append(action)
            action = 'add_node:-:' + number
            action_list.append(action)
            action = 'ope_arg:-:' + number
            action_list.append(action)

        for entity in entity_name_list:
            entity_action = 'add_entity_node:-:ent:_' + entity
            entity_action_i = cls.normalize_entity_action_cls(entity_action)
            if entity_action_i not in normalized_entity_set:
                normalized_entity_set.add(entity_action_i)
                entity_list.append(entity_action_i)

        fun_list = ['_max', '_min', '_argmin', '_argmax', '_count', '_sum', '_not', '_and', '_not', '_exists', \
                    '_equals', '_equals:_t', '_the', '_=', '_>', '_<', '_or']
        for fun in fun_list:
            action = 'add_operation:-:' + fun
            action_list.append(action)
            action = 'end_operation:-:' + fun
            action_list.append(action)

        action = 'end_action:-:end'
        action_list.append(action)

        return action_list, entity_list

    @classmethod
    def from_databases_for_geo(cls, databases):
        action_list = []
        entity_list = []
        entity_set = set()
        normalized_entity_set = set()
        character_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for base in databases:
            if base.startswith('schema:'):
                base = base[7:].strip()
                parts = base.split('\t')
                if len(parts) == 2:
                    cat = parts[0][4:]
                    action = 'add_type_node:-:_' + cat
                    if action not in action_list:
                        action_list.append(action)
                elif len(parts) == 3:
                    rel = parts[1][4:]
                    action = 'add_edge:-:_' + rel
                    if action not in action_list:
                        action_list.append(action)

            elif base.startswith('entity:'):
                base = base[7:].strip()
                parts = base.split('\t')
                split_i = parts[1].index(':')
                name_type = parts[1][:split_i - 2]
                name = parts[1][split_i + 1:]
                entity_action = 'add_entity_node:-:' + name + ':=:' + name_type
                if entity_action not in entity_set:
                    entity_set.add(entity_action)

            elif base.startswith('entity_type:'):
                base = base[12:].strip()
                parts = base.split('\t')
                entity_type = parts[1][5:]
                action = 'add_type_node:-:_' + entity_type
                if action not in action_list:
                    action_list.append(action)

            elif base.startswith('entity_rel:'):
                base = base[11:].strip()
                parts = base.split('\t')
                rel = parts[1][4:]
                action = 'add_edge:-:_' + rel
                if action not in action_list:
                    action_list.append(action)
            else:
                pass

        action = 'add_type_node:-:_population'
        if action not in action_list:
            action_list.append(action)
        action = 'add_type_node:-:_elevation'
        if action not in action_list:
            action_list.append(action)
        action = 'add_type_node:-:_area'
        if action not in action_list:
            action_list.append(action)
        action = 'add_type_node:-:_len'
        if action not in action_list:
            action_list.append(action)

        for entity_action in entity_set:
            entity_action_i = cls.normalize_entity_action_cls(entity_action)
            if entity_action_i not in normalized_entity_set:
                normalized_entity_set.add(entity_action_i)
                entity_list.append(entity_action_i)

        ope_fun_list = ['_highest', '_longest', '_shortest', '_lowest', '_largest', '_smallest', '_fewest', '_most']
        for ope_fun in ope_fun_list:
            action = 'add_operation:-:' + ope_fun
            action_list.append(action)
        other_ope_fun_list = ['_not', '_sum', '_count']
        action = 'end_operation:-:arg'
        action_list.append(action)
        action = 'end_operation:-:arg_count'
        action_list.append(action)
        for other_ope_fun in other_ope_fun_list:
            action = 'add_operation:-:' + other_ope_fun
            action_list.append(action)
            action = 'end_operation:-:' + other_ope_fun
            action_list.append(action)

        for character in character_list:
            action = 'return:-:' + character
            action_list.append(action)
            action = 'add_node:-:' + character
            action_list.append(action)

        action_list.append('ope_in:-:_len')
        action_list.append('ope_in:-:_population')
        action_list.append('ope_in:-:_area')
        action_list.append('ope_in:-:_elevation')

        for character in character_list:
            action = 'ope_for:-:' + character
            action_list.append(action)
            action = 'ope_return:-:' + character
            action_list.append(action)
            action = 'arg_node:-:' + character
            action_list.append(action)

        return action_list, entity_list

    @classmethod
    def from_databases(cls, domain, databases, structure_emb_size, semantic_emb_size, **kwargs):

        print('load action vocabulary from databases for domain = ', domain)
        action_list = []
        entity_list = []
        if domain == 'geoquery':
            action_list, entity_list = cls.from_databases_for_geo(databases)
        elif domain =='atis':
            action_list, entity_list = cls.from_databases_for_atis(databases)
        print('Extracted action vocab of size %d, entity vocab of size %d' % (
        len(action_list), len(entity_list)))
        return cls(action_list, entity_list, structure_emb_size, semantic_emb_size, **kwargs)

