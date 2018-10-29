""" code to convert geo sequence to action sequence"""

import os
import glob
import sys
import re

IN_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action_copy\\action\\geo880\\seq0")
OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action_copy\\action\\geo880\\action0")

def read_examples(filename):
    base_file_name = os.path.basename(filename)
    examples = []
    len_all = 0
    count = 0
    utterance = None
    logical_form = None
    with open(filename) as f:
        for line in f:
            line = line.strip()
            print(line)
            utterance, logical_form = line.rstrip('\n').split('\t')
            if base_file_name == 'geo880_train600.tsv':
                count += 1
                len_all += len(logical_form.split(' '))
            examples.append((utterance, logical_form))
    if count != 0:
        print('*************** logical_form **************')
        print('count = ' + str(count) + ', average_len = ' + str(len_all/count))
        print('********************************************')
    return examples

def write(out_filename, out_data):
    out_path = os.path.join(OUT_DIR, out_filename)
    len_all = 0
    count = 0
    with open(out_path, "w") as f:
        for x, y in out_data:
            #print('%s\t%s' % (x, ' '.join(y)), file=f)
            print >> f, '%s\t%s' % (x, ' '.join(y))
            if out_filename == 'geo880_train600.tsv':
                count += 1
                len_all += len(y)
    if count != 0:
        print('************** action ********************')
        print('count = ' + str(count) + ', average_len = ' + str(len_all/count))
        print('********************************************')

def is_connected(connected_node, node_id=None, node1_id=None, node2_id=None, entity_node_id=None):
    if len(connected_node) == 0:
        return True
    if node_id:
        if node_id in connected_node:
            return True
    if node1_id and node2_id:
        if node1_id in connected_node or node2_id in connected_node:
            return True
    if entity_node_id in connected_node:
        return True
    return False


def seq2action(logical_form):
    ope_fun_type_all = ['OPE ARG', 'NOT', 'COUNT', 'SUM']
    arg_fun_list = ['_highest', '_longest', '_shortest', '_lowest', '_largest', '_smallest', '_fewest', '_most']
    node_prefix = 'add_node:-:'
    entity_node_prefix = 'add_entity_node:-:'
    edge_prefix = 'add_edge:-:'
    type_node_prefix = 'add_type_node:-:'
    operation_prefix = 'add_operation:-:'
    operation_end_prefix = 'end_operation:-:'
    operation_end_arg_full = 'end_operation:-:arg'
    operation_end_arg_count_full = 'end_operation:-:arg_count'
    operation_for_prefix = 'ope_for:-:'
    operation_in_prefix = 'ope_in:-:'
    operation_return_prefix = 'ope_return:-:'
    return_prefix = 'return:-:'

    left_num_paren = 0
    right_num_paren = 0

    arg_node_prefix = 'arg_node:-:'

    act_seq = []
    fun_stack = []
    fun_trace = []
    cur_fun_index = ''
    next_is_entity = False
    entity = ''
    entity_type = ''
    argument_stack_map = {}
    fun_position_map = {}
    fun_left_paren_map = {}
    fun_type_map = {}
    fun_ope_map = {}
    ope_fun_flag_map = {}
    node_id_stack = []
    node_entity_map = {}
    ord_A = ord('A')
    ord_Z = ord('Z')

    lf_seq = logical_form.split(' ')
    index = 0
    for lf_token in lf_seq:
        if len(fun_stack) > 0:
            cur_fun_index = fun_stack[-1]
        index += 1

        if lf_token == '(':
            if left_num_paren > fun_left_paren_map[cur_fun_index]: # empty function, should insert one
                lf_token_index = '_dummy::' + str(index)
                if len(fun_stack) > 0:
                    fun_pre = fun_stack[-1]
                    argument_stack_map[fun_pre].append('fun:-:' + lf_token_index)
                fun_stack.append(lf_token_index)
                argument_stack_map[lf_token_index] = []
                fun_left_paren_map[lf_token_index] = left_num_paren

            left_num_paren += 1
            continue

        if lf_token == ')':
            right_num_paren += 1
            if len(fun_stack) == 0:
                continue
            fun_with_index_from_stack = fun_stack.pop()
            fun_trace.append(fun_with_index_from_stack)
            fun_from_stack = fun_with_index_from_stack[:fun_with_index_from_stack.index('::')]
            fun_position_map[fun_with_index_from_stack] = left_num_paren - right_num_paren

            if fun_from_stack == '_stateid':
                fun_type_map[cur_fun_index] = 'ENTITY'
                entity_type = 'state'
                if len(entity) > 0 and entity[-1] == '_':
                    entity = entity[:-1]
                argument_stack_map[fun_with_index_from_stack].append(entity.strip())
                next_is_entity = False
            elif fun_from_stack == '_cityid':
                fun_type_map[cur_fun_index] = 'ENTITY'
                entity_type = 'city'
                if len(entity) > 0 and entity[-1] == '_':
                    entity = entity[:-1]
                argument_stack_map[fun_with_index_from_stack].append(entity.strip().replace(' ', ':'))
                next_is_entity = False
            elif fun_from_stack == '_countryid':
                fun_type_map[cur_fun_index] = 'ENTITY'
                entity_type = 'country'
                if len(entity) > 0 and entity[-1] == '_':
                    entity = entity[:-1]
                argument_stack_map[fun_with_index_from_stack].append(entity.strip())
                next_is_entity = False
            elif fun_from_stack == '_riverid':
                fun_type_map[cur_fun_index] = 'ENTITY'
                entity_type = 'river'
                if len(entity) > 0 and entity[-1] == '_':
                    entity = entity[:-1]
                argument_stack_map[fun_with_index_from_stack].append(entity.strip())
                next_is_entity = False
            elif fun_from_stack == '_placeid':
                fun_type_map[cur_fun_index] = 'ENTITY'
                entity_type = 'place'
                if len(entity) > 0 and entity[-1] == '_':
                    entity = entity[:-1]
                argument_stack_map[fun_with_index_from_stack].append(entity.strip())
                next_is_entity = False
            elif fun_from_stack == '_const':
                fun_type_map[cur_fun_index] = 'CONST'
                if len(fun_stack) > 0:
                    pre_fun_with_index_from_stack = fun_stack[-1]
                    pre_fun_from_stack = pre_fun_with_index_from_stack[:pre_fun_with_index_from_stack.index('::')]
                    if pre_fun_from_stack == '\+' and \
                            fun_left_paren_map[pre_fun_with_index_from_stack] == fun_left_paren_map[fun_with_index_from_stack]:
                        not_fun_from_stack = fun_stack.pop()
                        fun_type_map[not_fun_from_stack] = 'NOT'
                        fun_trace.append(not_fun_from_stack)
                        fun_position_map[not_fun_from_stack] = left_num_paren - right_num_paren
                        cur_fun_index = not_fun_from_stack
                node_id = node_id_stack.pop()
                node_entity_map[node_id] = (entity.strip(), entity_type)
                entity = ''

            elif fun_from_stack in arg_fun_list:
                fun_type_map[cur_fun_index] = 'OPE ARG'
            elif fun_from_stack == '_sum':
                fun_type_map[cur_fun_index] = 'SUM'
            elif fun_from_stack == '_count':
                fun_type_map[cur_fun_index] = 'COUNT'
            elif fun_from_stack == '\+':
                fun_type_map[cur_fun_index] = 'NOT'
            elif fun_from_stack == '_answer':
                fun_type_map[cur_fun_index] = 'RETURN'
            elif fun_from_stack == '_dummy':
                fun_type_map[cur_fun_index] = 'DUMMY'
            elif len(argument_stack_map[fun_with_index_from_stack]) == 1:
                fun_type_map[cur_fun_index] = 'UNARY'
            elif len(argument_stack_map[fun_with_index_from_stack]) == 2:
                fun_type_map[cur_fun_index] = 'BINARY'
            else:
                fun_type_map[cur_fun_index] = 'TODO FUN TYPE'
                print(cur_fun_index)


        if len(lf_token) == 1:
            ord_c = ord(lf_token)
            if ord_c >= ord_A and ord_c <= ord_Z:
                character = lf_token
                argument_stack_map[cur_fun_index].append('node:-:' + character)
                node_id_stack.append(character)
            continue
        elif lf_token.startswith('_') or lf_token == '\+':
            lf_token_index = lf_token + '::' + str(index)
            if lf_token == '_const':
                next_is_entity = True
            if len(fun_stack) > 0:
                fun_pre = fun_stack[-1]
                argument_stack_map[fun_pre].append('fun:-:' + lf_token_index)
            fun_stack.append(lf_token_index)
            argument_stack_map[lf_token_index] = []
            fun_left_paren_map[lf_token_index] = left_num_paren
        else:
            if next_is_entity:
                entity += lf_token + '_'

    node_in_actions = set()
    connected_node = set()
    edge_in_actions = set()
    type_in_actions = set()
    ope_in_actions = set()
    entity = ''
    entity_type = ''
    entity_node_id = ''
    node_type = ''

    fun_name_map = {}
    fun_argument_map = {}
    arg_connection_map = {}

    ll = len(fun_trace)
    flag_fun_trace = []
    for i in range(ll):
        flag_fun_trace.append(False)

    first_index = 0


    index = 0
    for fun_with_index_from_stack in list(reversed(fun_trace)):
        argument_from_fun_stack = argument_stack_map[fun_with_index_from_stack]
        fun_type = fun_type_map[fun_with_index_from_stack]
        if fun_type in ope_fun_type_all:
            ope_fun_flag_map[fun_with_index_from_stack] = True
            for argument in argument_from_fun_stack:
                if not argument.startswith('fun:-:'):
                    continue
                arg_fun = argument[6:]
                if arg_fun not in fun_ope_map:
                    fun_ope_map[arg_fun] = []
                if fun_with_index_from_stack in fun_ope_map:
                    for ope_fun in fun_ope_map[fun_with_index_from_stack]:
                        if ope_fun not in fun_ope_map[arg_fun]:
                            fun_ope_map[arg_fun].append(ope_fun)
                if fun_with_index_from_stack not in fun_ope_map[arg_fun]:
                    fun_ope_map[arg_fun].append(fun_with_index_from_stack)
        else:
            if fun_with_index_from_stack not in fun_ope_map:
                fun_ope_map[fun_with_index_from_stack] = []
            for ope_fun in fun_ope_map[fun_with_index_from_stack]:
                for argument in argument_from_fun_stack:
                    if not argument.startswith('fun:-:'):
                        continue
                    arg_fun = argument[6:]
                    if arg_fun not in fun_ope_map:
                        fun_ope_map[arg_fun] = []
                    if fun_with_index_from_stack not in fun_ope_map[arg_fun]:
                        fun_ope_map[arg_fun].append(ope_fun)


    for fun_with_index_from_stack in fun_trace:
        arg_connection_map[fun_with_index_from_stack] = False
        argument_from_fun_stack = argument_stack_map[fun_with_index_from_stack]
        ope_fun_list = []
        if fun_with_index_from_stack in fun_ope_map:
            ope_fun_list = fun_ope_map[fun_with_index_from_stack]
        #print('index = ', index, ', fun = ' + fun_with_index_from_stack + ', fun_type = ' + fun_type_map[fun_with_index_from_stack] + \
        #    ', position = ' + str(fun_position_map[fun_with_index_from_stack]) + ', argument = [ ' + ' '.join(argument_from_fun_stack) + ' ]' + \
        #      ', ope_fun = ' + ' '.join(ope_fun_list))
        index += 1

    while first_index < ll:
        second_index = first_index
        if flag_fun_trace[first_index]:
            first_index += 1
            continue
        while second_index < ll:
            #print(first_index, second_index, fun_trace, flag_fun_trace, connected_node)
            #print(act_seq)
            if flag_fun_trace[first_index]:
                first_index += 1
                break
            fun_with_index_from_stack = fun_trace[second_index]
            position = fun_position_map[fun_with_index_from_stack]

            fun_from_stack = fun_with_index_from_stack[:fun_with_index_from_stack.index('::')]
            fun_type = fun_type_map[fun_with_index_from_stack]
            argument_list = argument_stack_map[fun_with_index_from_stack]

            if flag_fun_trace[second_index]:
                second_index += 1
                continue

            if fun_type == 'UNARY':
                argument = argument_list[0]
                if not argument.startswith('node:-:'):
                    print('Error: ' + argument)
                    break
                node_id = argument[7:]

                if not is_connected(connected_node, node_id, None, None, None):
                    second_index += 1
                    continue
                else:
                    flag_fun_trace[second_index] = True
                    if first_index == second_index:
                        first_index += 1
                    arg_connection_map[argument] = True
                    arg_connection_map[fun_with_index_from_stack] = True

                for ope_fun in fun_ope_map[fun_with_index_from_stack]:
                    if ope_fun_flag_map[ope_fun]:
                        ope_name = ope_fun[:ope_fun.index('::')]
                        if not ope_name.startswith('_') and '+' in ope_name:
                            ope_name = '_not'
                        ope_action = operation_prefix + ope_name
                        act_seq.append(ope_action)
                        ope_fun_flag_map[ope_fun] = False

                if node_id not in node_in_actions:
                    add_node_action = node_prefix + node_id
                    node_in_actions.add(node_id)
                    connected_node.add(node_id)
                    act_seq.append(add_node_action)
                else:
                    pass

                add_type_node_action = type_node_prefix + fun_from_stack
                act_seq.append(add_type_node_action)
                act_seq.append(arg_node_prefix + node_id)
                fun_arg = node_id
                fun_argument_map[fun_with_index_from_stack] = [(fun_arg, 'TYPE', fun_from_stack)]

            elif fun_type == 'BINARY':
                arg1 = argument_list[0]
                arg2 = argument_list[1]

                if not arg1.startswith('node:-:'):
                    print('Error: ' + arg1)
                    break
                node1_id = arg1[7:]
                if not arg2.startswith('node:-:'):
                    print('Error: ' + arg2)
                    break
                node2_id = arg2[7:]

                if not is_connected(connected_node, None, node1_id, node2_id, None):
                    second_index += 1
                    continue
                else:
                    flag_fun_trace[second_index] = True
                    if first_index == second_index:
                        first_index += 1
                    arg_connection_map[fun_with_index_from_stack] = True
                    arg_connection_map[arg1] = True
                    arg_connection_map[arg2] = True

                for ope_fun in fun_ope_map[fun_with_index_from_stack]:
                    if ope_fun_flag_map[ope_fun]:
                        ope_name = ope_fun[:ope_fun.index('::')]
                        if not ope_name.startswith('_') and '+' in ope_name:
                            ope_name = '_not'
                        ope_action = operation_prefix + ope_name
                        act_seq.append(ope_action)
                        ope_fun_flag_map[ope_fun] = False

                if node1_id not in node_in_actions:
                    add_node_action = node_prefix + node1_id
                    node_in_actions.add(node1_id)
                    connected_node.add(node1_id)
                    act_seq.append(add_node_action)
                if node2_id not in node_in_actions:
                    add_node_action = node_prefix + node2_id
                    node_in_actions.add(node2_id)
                    connected_node.add(node2_id)
                    act_seq.append(add_node_action)

                add_edge_action = edge_prefix + fun_from_stack
                act_seq.append(add_edge_action)
                act_seq.append(arg_node_prefix + node1_id)
                act_seq.append(arg_node_prefix + node2_id)

                fun_arg1 = node1_id
                fun_arg2 = node2_id
                fun_argument_map[fun_with_index_from_stack] = [(fun_arg1, fun_from_stack, fun_arg2)]

            elif fun_type == 'OPE ARG':
                arg_for_ope_list = []
                ope_connection_flag = True
                if argument_list[0] not in arg_connection_map:
                    ope_connection_flag = False
                for arg_fun_with_title in argument_list[1:]:
                    arg_fun = arg_fun_with_title[arg_fun_with_title.index(':-:') + 3:]
                    if len(arg_fun) == 1:
                        ord_c = ord(arg_fun)
                        if ord_c >= ord_A and ord_c <= ord_Z:
                            continue
                    if arg_fun not in arg_connection_map:
                        ope_connection_flag = False
                        break
                    if not arg_connection_map[arg_fun]:
                        ope_connection_flag = False
                if not ope_connection_flag:
                    second_index += 1
                    continue

                arg_connection_map[fun_with_index_from_stack] = True

                ope_end_action = operation_end_arg_full
                if len(argument_list) > 1 and argument_list[1].startswith('node:-:'):
                    ope_end_action = operation_end_arg_count_full
                act_seq.append(ope_end_action)
                ope_for = argument_list[0][7:]
                ope_for_action = operation_for_prefix + ope_for
                act_seq.append(ope_for_action)
                if len(argument_list) > 1 and argument_list[1].startswith('node:-:'):
                    ope_for = argument_list[1][7:]
                    ope_for_action = operation_for_prefix + ope_for
                    act_seq.append(ope_for_action)

                flag_fun_trace[second_index] = True
                if first_index == second_index:
                    first_index += 1
                fun_argument_map[fun_with_index_from_stack] = arg_for_ope_list

            elif fun_type == 'ENTITY':
                entity = argument_list[0]
            elif fun_type == 'CONST':
                arg = argument_list[0]
                entity_node_id = arg[7:]
                _, entity_type = node_entity_map[entity_node_id]
                if not is_connected(connected_node, None, None, None, entity_node_id):
                    second_index += 1
                    continue
                else:
                    arg_connection_map[fun_with_index_from_stack] = True

                for ope_fun in fun_ope_map[fun_with_index_from_stack]:
                    if ope_fun_flag_map[ope_fun]:
                        ope_name = ope_fun[:ope_fun.index('::')]
                        if not ope_name.startswith('_') and '+' in ope_name:
                            ope_name = '_not'
                        ope_action = operation_prefix + ope_name
                        act_seq.append(ope_action)
                        ope_fun_flag_map[ope_fun] = False

                flag_fun_trace[second_index] = True
                if second_index - 1 >= 0:
                    flag_fun_trace[second_index-1] = True
                    arg_connection_map[fun_trace[second_index-1]] = True

                if entity_node_id not in node_in_actions:
                    act_seq.append(node_prefix + entity_node_id)
                    node_in_actions.add(entity_node_id)
                    connected_node.add(entity_node_id)

                act_seq.append(entity_node_prefix + entity + ':=:' + entity_type)
                act_seq.append(arg_node_prefix + entity_node_id)
                fun_argument_map[fun_with_index_from_stack] = []
                fun_argument_map[fun_with_index_from_stack].append((entity_node_id, fun_from_stack, entity + ':=:' + entity_type))

                if first_index == second_index - 1:
                    first_index += 1
                    continue

            elif fun_type == 'SUM':
                arg_for_sum_list = []
                sum_connection_flag = True
                if argument_list[0] not in arg_connection_map:
                    ope_connection_flag = False
                for arg_fun_with_title in argument_list[1:-1]:
                    arg_fun = arg_fun_with_title[arg_fun_with_title.index(':-:') + 3:]
                    if len(arg_fun) == 1:
                        ord_c = ord(arg_fun)
                        if ord_c >= ord_A and ord_c <= ord_Z:
                            continue
                    if arg_fun not in arg_connection_map:
                        sum_connection_flag = False
                        break
                    if not arg_connection_map[arg_fun]:
                        sum_connection_flag = False
                if not sum_connection_flag:
                    second_index += 1
                    continue
                if first_index != second_index:
                    second_index += 1
                    continue
                arg_connection_map[fun_with_index_from_stack] = True

                ope_end_action = operation_end_prefix + fun_from_stack
                act_seq.append(ope_end_action)
                sum_for = argument_list[0][7:]
                sum_for_action = operation_for_prefix + sum_for
                act_seq.append(sum_for_action)
                sum_in = argument_list[-2][argument_list[-2].index(':-:')+3 : argument_list[-2].index('::')]
                sum_in_action = operation_in_prefix + sum_in
                act_seq.append(sum_in_action)
                sum_return = argument_list[-1][7:]
                sum_return_action = operation_return_prefix + sum_return
                act_seq.append(sum_return_action)

                fun_argument_map[fun_with_index_from_stack] = arg_for_sum_list
                if first_index == second_index:
                    first_index += 1

            elif fun_type == 'COUNT':
                arg_for_ope_list = []
                if first_index != second_index:
                    second_index += 1
                    continue
                count_connection_flag = True
                if argument_list[0] not in arg_connection_map:
                    count_connection_flag = False
                for arg_fun_with_title in argument_list[1:-1]:
                    arg_fun = arg_fun_with_title[arg_fun_with_title.index(':-:') + 3:]
                    if len(arg_fun) == 1:
                        ord_c = ord(arg_fun)
                        if ord_c >= ord_A and ord_c <= ord_Z:
                            continue
                    if arg_fun not in arg_connection_map:
                        count_connection_flag = False
                        break
                    if not arg_connection_map[arg_fun]:
                        count_connection_flag = False
                if not count_connection_flag:
                    second_index += 1
                    continue
                arg_connection_map[fun_with_index_from_stack] = True

                ope_end_action = operation_end_prefix + fun_from_stack
                act_seq.append(ope_end_action)
                count_for = argument_list[0][7:]
                count_for_action = operation_for_prefix + count_for
                act_seq.append(count_for_action)
                count_return = argument_list[-1][7:]
                count_return_action = operation_return_prefix + count_return
                act_seq.append(count_return_action)

                fun_argument_map[fun_with_index_from_stack] = arg_for_ope_list
                if first_index == second_index:
                    first_index += 1

            elif fun_type == 'NOT':
                arg_for_not_list = []
                if first_index != second_index:
                    second_index += 1
                    continue
                not_connection_flag = True
                for arg_fun_with_title in argument_list:
                    arg_fun = arg_fun_with_title[arg_fun_with_title.index(':-:') + 3:]
                    if len(arg_fun) == 1:
                        ord_c = ord(arg_fun)
                        if ord_c >= ord_A and ord_c <= ord_Z:
                            continue
                    if arg_fun not in arg_connection_map:
                        not_connection_flag = False
                        break
                    if not arg_connection_map[arg_fun]:
                        not_connection_flag = False
                if not not_connection_flag:
                    second_index += 1
                    continue
                arg_connection_map[fun_with_index_from_stack] = True

                ope_end_action = operation_end_prefix + '_not'
                act_seq.append(ope_end_action)
                fun_name_map[fun_with_index_from_stack] = '_not'
                fun_argument_map[fun_with_index_from_stack] = arg_for_not_list
                if first_index == second_index:
                    first_index += 1
            elif fun_type == 'RETURN':
                if first_index != second_index:
                    second_index += 1
                    continue
                argument = argument_list[0]
                if argument.startswith('node:-:'):
                    return_action = return_prefix + argument[7:]
                    act_seq.append(return_action)
                if first_index == second_index:
                    first_index += 1
            elif fun_type == 'DUMMY':
                arg_for_dummy_list = []
                dummy_connection_flag = True
                for arg_fun_with_title in argument_list:
                    arg_fun = arg_fun_with_title[arg_fun_with_title.index(':-:') + 3:]
                    if len(arg_fun) == 1:
                        ord_c = ord(arg_fun)
                        if ord_c >= ord_A and ord_c <= ord_Z:
                            continue
                    if arg_fun not in arg_connection_map:
                        dummy_connection_flag = False
                        break
                    if not arg_connection_map[arg_fun]:
                        dummy_connection_flag = False
                if not dummy_connection_flag:
                    second_index += 1
                    continue

                arg_connection_map[fun_with_index_from_stack] = True
                for arg_fun_with_title in argument_list:
                    arg_fun = arg_fun_with_title[arg_fun_with_title.index(':-:') + 3:]
                    if len(arg_fun) == 1:
                        ord_c = ord(arg_fun)
                        if ord_c >= ord_A and ord_c <= ord_Z:
                            continue
                    if arg_fun not in fun_argument_map:
                        continue
                    arg_fun_type = fun_type_map[arg_fun]
                    if arg_fun_type == 'OPE ARG' or arg_fun_type == 'COUNT' or \
                                    arg_fun_type == 'NOT' or arg_fun_type == 'SUM':
                        arg_for_dummy_list.append((arg_fun, None))
                        continue
                    for arg_triple in fun_argument_map[arg_fun]:
                        arg_for_dummy_list.append(arg_triple)
                fun_argument_map[fun_with_index_from_stack] = arg_for_dummy_list
                if first_index == second_index:
                    first_index += 1
            else:
                print('TODO: ' + fun_type)

            second_index += 1

    #print('####### argument_stack_map ##########')
    #print(argument_stack_map)
    #print('####### fun_argument_map ##########')
    #print(fun_argument_map)
    return act_seq

def test_convertion():
    lf = '_answer ( A , _smallest ( A , _most ( A , B , ( _state ( A ) , _next_to ( A , B ) , _state ( B ) ) ) ) )'
    print(lf)
    print('len = ' + str(len(lf.split(' '))))
    actions = seq2action(lf)
    print('actions: ' + ', '.join(actions))
    ii = 0
    jj = ii + 1
    print('----------------------------------------------')
    while ii < len(actions):
        while jj < len(actions) and not actions[jj].startswith('add') and not actions[jj].startswith('return')\
                and not actions[jj].startswith('end_operation'):
            jj += 1
            if jj >= len(actions):
                jj = len(actions)
        print(' , '.join(actions[ii:jj]))
        ii = jj
        jj = ii + 1
    print('len = ' + str(len(actions)))

def process(filename, base_file_name):
    in_data = read_examples(filename)
    out_data = []
    for (utterance, logical_form) in in_data:
        print('utterance: ' + utterance)
        print('logical_form: ' + logical_form)
        y = seq2action(logical_form)
        #print('actions: ' + ' '.join(y))
        out_data.append((utterance, y))
    write(base_file_name, out_data)


def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
    for filename in sorted(glob.glob(os.path.join(IN_DIR, '*.tsv'))):
        base_file_name = os.path.basename(filename)
        process(filename, base_file_name)


if __name__ == "__main__":
    main()
    #test_convertion()