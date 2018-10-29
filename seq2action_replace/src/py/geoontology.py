import os

from ontology import Ontology

from ontology import Ontology

class GeoOntology(Ontology):

    def read_grammars(self, grammar_file):
        grammars = {}
        grammars['cat'] = {}
        grammars['rel'] = {}
        with open(grammar_file) as f:
            for line in f:
                if line.startswith('schema:'):
                    line = line[7:].strip()
                    parts = line.split('\t')
                    if len(parts) == 2:
                        cat = parts[0][4:]
                        type0 = parts[1][5:]
                        if cat not in grammars['cat']:
                            grammars['cat'][cat] = []
                        if type0 not in grammars['cat'][cat]:
                            grammars['cat'][cat].append(type0)
                    elif len(parts) == 3:
                        rel = parts[1][4:]
                        type1 = parts[0][5:]
                        type2 = parts[2][5:]
                        if rel not in grammars['rel']:
                            grammars['rel'][rel] = []
                        if (type1, type2) not in grammars['rel'][rel]:
                            grammars['rel'][rel].append((type1, type2))
        return grammars

    def is_legal_action_then_read(self, pre_action_class, pre_arg_list, action_token, pre_action, node_dict, type_node_dict,
                                  entity_node_dict, operation_dict, edge_dict, return_node, db_triple, fun_trace_list, for_controller=True):

        return True,

    def is_legal_action(self, pre_action_class, pre_arg_list, action_token, pre_action, node_dict, type_node_dict,
                        entity_node_dict, operation_dict, edge_dict, return_node, db_triple, fun_trace_list, for_controller=True, entity_lex_map={}):
        if for_controller and not self.use_ontology:
            return True
        if action_token == None or action_token == '' or action_token == '<COPY>':
            return False
        if action_token.startswith('add_unk'):
            return False

        print('entity_lex in is_legal_action = %s' % entity_lex_map)
        if action_token.startswith('add_entity_node'):
            entity = action_token[action_token.index(':-:')+3:]
            #print('entity = %s' % entity)
            if entity not in entity_lex_map:
                entity_flag = False
                for entity_key in entity_lex_map:
                    entity_value = entity_lex_map[entity_key]
                    if entity == entity_value:
                        entity_flag = True
                        break
                if not entity_flag:
                    return False


        if pre_action_class == 'inner_start':
            type_for_node_map = {}

            for node in node_dict:
                type_for_node_map[node] = []

            for type_edge in type_node_dict:
                if ':_:' not in type_edge:
                    continue
                if not type_edge.startswith('TYPE_'):
                    return False
                type_value = type_edge[5:type_edge.index(':_:')]
                if 'arg' not in type_node_dict[type_edge]:
                    return False
                arg = type_node_dict[type_edge]['arg'][0]
                if arg not in type_for_node_map:
                    return False
                if type_value in type_for_node_map[arg]:
                    continue
                if type_value == 'elevation' or type_value == 'len' or \
                                type_value == 'population' or type_value == 'area':
                    continue
                type_for_node_map[arg].append(type_value)

            for entity in entity_node_dict:
                if not ':=:' in entity:
                    continue
                entity_type = entity[entity.index(':=:')+3:]
                if 'arg1' not in entity_node_dict[entity]:
                    return False
                arg = entity_node_dict[entity]['arg1']
                if arg not in type_for_node_map:
                    return False
                if entity_type not in type_for_node_map[arg]:
                    type_for_node_map[arg].append(entity_type)

            #print('type_for_node_map: ', type_for_node_map)

            for node in type_for_node_map:
                type_size = len(type_for_node_map[node])
                if type_size < 2:
                    continue
                for ii in range(type_size-1):
                    for jj in range(ii+1, type_size):
                        type1 = type_for_node_map[node][ii]
                        type2 = type_for_node_map[node][jj]
                        #print('type1: ', type1)
                        #print('type2: ', type2)
                        if type1 in self.grammars['cat'] and type2 in self.grammars['cat']:
                            conjoin = set(self.grammars['cat'][type1]) & set(self.grammars['cat'][type2])
                            if len(conjoin) == 0:
                                return False
                        elif type1 in self.grammars['cat']:
                            if type2 not in self.grammars['cat'][type1]:
                                return False
                        elif type2 in self.grammars['cat']:
                            if type1 not in self.grammars['cat'][type2]:
                                return False
                        else:
                            return False

            for edge in edge_dict:
                if ':_:' not in edge:
                    continue
                if 'arg1' not in edge_dict[edge]:
                    return False
                if 'arg2' not in edge_dict[edge]:
                    return False
                arg1 = edge_dict[edge]['arg1'][0]
                arg2 = edge_dict[edge]['arg2'][0]

                if arg1 not in type_for_node_map:
                    return False
                if arg2 not in type_for_node_map:
                    return False

                basic_type_1 = self.get_basic_type_for_node(type_for_node_map, arg1)
                basic_type_2 = self.get_basic_type_for_node(type_for_node_map, arg2)
                edge = edge[1:edge.index(':_:')]

                #print('edge: ', edge)
                #print('basic_type_1: ', basic_type_1)
                #print('basic_type_2: ', basic_type_2)

                if basic_type_1 == '' or basic_type_2 == '':
                    continue
                if edge not in self.grammars['rel']:
                    return False
                if (basic_type_1, basic_type_2) not in self.grammars['rel'][edge]:
                    return False
        return True

    def get_basic_type_for_node(self, type_for_node_map, node):
        if node not in type_for_node_map or len(type_for_node_map[node])==0:
            return ''
        for type_value in type_for_node_map[node]:
            if type_value not in self.grammars['cat']:
                return type_value
            elif len(self.grammars['cat'][type_value]) == 1:
                return self.grammars['cat'][type_value][0]
            elif len(type_for_node_map[node]) > 1:
                continue
            elif len(self.grammars['cat'][type_value]) > 1:
                return ''
            else:
                return type_value
        return ''

    def get_legal_action_list(self, pre_action_class, pre_arg_list, pre_action, node_dict, type_node_dict, entity_node_dict,
                              operation_dict, edge_dict, return_node, db_triple, fun_trace_list, action_all, for_controller=True, entity_lex_map={}):
        legal_action_list = []
        for action_token in action_all:
            legal_flag = self.is_legal_action(pre_action_class, pre_arg_list, action_token, pre_action, node_dict, type_node_dict,
                                              entity_node_dict, operation_dict, edge_dict, return_node, db_triple, fun_trace_list, entity_lex_map=entity_lex_map)
            if legal_flag:
                legal_action_list.append(True)
            else:
                legal_action_list.append(False)
        return legal_action_list