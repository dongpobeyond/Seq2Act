import os

from ontology import Ontology
import copy

class GeneralOntology(Ontology):

    def read_grammars(self, grammar_file):
        grammars = {}
        with open(grammar_file) as f:
            for line in f:
                if line.startswith('G::'):
                    parts = line[len('G::	'):].strip().split('\t')
                    if not len(parts) == 3:
                        print('illegal grammar: ' + line.strip())
                        continue
                    action_name = parts[0]
                    arg_list = []
                    arg_count_list = []
                    arg_count_parts = parts[1].split(' + ')
                    for arg_count in arg_count_parts:
                        arg_count_list.append(arg_count)

                    arg_parts = parts[2].split(' + ')
                    for arg_part in arg_parts:
                        arg_part_parts = arg_part.split(' | ')
                        arg_item_set = set()
                        for arg_part_part in arg_part_parts:
                            arg_item_set.add(arg_part_part)
                        arg_list.append(arg_item_set)

                    if len(arg_list) != len(arg_count_list):
                        print('illegal grammar: ' + line.strip())
                        continue
                    grammars[action_name] = (arg_count_list, arg_list)

        return grammars

    def is_connected(self, pre_action_class, pre_arg_list, pre_action, action_token, node_dict_in_con, type_node_dict_in_con, \
                     entity_node_dict_in_con, operation_dict_in_con, edge_dict_in_con, return_node_in_con, db_triple_in_con):
        #print('pre_action: ', pre_action)
        #print('pre_action_class: ', pre_action_class)
        #print('pre_arg_list: ', pre_arg_list)
        action_key = pre_action[pre_action.index(':-:')+3:]
        #print('action_key: ', action_key)
        #print('action_token: ', action_token)
        #print('*****************************')
        if 'type_node' == pre_action_class:
            action_key = 'TYPE' + action_key
            action_key = type_node_dict_in_con[action_key]['stack'][-1]
            #print(pre_action_class, action_key, type_node_dict_in_con[action_key])
            if action_key not in type_node_dict_in_con:
                return False
            if 'arg' not in type_node_dict_in_con[action_key] or \
                    not len(type_node_dict_in_con[action_key]['arg']) == 1:
                return False
            node = type_node_dict_in_con[action_key]['arg'][0]
            if not node in node_dict_in_con:
                return False
            db_triple_in_con[action_key] = {}
            db_triple_in_con[action_key]['arg'] = node

        elif 'edge' == pre_action_class:
            action_key = edge_dict_in_con[action_key]['stack'][-1]
            #print(pre_action_class, action_key, edge_dict_in_con[action_key])
            if action_key not in edge_dict_in_con:
                return False
            if 'arg_count' not in edge_dict_in_con[action_key] or \
                not edge_dict_in_con[action_key]['arg_count'] == 2:
                return False
            if 'arg1' not in edge_dict_in_con[action_key] or 'arg2' not in edge_dict_in_con[action_key] or \
                not len(edge_dict_in_con[action_key]['arg1']) == 1 or not len(edge_dict_in_con[action_key]['arg2']) == 1:
                return False
            node_in = edge_dict_in_con[action_key]['arg1'][0]
            node_out = edge_dict_in_con[action_key]['arg2'][0]
            if not node_in in node_dict_in_con:
                    return False
            if not node_out in node_dict_in_con :
                    return False
            if node_out == node_in:
                return False
            db_triple_in_con[action_key] = {}
            db_triple_in_con[action_key]['arg1'] = node_in
            db_triple_in_con[action_key]['arg2'] = node_out

        elif 'entity_node' == pre_action_class:
            #print(pre_action_class, action_key, entity_node_dict_in_con[action_key])
            if action_key not in entity_node_dict_in_con:
                return False
            if 'arg1' not in entity_node_dict_in_con[action_key] or 'arg2' not in entity_node_dict_in_con[action_key]:
                return False
            if entity_node_dict_in_con[action_key]['arg1'] not in node_dict_in_con:
                return False
            node = entity_node_dict_in_con[action_key]['arg1']
            edge = entity_node_dict_in_con[action_key]['arg2']
            db_triple_in_con[edge] = {}
            db_triple_in_con[edge]['arg1'] = node
            db_triple_in_con[edge]['arg2'] = action_key

        elif 'end_operation_not' == pre_action_class:
            #print(pre_action_class, action_key, operation_dict_in_con[action_key])
            action_key = operation_dict_in_con['end'][action_key]['stack'][-1]
            action_key = operation_dict_in_con['end'][action_key]
            if action_key not in operation_dict_in_con['core']:
                return False
            if 'arg_count' not in operation_dict_in_con['core'][action_key] or \
                not operation_dict_in_con['core'][action_key]['arg_count'] == 1:
                return False
            if 'arg0' not in operation_dict_in_con['core'][action_key]:
                return False

        elif 'end_operation_count' == pre_action_class:
            #print(pre_action_class, action_key, operation_dict_in_con[action_key])
            action_key = operation_dict_in_con['end'][action_key]['stack'][-1]
            if action_key not in operation_dict_in_con['core']:
                return False
            if 'arg_count' not in operation_dict_in_con['core'][action_key] or \
                not operation_dict_in_con['core'][action_key]['arg_count'] == 2:
                return False
            if 'arg1' not in operation_dict_in_con['core'][action_key] or not len(operation_dict_in_con['core'][action_key]['arg1']) == 1 or \
                 'arg2' not in operation_dict_in_con['core'][action_key] or not len(operation_dict_in_con['core'][action_key]['arg2']) == 1:
                return False
            ope_for = operation_dict_in_con['core'][action_key]['arg1'][0]
            ope_return = operation_dict_in_con['core'][action_key]['arg2'][0]
            if ope_for not in node_dict_in_con:
                return False
            if ope_return in node_dict_in_con:
                return False
            if 'ope_return_set' not in return_node_in_con:
                return_node_in_con['ope_return_set'] = set()
            if ope_return not in return_node_in_con['ope_return_set']:
                return_node_in_con['ope_return_set'].add(ope_return)

        elif 'end_operation_arg_count' == pre_action_class:
            #print(pre_action_class, action_key, operation_dict_in_con[action_key])
            action_key = operation_dict_in_con['end'][action_key]['stack'][-1]
            action_key = operation_dict_in_con['end'][action_key]
            if action_key not in operation_dict_in_con['core']:
                return False
            if 'arg_count' not in operation_dict_in_con['core'][action_key] or \
                not operation_dict_in_con['core'][action_key]['arg_count'] == 2:
                return False
            if 'arg1' not in operation_dict_in_con['core'][action_key] or not len(operation_dict_in_con['core'][action_key]['arg1']) == 1 or \
                 'arg2' not in operation_dict_in_con['core'][action_key] or not len(operation_dict_in_con['core'][action_key]['arg2']) == 1:
                return False
            ope_for_1 = operation_dict_in_con['core'][action_key]['arg1'][0]
            if ope_for_1 not in node_dict_in_con:
                return False
            ope_for_2 = operation_dict_in_con['core'][action_key]['arg2'][0]
            if ope_for_2 not in node_dict_in_con:
                return False

        elif 'end_operation_arg' == pre_action_class:
            #print(pre_action_class, action_key, operation_dict_in_con[action_key])
            action_key = operation_dict_in_con['end'][action_key]['stack'][-1]
            action_key = operation_dict_in_con['end'][action_key]
            if action_key not in operation_dict_in_con['core']:
                return False
            if 'arg_count' not in operation_dict_in_con['core'][action_key] or \
                not operation_dict_in_con['core'][action_key]['arg_count'] == 1:
                return False
            if 'arg1' not in operation_dict_in_con['core'][action_key] or not len(operation_dict_in_con['core'][action_key]['arg1']) == 1:
                return False
            ope_for = operation_dict_in_con['core'][action_key]['arg1'][0]
            if ope_for not in node_dict_in_con:
                return False

        elif 'end_operation_sum' == pre_action_class:
            #print(pre_action_class, action_key, operation_dict_in_con[action_key])
            action_key = operation_dict_in_con['end'][action_key]['stack'][-1]
            if action_key not in operation_dict_in_con['core']:
                return False
            if 'arg_count' not in operation_dict_in_con['core'][action_key] or \
                not operation_dict_in_con['core'][action_key]['arg_count'] == 3:
                return False
            if 'arg1' not in operation_dict_in_con['core'][action_key] or not len(operation_dict_in_con['core'][action_key]['arg1']) == 1 or \
                 'arg2' not in operation_dict_in_con['core'][action_key] or not len(operation_dict_in_con['core'][action_key]['arg2']) == 1 or \
                    'arg3' not in operation_dict_in_con['core'][action_key] or not len(operation_dict_in_con['core'][action_key]['arg3']) == 1:
                return False
            ope_for = operation_dict_in_con['core'][action_key]['arg1'][0]
            ope_return = operation_dict_in_con['core'][action_key]['arg3'][0]
            if ope_for not in node_dict_in_con:
                return False
            if ope_return in node_dict_in_con:
                return False
            if 'ope_return_set' not in return_node_in_con:
                return_node_in_con['ope_return_set'] = set()
            if ope_return not in return_node_in_con['ope_return_set']:
                return_node_in_con['ope_return_set'].add(ope_return)
        elif 'inner_start' == pre_action_class:
            pass
        else:
            #print('pre_action_class: ', pre_action_class)
            print('TODO for connection function in generalontology!')
            return False
        return True

    def is_legal_action(self, pre_action_class, pre_arg_list, action_token, pre_action, node_dict,
                        type_node_dict, entity_node_dict, operation_dict, edge_dict, return_node,
                        db_triple, fun_trace_list, for_controller=True, entity_lex_map={}):
        #print('**************', action_token, '**************')
        if for_controller and not self.use_ontology:
            return True
        if pre_action_class not in self.grammars:
            #print('pre_action_class not in grammar: '+ pre_action_class)
            return False
        if action_token == None or action_token == '' or action_token == '<COPY>':
            return False
        if action_token.startswith('add_unk'):
            return False

        action_type = action_token[:action_token.index(':-:')]
        action_fake = action_token.replace(':-:', '_')
        arg_count_list, arg_list = self.grammars[pre_action_class]
        arg_index = 0
        arg_len = len(arg_list)
        for pre_arg in pre_arg_list:
            arg_count = arg_count_list[arg_index]
            if arg_count == '1':
                arg_index += 1

        #print('arg_index: ', arg_index)
        #print('arg_len: ', arg_len)

        if arg_index < arg_len and action_type not in arg_list[arg_index]:
            #print('false 1: ', arg_index, arg_len, action_token, action_type, arg_list[arg_index], pre_action_class, pre_arg_list)
            return False

        if arg_index < arg_len and action_type in arg_list[arg_index]:
            #print('pre_action_class: ', pre_action_class, '  action_type: ', action_type)
            check_flag = self.check_before_update(pre_action_class, pre_action, action_token, arg_index, node_dict,
                                                  edge_dict, type_node_dict, entity_node_dict, operation_dict, return_node, db_triple)
            if not check_flag:
                return False

        #print('pre_action_class 1 : ' + pre_action_class, pre_arg_list, arg_index, arg_len)
        pre_arg_list_temp_in_gen = self.update_pre_arg_list(pre_arg_list, action_token)
        pre_action_class_temp = pre_action_class

        node_dict_temp_in_gen = copy.deepcopy(node_dict)
        type_node_dict_temp_in_gen = copy.deepcopy(type_node_dict)
        entity_node_dict_temp_in_gen = copy.deepcopy(entity_node_dict)
        operation_dict_temp_in_gen = copy.deepcopy(operation_dict)
        edge_dict_temp_in_gen = copy.deepcopy(edge_dict)
        return_node_temp_in_gen = copy.deepcopy(return_node)
        db_triple_temp_in_gen = copy.deepcopy(db_triple)


        #print('update connection info in test!')
        self.update_connection_info(pre_action_class, pre_action, action_token, arg_index, node_dict_temp_in_gen,
                                        type_node_dict_temp_in_gen, entity_node_dict_temp_in_gen, operation_dict_temp_in_gen,
                                    edge_dict_temp_in_gen, return_node_temp_in_gen)


        if (not pre_action_class == 'start') and arg_index == arg_len-1:
            #print('action_fake', action_fake)
            connection_flag = self.is_connected(pre_action_class, pre_arg_list_temp_in_gen, pre_action, action_token, node_dict_temp_in_gen,
                                                type_node_dict_temp_in_gen, entity_node_dict_temp_in_gen, operation_dict_temp_in_gen, edge_dict_temp_in_gen,
                                                return_node_temp_in_gen, db_triple_temp_in_gen)
            if not connection_flag:
                #print('is not connected in test!')
                return False
            pre_action_class_temp = 'inner_start'

        if pre_action_class == 'start' or pre_action_class_temp == 'inner_start':
            if action_token.startswith('return'):
                node = action_token[action_token.index(':-:')+3:]
                if node not in node_dict:
                    if 'ope_return_set' not in return_node_temp_in_gen:
                        return False
                    elif node not in return_node_temp_in_gen['ope_return_set']:
                        return False
        return True

    def is_legal_action_then_read(self, pre_action_class, pre_arg_list, action_token, pre_action, node_dict,
                                  type_node_dict, entity_node_dict, operation_dict, edge_dict, return_node,
                                  db_triple, fun_trace_list, for_controller=True):
        #print('**************', action_token, '**************')
        #print('pre_action_class: ', pre_action_class)
        if for_controller and not self.use_ontology:
            return True, pre_action_class, pre_arg_list, pre_action, fun_trace_list
        if pre_action_class not in self.grammars:
            #print('pre_action_class not in grammar: '+ pre_action_class)
            return False, pre_action_class, pre_arg_list, pre_action, fun_trace_list

        if action_token == None or action_token == '' or action_token == '<COPY>':
            return False, pre_action_class, pre_arg_list, pre_action, fun_trace_list

        if action_token.startswith('add_unk'):
            return False, pre_action_class, pre_arg_list, pre_action, fun_trace_list

        action_type = action_token[:action_token.index(':-:')]
        action_fake = action_token.replace(':-:', '_')
        arg_count_list, arg_list = self.grammars[pre_action_class]
        arg_index = 0
        arg_len = len(arg_list)
        for pre_arg in pre_arg_list:
            arg_count = arg_count_list[arg_index]
            if arg_count == '1':
                arg_index += 1

        #print('arg_index: ', arg_index)
        #print('arg_len: ', arg_len)

        if arg_index < arg_len and action_type not in arg_list[arg_index]:
            #print('false 1: ', arg_index, arg_len, action_token, action_type, arg_list[arg_index], pre_action_class, pre_arg_list)
            return False, pre_action_class, pre_arg_list, pre_action, fun_trace_list

        if arg_index < arg_len and action_type in arg_list[arg_index]:
            #print('in check 1!!!!')
            check_flag = self.check_before_update(pre_action_class, pre_action, action_token, arg_index, node_dict,
                                                  edge_dict, type_node_dict, entity_node_dict, operation_dict, return_node, db_triple)
            if not check_flag:
                #print('check before update return False!')
                return False, pre_action_class, pre_arg_list, pre_action, fun_trace_list

        #print('pre_action_class 1 : ' + pre_action_class, pre_arg_list, arg_index, arg_len)
        pre_arg_list = self.update_pre_arg_list(pre_arg_list, action_token)
        #print('update connection info in read!')
        self.update_connection_info(pre_action_class, pre_action, action_token, arg_index, node_dict,
                                        type_node_dict, entity_node_dict, operation_dict, edge_dict, return_node)

        if (not pre_action_class == 'start') and arg_index == arg_len-1:
            #print('will check is_connected!!!')
            connection_flag = self.is_connected(pre_action_class, pre_arg_list, pre_action, action_token, node_dict,
                                                type_node_dict, entity_node_dict, operation_dict, edge_dict, return_node, db_triple)
            if not connection_flag:
                print('in read, is not connected!')
                return False, pre_action_class, pre_arg_list, pre_action, fun_trace_list
            pre_action_class = 'inner_start'
            pre_arg_list = []

        if pre_action_class == 'start' or pre_action_class == 'inner_start':
            if action_token.startswith('add') or action_token.startswith('return') or action_token.startswith('end'):
                #print('update pre action class and fun trace list.')
                pre_action_class, pre_action, fun_trace_list = self.update_pre_action_class(pre_action_class, pre_action,
                                action_token, node_dict, type_node_dict, entity_node_dict,
                                 operation_dict, edge_dict, return_node, db_triple, fun_trace_list)
                pre_arg_list = []
            if action_token.startswith('return'):
                if len(return_node) == 0 or 'node' not in return_node:
                    if return_node['node'] not in node_dict:
                        if 'ope_return_set' not in return_node:
                            return False, pre_action_class, pre_arg_list, pre_action, fun_trace_list
                        elif return_node['node'] not in return_node['ope_return_set']:
                            return False, pre_action_class, pre_arg_list, pre_action, fun_trace_list

        #print('pre_arg_list', pre_arg_list)
        return True, pre_action_class, pre_arg_list, pre_action, fun_trace_list

    def final_check(self, node_dict, type_node_dict, entity_node_dict, operation_dict, edge_dict, return_node, db_triple):
        for triple_key in db_triple:
            if triple_key.startswith('TYPE'):
                if 'arg' not in db_triple[triple_key]:
                    return False
                if db_triple[triple_key]['arg'] not in node_dict:
                    return False
            elif triple_key.startswith('_const'):
                if 'arg1' not in db_triple[triple_key] or 'arg2' not in db_triple[triple_key]:
                    return False
                if db_triple[triple_key]['arg1'] not in node_dict:
                    return False
                if db_triple[triple_key]['arg2'] not in entity_node_dict:
                    return False
            else:
                if 'arg1' not in db_triple[triple_key] or 'arg2' not in db_triple[triple_key]:
                    return False
                if db_triple[triple_key]['arg1'] not in node_dict:
                    return False
                if db_triple[triple_key]['arg2'] not in node_dict:
                    return False
        if 'core' in operation_dict:
            for operation_key in operation_dict['core']:
                #print('operation_key: ', operation_key)
                #print('operaton_map: ', operation_dict['core'][operation_key])
                if operation_key in operation_dict['add'] and operation_dict['add'][operation_key].startswith('arg_count'):
                    if 'arg_count' not in operation_dict['core'][operation_key] or \
                        'arg1' not in operation_dict['core'][operation_key] or 'arg2' not in operation_dict['core'][operation_key] or \
                                    'arg0' not in operation_dict['core'][operation_key]:
                        return False
                    if not operation_dict['core'][operation_key]['arg_count'] == 2 or not len(operation_dict['core'][operation_key]['arg1']) == 1 or \
                            operation_dict['core'][operation_key]['arg1'][0] not in node_dict:
                        return False
                    if not len(operation_dict['core'][operation_key]['arg2']) == 1 or not len(operation_dict['core'][operation_key]['arg2']) == 1 or \
                            operation_dict['core'][operation_key]['arg2'][0] not in node_dict:
                        return False
                elif operation_key in operation_dict['add'] and operation_dict['add'][operation_key].startswith('arg'):
                    if 'arg_count' not in operation_dict['core'][operation_key] or \
                        'arg1' not in operation_dict['core'][operation_key] or 'arg0' not in operation_dict['core'][operation_key]:
                        return False
                    if not operation_dict['core'][operation_key]['arg_count'] == 1 or not len(operation_dict['core'][operation_key]['arg1']) == 1 or \
                            operation_dict['core'][operation_key]['arg1'][0] not in node_dict:
                        return False
                elif operation_key.startswith('_count'):
                    if 'arg_count' not in operation_dict['core'][operation_key] or \
                        'arg1' not in operation_dict['core'][operation_key] or 'arg2' not in operation_dict['core'][operation_key] or \
                                    'arg0' not in operation_dict['core'][operation_key]:
                        return False
                    if not operation_dict['core'][operation_key]['arg_count'] == 2 or not len(operation_dict['core'][operation_key]['arg1']) == 1 or \
                            operation_dict['core'][operation_key]['arg1'][0] not in node_dict:
                        return False
                    if not len(operation_dict['core'][operation_key]['arg2']) == 1 or 'ope_return_set' not in return_node or \
                            operation_dict['core'][operation_key]['arg2'][0] not in return_node['ope_return_set']:
                        return False
                elif operation_key.startswith('_sum'):
                    if 'arg_count' not in operation_dict['core'][operation_key] or \
                        'arg1' not in operation_dict['core'][operation_key] or 'arg2' not in operation_dict['core'][operation_key] or \
                        'arg3' not in operation_dict['core'][operation_key] or 'arg0' not in operation_dict['core'][operation_key]:
                        return False
                    if not operation_dict['core'][operation_key]['arg_count'] == 3 or not len(operation_dict['core'][operation_key]['arg1']) == 1 or \
                            operation_dict['core'][operation_key]['arg1'][0] not in node_dict:
                        return False
                    if not len(operation_dict['core'][operation_key]['arg3']) == 1 or 'ope_return_set' not in return_node or \
                            operation_dict['core'][operation_key]['arg3'][0] not in return_node['ope_return_set']:
                        return False
                elif operation_key.startswith('_not'):
                    if 'arg0' not in operation_dict['core'][operation_key]:
                        return False
                else:
                    return False
        return True

    def get_legal_action_list(self, pre_action_class, pre_arg_list, pre_action, node_dict, type_node_dict, entity_node_dict,
                              operation_dict, edge_dict, return_node, db_triple, fun_trace_list, action_all, for_controller=True, entity_lex_map={}):
        legal_action_list = []
        for action_token in action_all:
            legal_flag = self.is_legal_action(pre_action_class, pre_arg_list, action_token, pre_action, node_dict,
                                              type_node_dict, entity_node_dict, operation_dict, edge_dict, return_node, db_triple, fun_trace_list, for_controller)
            if legal_flag:
                legal_action_list.append(True)
            else:
                legal_action_list.append(False)
        return legal_action_list

    def update_pre_action_class(self, pre_action_class, pre_action, action_token, node_dict, type_node_dict, entity_node_dict,
                              operation_dict, edge_dict, return_node, db_triple, fun_trace_list):
        pre_action = action_token
        action_title = action_token[:action_token.index(':-:')]
        action_key = action_token[action_token.index(':-:')+3:]
        if action_token.startswith('add_node'):
            pre_action_class = 'inner_start'
        elif action_token.startswith('add_type_node'):
            pre_action_class = 'type_node'
            action_key = 'TYPE' + action_key
            action_key_c_str = type_node_dict[action_key]['stack'][-1]
            fun_trace_list.append(action_title + ':-:' + action_key_c_str)
        elif action_token.startswith('add_edge'):
            pre_action_class = 'edge'
            action_key_c_str = edge_dict[action_key]['stack'][-1]
            fun_trace_list.append(action_title + ':-:' + action_key_c_str)
        elif action_token.startswith('add_entity_node'):
            pre_action_class = 'entity_node'
            action_key = '_const'
            action_key_c_str = entity_node_dict[action_key]['stack'][-1]
            fun_trace_list.append(action_title + ':-:' + action_key_c_str)
        elif action_token.startswith('add_operation'):
            pre_action_class = 'inner_start'
            operation = action_token[action_token.index(':-:')+3:]
            operation_c_str = operation + ':_:' + str(operation_dict['add'][operation]['count'])
            fun_trace_list.append(action_title + ':-:' + operation_c_str)
        elif action_token.startswith('end_operation:-:arg_count'):
            pre_action_class = 'end_operation_arg_count'
            action_key_c_str = operation_dict['end'][action_key]['stack'][-1]
            fun_trace_list.append(action_title + ':-:' + action_key_c_str)
        elif action_token.startswith('end_operation:-:arg'):
            pre_action_class = 'end_operation_arg'
            action_key_c_str = operation_dict['end'][action_key]['stack'][-1]
            fun_trace_list.append(action_title + ':-:' + action_key_c_str)
        elif action_token.startswith('end_operation:-:_count'):
            pre_action_class = 'end_operation_count'
            action_key_c_str = operation_dict['end'][action_key]['stack'][-1]
            fun_trace_list.append(action_title + ':-:' + action_key_c_str)
        elif action_token.startswith('end_operation:-:_sum'):
            pre_action_class = 'end_operation_sum'
            action_key_c_str = operation_dict['end'][action_key]['stack'][-1]
            fun_trace_list.append(action_title + ':-:' + action_key_c_str)
        elif action_token.startswith('end_operation:-:_not'):
            pre_action_class = 'inner_start'
            action_key_c_str = operation_dict['end'][action_key]['stack'][-1]
            fun_trace_list.append(action_title + ':-:' + action_key_c_str)
        elif action_token.startswith('return'):
            pre_action_class = 'inner_start'
            fun_trace_list.append(action_token)
        return pre_action_class, pre_action, fun_trace_list

    def update_pre_arg_list(self, pre_arg_list, action_token):
        ret_list = copy.deepcopy(pre_arg_list)
        if action_token.startswith('arg_node'):
            ret_list.append('arg_node')
        elif action_token.startswith('ope_for'):
            ret_list.append('ope_for')
        elif action_token.startswith('ope_in'):
            ret_list.append('ope_in')
        elif action_token.startswith('ope_return'):
            ret_list.append('ope_return')
        return (ret_list)

    def update_connection_info(self, pre_action_class, pre_action, action_token, arg_index,
                            node_dict_in_update, type_node_dict_in_update, entity_node_dict_in_update,
                               operation_dict_in_update, edge_dict_in_update, return_node_in_update):
        #print('connection_info: ', pre_action_class, pre_action, arg_index, action_token)
        if 'type_node' == pre_action_class:
            node_type = 'TYPE' + pre_action[pre_action.index(':-:') + 3:]
            node_type_c_str = type_node_dict_in_update[node_type]['stack'][-1]
            type_node_arg = action_token[action_token.index(':-:')+3:]
            if 'arg' not in type_node_dict_in_update[node_type_c_str]:
                type_node_dict_in_update[node_type_c_str]['arg'] = []
            type_node_dict_in_update[node_type_c_str]['arg'].append(type_node_arg)

        elif 'edge' == pre_action_class:
            edge_name = pre_action[pre_action.index(':-:') + 3:]
            edge_name_c_str = edge_dict_in_update[edge_name]['stack'][-1]
            edge_arg = 'arg' + str(arg_index + 1)
            arg_node = action_token[action_token.index(':-:')+3:]
            if edge_arg not in edge_dict_in_update[edge_name_c_str]:
                edge_dict_in_update[edge_name_c_str][edge_arg] = []
            edge_dict_in_update[edge_name_c_str][edge_arg].append(arg_node)
            edge_dict_in_update[edge_name_c_str]['arg_count'] = arg_index + 1

        elif 'entity_node' == pre_action_class:
            split1 = pre_action.index(':-:')
            entity = pre_action[split1 + 3:]
            const_edge = '_const'
            arg_edge =  entity_node_dict_in_update[const_edge]['stack'][-1]
            arg_node = action_token[action_token.index(':-:')+3:]
            entity_node_dict_in_update[entity]['arg1'] = arg_node
            entity_node_dict_in_update[entity]['arg2'] = arg_edge
            entity_node_dict_in_update[arg_edge]['arg1'] = arg_node
            entity_node_dict_in_update[arg_edge]['arg2'] = entity

        elif pre_action_class.startswith('end_operation'):
            end_operation = pre_action[pre_action.index(':-:') + 3:]
            end_operation_c_str = operation_dict_in_update['end'][end_operation]['stack'][-1]
            operation = operation_dict_in_update['end'][end_operation_c_str]
            ope_arg_key = 'arg' + str(arg_index + 1)
            ope_arg_value = action_token[action_token.index(':-:') + 3:]
            if ope_arg_key not in operation_dict_in_update['core'][operation]:
                operation_dict_in_update['core'][operation][ope_arg_key] = []
            operation_dict_in_update['core'][operation][ope_arg_key].append(ope_arg_value)
            operation_dict_in_update['core'][operation]['arg_count'] = arg_index + 1

        elif pre_action_class == 'inner_start':
            if action_token.startswith('add_node'):
                node_id = action_token[action_token.index(':-:')+3:]
                node_dict_in_update[node_id] = {}
                if 'add' in operation_dict_in_update and 'stack' in operation_dict_in_update['add'] and \
                    len(operation_dict_in_update['add']['stack']) > 0:
                        operation = operation_dict_in_update['add']['stack'][-1]
                        if 'arg00' not in operation_dict_in_update['core'][operation]:
                            operation_dict_in_update['core'][operation]['arg00'] = []
                        operation_dict_in_update['core'][operation]['arg00'].append(node_id)
            elif action_token.startswith('add_edge'):
                edge = action_token[action_token.index(':-:')+3:]
                if edge not in edge_dict_in_update:
                    edge_dict_in_update[edge] = {}
                    edge_dict_in_update[edge]['count'] = 0
                edge_c = edge_dict_in_update[edge]['count']
                edge_dict_in_update[edge]['count'] = edge_c + 1
                edge_c_str = edge + ':_:' + str(edge_c+1)
                edge_dict_in_update[edge_c_str] = {}
                if 'stack' not in edge_dict_in_update[edge]:
                    edge_dict_in_update[edge]['stack'] = []
                edge_dict_in_update[edge]['stack'].append(edge_c_str)
                if 'add' in operation_dict_in_update and 'stack' in operation_dict_in_update['add'] and \
                    len(operation_dict_in_update['add']['stack']) > 0:
                        operation = operation_dict_in_update['add']['stack'][-1]
                        if 'arg0' not in operation_dict_in_update['core'][operation]:
                            operation_dict_in_update['core'][operation]['arg0'] = []
                        operation_dict_in_update['core'][operation]['arg0'].append(edge_c_str)

            elif action_token.startswith('add_type_node'):
                type_edge = 'TYPE' + action_token[action_token.index(':-:')+3:]
                if type_edge not in type_node_dict_in_update:
                    type_node_dict_in_update[type_edge] = {}
                    type_node_dict_in_update[type_edge]['count'] = 0
                type_edge_c = type_node_dict_in_update[type_edge]['count']
                type_node_dict_in_update[type_edge]['count'] = type_edge_c + 1
                type_edge_c_str = type_edge + ':_:' + str(type_edge_c+1)
                type_node_dict_in_update[type_edge_c_str] = {}
                if 'stack' not in type_node_dict_in_update[type_edge]:
                    type_node_dict_in_update[type_edge]['stack'] = []
                type_node_dict_in_update[type_edge]['stack'].append(type_edge_c_str)
                if 'add' in operation_dict_in_update and 'stack' in operation_dict_in_update['add'] and \
                    len(operation_dict_in_update['add']['stack']) > 0:
                        operation = operation_dict_in_update['add']['stack'][-1]
                        if 'arg0' not in operation_dict_in_update['core'][operation]:
                            operation_dict_in_update['core'][operation]['arg0'] = []
                        operation_dict_in_update['core'][operation]['arg0'].append(type_edge_c_str)

            elif action_token.startswith('add_entity_node'):
                entity = action_token[action_token.index(':-:')+3:]
                const_edge = '_const'
                if const_edge not in entity_node_dict_in_update:
                    entity_node_dict_in_update[const_edge] = {}
                    entity_node_dict_in_update[const_edge]['count'] = 0
                const_edge_c = entity_node_dict_in_update[const_edge]['count']
                entity_node_dict_in_update[const_edge]['count'] = const_edge_c + 1
                const_edge_c_str = const_edge + ':_:' + str(const_edge_c+1)
                entity_node_dict_in_update[const_edge_c_str] = {}
                if 'stack' not in entity_node_dict_in_update[const_edge]:
                    entity_node_dict_in_update[const_edge]['stack'] = []
                entity_node_dict_in_update[const_edge]['stack'].append(const_edge_c_str)
                entity_node_dict_in_update[entity] = {}
                if 'add' in operation_dict_in_update and 'stack' in operation_dict_in_update['add'] and \
                    len(operation_dict_in_update['add']['stack']) > 0:
                        operation = operation_dict_in_update['add']['stack'][-1]
                        if 'arg0' not in operation_dict_in_update['core'][operation]:
                            operation_dict_in_update['core'][operation]['arg0'] = []
                        operation_dict_in_update['core'][operation]['arg0'].append(const_edge_c_str)

            elif action_token.startswith('add_operation'):
                operation = action_token[action_token.index(':-:') + 3:]
                if 'add' not in operation_dict_in_update:
                    operation_dict_in_update['add'] = {}
                if operation not in operation_dict_in_update['add']:
                    operation_dict_in_update['add'][operation] = {}
                    operation_dict_in_update['add'][operation]['count'] = 0
                operation_c = operation_dict_in_update['add'][operation]['count']
                operation_dict_in_update['add'][operation]['count'] = operation_c + 1
                operation_c_str = operation + ':_:' + str(operation_c + 1)
                if 'core' not in operation_dict_in_update:
                    operation_dict_in_update['core'] = {}
                operation_dict_in_update['core'][operation_c_str] = {}
                if 'stack' not in operation_dict_in_update['add']:
                    operation_dict_in_update['add']['stack'] = []
                operation_dict_in_update['add']['stack'].append(operation_c_str)
                if 'add' in operation_dict_in_update and 'stack' in operation_dict_in_update['add'] and \
                    len(operation_dict_in_update['add']['stack']) > 1:
                        operation = operation_dict_in_update['add']['stack'][-2]
                        if 'arg0' not in operation_dict_in_update['core'][operation]:
                            operation_dict_in_update['core'][operation]['arg0'] = []
                        operation_dict_in_update['core'][operation]['arg0'].append(operation_c_str)

            elif action_token.startswith('end_operation'):
                if 'end' not in operation_dict_in_update:
                    operation_dict_in_update['end'] = {}
                end_operation = action_token[action_token.index(':-:')+3:]
                if end_operation not in operation_dict_in_update['end']:
                    operation_dict_in_update['end'][end_operation] = {}
                    operation_dict_in_update['end'][end_operation]['count'] = 0
                end_operation_c = operation_dict_in_update['end'][end_operation]['count']
                operation_dict_in_update['end'][end_operation]['count'] = end_operation_c + 1
                operation = operation_dict_in_update['add']['stack'].pop()
                end_operation_c_str = operation
                operation_dict_in_update['end'][end_operation_c_str] = {}
                if 'stack' not in operation_dict_in_update['end'][end_operation]:
                    operation_dict_in_update['end'][end_operation]['stack'] = []
                operation_dict_in_update['end'][end_operation]['stack'].append(end_operation_c_str)
                operation = operation_dict_in_update['add']['stack'].pop()
                operation_dict_in_update['end'][end_operation_c_str] = operation
                operation_dict_in_update['add'][operation] = end_operation

            elif action_token.startswith('return'):
                node_id = action_token[action_token.index(':-:')+3:]
                return_node_in_update['node'] = node_id

        elif pre_action_class == 'start':
            if action_token.startswith('add_node'):
                node_id = action_token[action_token.index(':-:') + 3:]
                node_dict_in_update[node_id] = {}
            elif action_token.startswith('add_operation'):
                operation = action_token[action_token.index(':-:') + 3:]
                if 'add' not in operation_dict_in_update:
                    operation_dict_in_update['add'] = {}
                if operation not in operation_dict_in_update['add']:
                    operation_dict_in_update['add'][operation] = {}
                    operation_dict_in_update['add'][operation]['count'] = 0
                operation_c = operation_dict_in_update['add'][operation]['count']
                operation_dict_in_update['add'][operation]['count'] = operation_c + 1
                operation_c_str = operation + ':_:' + str(operation_c + 1)
                if 'core' not in operation_dict_in_update:
                    operation_dict_in_update['core'] = {}
                operation_dict_in_update['core'][operation_c_str] = {}
                if 'stack' not in operation_dict_in_update['add']:
                    operation_dict_in_update['add']['stack'] = []
                operation_dict_in_update['add']['stack'].append(operation_c_str)

        else:
            pass


    def is_legal_action_seq(self, action_seq):
        gen_pre_action_in = ''
        gen_pre_action_class_in = 'start'
        gen_pre_arg_list_in = []
        legal_action_seq = True
        legal_action_seq_test = True
        node_dict = {}
        type_node_dict = {}
        entity_node_dict = {}
        operation_dict = {}
        edge_dict = {}
        return_node = {}
        db_triple = {}
        fun_trace_list_in = []
        for action_token in action_seq:
            gen_flag_test = self.is_legal_action(gen_pre_action_class_in, gen_pre_arg_list_in, action_token,
                                                             gen_pre_action_in, node_dict, type_node_dict,
                                                             entity_node_dict, operation_dict, edge_dict, return_node,
                                                             db_triple, fun_trace_list_in, False)
            if not gen_flag_test:
                legal_action_seq_test = False
                #print('action seq is not legal in test: ', action_token)


            gen_flag, gen_pre_action_class_out, gen_pre_arg_list_out, gen_pre_action_out, fun_trace_list_out = \
                self.is_legal_action_then_read(gen_pre_action_class_in, gen_pre_arg_list_in, action_token,
                                                             gen_pre_action_in, node_dict, type_node_dict,
                                                             entity_node_dict, operation_dict, edge_dict, return_node,
                                                             db_triple, fun_trace_list_in, False)

            if not gen_flag:
                legal_action_seq = False
                #print('action seq is not legal in read: ', action_token)
                break

            gen_pre_action_class_in = gen_pre_action_class_out
            gen_pre_arg_list_in = gen_pre_arg_list_out
            gen_pre_action_in = gen_pre_action_out
            fun_trace_list_in = fun_trace_list_out

            if not legal_action_seq_test or not legal_action_seq:
                break

        return (legal_action_seq_test, legal_action_seq)

    def check_before_update(self, pre_action_class, pre_action, action_token, arg_index, node_dict,
                            edge_dict, type_node_dict, entity_node_dict, operation_dict, return_node, db_triple):
        #print('start check_before_update!')
        if pre_action_class == 'edge':
            node = action_token[action_token.index(':-:') + 3:]
            if node not in node_dict:
                return False
            if arg_index == 1:
                node1 = pre_action[pre_action.index(':-:') + 3:]
                if node == node1:
                    return False
        elif pre_action_class == 'type_node':
            node = action_token[action_token.index(':-:') + 3:]
            if node not in node_dict:
                return False
        elif pre_action_class == 'entity_node':
            node = action_token[action_token.index(':-:') + 3:]
            if node not in node_dict:
                return False
        elif pre_action_class == 'end_operation_arg':
            if arg_index == 0:
                node = action_token[action_token.index(':-:') + 3:]
                if node not in node_dict:
                    return False
        elif pre_action_class == 'end_operation_arg_count':
            if arg_index == 0:
                node = action_token[action_token.index(':-:') + 3:]
                if node not in node_dict:
                    return False
            elif arg_index == 1:
                node = action_token[action_token.index(':-:') + 3:]
                if node not in node_dict:
                    return False
                node1 = pre_action[pre_action.index(':-:') + 3:]
                if node == node1:
                    return False
        elif pre_action_class == 'end_operation_count':
            if arg_index == 0:
                node = action_token[action_token.index(':-:') + 3:]
                if node not in node_dict:
                    return False
        elif pre_action_class == 'end_operation_sum':
            if arg_index == 0:
                node = action_token[action_token.index(':-:') + 3:]
                if node not in node_dict:
                    return False
        elif pre_action_class == 'inner_start':
            if action_token.startswith('add_node'):
                node_count = len(node_dict)
                node_in_edge_set = set()
                for edge in edge_dict:
                    if ':_:' not in edge:
                        continue
                    node_in_edge_set.add(edge_dict[edge]['arg1'][0])
                    node_in_edge_set.add(edge_dict[edge]['arg2'][0])
                node_in_edge_count = len(node_in_edge_set)
                if node_count - node_in_edge_count > 1:
                    return False
            elif action_token.startswith('end_operation:'):
                end_ope_name = action_token[action_token.index(':-:')+3:]
                if 'add' not in operation_dict or 'stack' not in operation_dict['add'] or len(operation_dict['add']['stack']) == 0:
                    return False
                add_ope_name_c_str = operation_dict['add']['stack'][-1]
                add_ope_name_full = add_ope_name_c_str[:add_ope_name_c_str.index(':_:')]
                ope_arg_fun_list = ['_highest', '_longest', '_shortest', '_lowest', '_largest', '_smallest']
                ope_arg_count_fun_list = ['_fewest', '_most']
                if add_ope_name_full in ope_arg_fun_list:
                    add_ope_name = 'arg'
                elif add_ope_name_full in ope_arg_count_fun_list:
                    add_ope_name = 'arg_count'
                else:
                    add_ope_name = add_ope_name_full
                if not add_ope_name == end_ope_name:
                    return False
                if 'core' not in operation_dict or add_ope_name_c_str not in operation_dict['core'] or \
                    'arg0' not in operation_dict['core'][add_ope_name_c_str]:
                    return False
                node_in_ope_set = set()
                node_in_edge_set = set()
                if 'arg00' in operation_dict['core'][add_ope_name_c_str]:
                    for node in operation_dict['core'][add_ope_name_c_str]['arg00']:
                        node_in_ope_set.add(node)
                for edge_or_fun in operation_dict['core'][add_ope_name_c_str]['arg0']:
                    if edge_or_fun in edge_dict:
                        node_in_edge_set.add(edge_dict[edge_or_fun]['arg1'][0])
                        node_in_edge_set.add(edge_dict[edge_or_fun]['arg2'][0])
                    elif edge_or_fun in type_node_dict:
                        node_in_edge_set.add(type_node_dict[edge_or_fun]['arg'][0])
                    elif edge_or_fun in entity_node_dict:
                        node_in_edge_set.add(entity_node_dict[edge_or_fun]['arg1'])
                for node in node_in_ope_set:
                    if node not in node_in_edge_set:
                        return False
            elif action_token.startswith('add_type_node'):
                if len(node_dict) == 0:
                    return False
            elif action_token.startswith('add_entity_node'):
                if len(node_dict) == 0:
                    return False
            elif action_token.startswith('add_edge'):
                if len(node_dict) < 2:
                    return False
            elif action_token.startswith('return'):
                return self.final_check(node_dict, type_node_dict, entity_node_dict, operation_dict, edge_dict, return_node, db_triple)
        return True
