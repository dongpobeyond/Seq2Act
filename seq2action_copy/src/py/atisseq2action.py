""" code to convert geo sequence to action sequence"""

import os
import glob
import sys
import re

IN_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action_copy\\action\\atis\\seq0")
OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action_copy\\action\\atis\\action0")

unary_map = {}
binary_map = {}
entity_map = {}

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
            if base_file_name == 'atis_train.tsv':
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
            print('%s\t%s' % (x, ' '.join(y)), file=f)
            #print >> f, '%s\t%s' % (x, ' '.join(y))
            if out_filename == 'atis_train.tsv':
                count += 1
                len_all += len(y)
    if count != 0:
        print('************** action ********************')
        print('count = ' + str(count) + ', average_len = ' + str(len_all/count))
        print('********************************************')


def seq2action(logical_form):
    ope_fun_type_all = ['ARG', 'COUNT', 'NOT', 'SUM', 'MAX', 'OR', 'COMP', 'EXIST', 'EQUAL', 'AND', 'THE']
    node_prefix = 'add_node:-:'
    entity_node_prefix = 'add_entity_node:-:'
    edge_prefix = 'add_edge:-:'
    type_node_prefix = 'add_type_node:-:'
    operation_prefix = 'add_operation:-:'
    operation_end_prefix = 'end_operation:-:'
    operation_for_prefix = 'ope_for:-:'
    return_prefix = 'return:-:'
    end_signal_action = 'end_action:-:end'
    operation_arg_prefix = 'ope_arg:-:'

    left_num_paren = 0
    right_num_paren = 0

    arg_node_prefix = 'arg_node:-:'

    act_seq = []
    fun_stack = []
    fun_trace = []
    cur_fun_index = ''
    entity = ''
    entity_type = ''
    argument_stack_map = {}
    fun_position_map = {}
    fun_left_paren_map = {}
    fun_type_map = {}
    fun_ope_map = {}
    fun_comp_map = {}
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
        else:
            cur_fun_index = '_root:-:0'
        index += 1

        if lf_token == '(':
            left_num_paren += 1
            continue

        elif lf_token == ')':
            right_num_paren += 1
            if len(fun_stack) == 0:
                continue
            fun_with_index_from_stack = fun_stack.pop()
            fun_trace.append(fun_with_index_from_stack)
            fun_from_stack = fun_with_index_from_stack[:fun_with_index_from_stack.index('::')]
            fun_position_map[fun_with_index_from_stack] = left_num_paren - right_num_paren

            print('fun_from_stack = %s' % fun_from_stack)

            if fun_from_stack == '_lambda':
                fun_type_map[cur_fun_index] = 'LAMBDA'
            elif fun_from_stack == '_and':
                fun_type_map[cur_fun_index] = 'AND'
            elif fun_from_stack == '_or':
                fun_type_map[cur_fun_index] = 'OR'
            elif fun_from_stack == '_argmax' or fun_from_stack == '_argmin':
                fun_type_map[cur_fun_index] = 'ARG'
            elif fun_from_stack == '_max' or fun_from_stack == '_min':
                fun_type_map[cur_fun_index] = 'MAX'
            elif fun_from_stack == '_>' or fun_from_stack == '_<' or fun_from_stack == '_=':
                fun_type_map[cur_fun_index] = 'COMP'
            elif fun_from_stack == '_equals' or fun_from_stack == '_equals:_t':
                fun_type_map[cur_fun_index] = 'EQUAL'
            elif fun_from_stack == '_the':
                fun_type_map[cur_fun_index] = 'THE'
            elif fun_from_stack == '_exists':
                fun_type_map[cur_fun_index] = 'EXIST'
            elif fun_from_stack == '_not':
                fun_type_map[cur_fun_index] = 'NOT'
            elif fun_from_stack == '_count':
                fun_type_map[cur_fun_index] = 'COUNT'
            elif fun_from_stack == '_sum':
                fun_type_map[cur_fun_index] = 'SUM'
            elif len(argument_stack_map[fun_with_index_from_stack]) == 1:
                fun_type_map[cur_fun_index] = 'UNARY'
            elif len(argument_stack_map[fun_with_index_from_stack]) == 2:
                fun_type_map[cur_fun_index] = 'BINARY'
            else:
                fun_type_map[cur_fun_index] = 'TODO FUN TYPE'
                print('todo fun type for %s' % cur_fun_index)

        elif lf_token.startswith('$'):
            var_id = lf_token
            argument_stack_map[cur_fun_index].append('node:-:' + var_id)
            node_id_stack.append(var_id)

        elif lf_token.startswith('_'):
            lf_token_index = lf_token + '::' + str(index)
            if len(fun_stack) > 0:
                fun_pre = fun_stack[-1]
                argument_stack_map[fun_pre].append('fun:-:' + lf_token_index)
            fun_stack.append(lf_token_index)
            argument_stack_map[lf_token_index] = []
            fun_left_paren_map[lf_token_index] = left_num_paren

        elif not lf_token == 'e' and not lf_token == 'i':
            entity = lf_token
            if cur_fun_index not in argument_stack_map:
                argument_stack_map[cur_fun_index] = []
            argument_stack_map[cur_fun_index].append('entity:-:' + entity)
            if entity not in entity_map:
                entity_map[entity] = []


    node_in_actions = set()
    fun_name_map = {}
    cur_character_int = ord('A')
    entity_character_map = {}

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
        argument_from_fun_stack = argument_stack_map[fun_with_index_from_stack]
        ope_fun_list = []
        if fun_with_index_from_stack in fun_ope_map:
            ope_fun_list = fun_ope_map[fun_with_index_from_stack]
        print('index = ', index, ', fun = ' + fun_with_index_from_stack + ', fun_type = ' + fun_type_map[fun_with_index_from_stack] + \
            ', position = ' + str(fun_position_map[fun_with_index_from_stack]) + ', argument = [ ' + ' '.join(argument_from_fun_stack) + ' ]' + \
              ', ope_fun = ' + ' '.join(ope_fun_list))
        index += 1

    for fun_with_index_from_stack in fun_trace:
        #print('fun_with_index_from_stack: %s' % fun_with_index_from_stack)
        #print('act_seq: %s' % ' '.join(act_seq))
        fun_from_stack = fun_with_index_from_stack[:fun_with_index_from_stack.index('::')]
        fun_type = fun_type_map[fun_with_index_from_stack]
        argument_list = argument_stack_map[fun_with_index_from_stack]

        if fun_type == 'UNARY':
            argument = argument_list[0]
            if argument.startswith('node:-:'):
                node_id = argument[7:]
            elif argument.startswith('entity:-:'):
                node_id = argument[9:]
            elif argument.startswith('fun:-:'):
                node_id = ''
            else:
                print('Unary Error: unary = %s, argument = %s' % (fun_from_stack, argument))
                break

            for ope_fun in fun_ope_map[fun_with_index_from_stack]:
                if ope_fun_flag_map[ope_fun]:
                    ope_name = ope_fun[:ope_fun.index('::')]
                    ope_action = operation_prefix + ope_name
                    act_seq.append(ope_action)
                    ope_fun_flag_map[ope_fun] = False
                    if fun_type_map[ope_fun] == 'EQUAL':
                        equal_arg_list = argument_stack_map[ope_fun]
                        for equal_arg in equal_arg_list:
                            if equal_arg.startswith('node:-:'):
                                equal_arg_node_id = equal_arg[7:]
                                if equal_arg_node_id in node_in_actions:
                                    act_seq.append(arg_node_prefix + equal_arg_node_id)

            if not node_id == '' and node_id not in node_in_actions:
                if node_id.startswith('$'):
                    add_node_action = node_prefix + node_id
                    node_in_actions.add(node_id)
                    act_seq.append(add_node_action)
                elif ':' in node_id:
                    if node_id not in entity_character_map:
                        entity_character = '$' + chr(cur_character_int)
                        cur_character_int += 1
                        entity_character_map[node_id] = entity_character
                        node_in_actions.add(entity_character)
                        add_node_action = node_prefix + entity_character
                        act_seq.append(add_node_action)
                        add_entity_node_action = entity_node_prefix + node_id
                        act_seq.append(add_entity_node_action)
                        act_seq.append(arg_node_prefix + entity_character)
                else:
                    print('something wrong for node1_id in unary: %s' % node_id)
                    break
            else:
                pass

            add_type_node_action = type_node_prefix + fun_from_stack
            act_seq.append(add_type_node_action)
            if node_id == '':
                arg_fun_name = argument[argument.index(':-:') + 3:]
                if arg_fun_name not in argument_stack_map:
                    print('wrong fun arg for unary! arg_fun_name = %s' % arg_fun_name)
                    break
                arg_node_raw = argument_stack_map[arg_fun_name][0]
                if not arg_node_raw.startswith('node:-:'):
                    print('wrong arg node for unary! arg_node_raw = %s' % arg_node_raw)
                    break
                node_id = arg_node_raw[arg_node_raw.index(':-:') + 3:]

            if node_id in entity_character_map:
                node_id = entity_character_map[node_id]
            act_seq.append(arg_node_prefix + node_id)

            unary = fun_from_stack
            if unary not in unary_map:
                unary_map[unary] = []

        elif fun_type == 'BINARY':
            arg1 = argument_list[0]
            arg2 = argument_list[1]

            if arg1.startswith('node:-:'):
                node1_id = arg1[7:]
            elif arg1.startswith('entity:-:'):
                node1_id = arg1[9:]
            elif arg1.startswith('fun:-:'):
                node1_id = ''
            else:
                print('Binary arg1 Error: ' + arg1)
                break
            if arg2.startswith('node:-:'):
                node2_id = arg2[7:]
            elif arg2.startswith('entity:-:'):
                node2_id = arg2[9:]
            elif arg2.startswith('fun:-:'):
                node2_id = ''
            else:
                print('Binary arg2 Error: ' + arg2)
                break

            for ope_fun in fun_ope_map[fun_with_index_from_stack]:
                if ope_fun_flag_map[ope_fun]:
                    ope_name = ope_fun[:ope_fun.index('::')]
                    ope_action = operation_prefix + ope_name
                    act_seq.append(ope_action)
                    ope_fun_flag_map[ope_fun] = False
                    if fun_type_map[ope_fun] == 'EQUAL':
                        equal_arg_list = argument_stack_map[ope_fun]
                        for equal_arg in equal_arg_list:
                            if equal_arg.startswith('node:-:'):
                                equal_arg_node_id = equal_arg[7:]
                                if equal_arg_node_id in node_in_actions:
                                    act_seq.append(arg_node_prefix + equal_arg_node_id)

            if not node1_id == '' and node1_id not in node_in_actions:
                if node1_id.startswith('$'):
                    add_node_action = node_prefix + node1_id
                    node_in_actions.add(node1_id)
                    act_seq.append(add_node_action)
                elif ':' in node1_id:
                    if node1_id not in entity_character_map:
                        entity_character = '$' + chr(cur_character_int)
                        cur_character_int += 1
                        entity_character_map[node1_id] = entity_character
                        node_in_actions.add(entity_character)
                        add_node_action = node_prefix + entity_character
                        act_seq.append(add_node_action)
                        add_entity_node_action = entity_node_prefix + node1_id
                        act_seq.append(add_entity_node_action)
                        act_seq.append(arg_node_prefix + entity_character)
                else:
                    print('something wrong for node1_id in binary: %s' % node1_id)
                    break

            if node1_id == '':
                arg_fun_name = arg1[arg1.index(':-:') + 3:]
                if arg_fun_name not in argument_stack_map:
                    print('wrong fun arg for binary arg1! arg_fun_name = %s' % arg_fun_name)
                    break
                arg_node_raw = argument_stack_map[arg_fun_name][0]
                if not arg_node_raw.startswith('node:-:'):
                    print('wrong arg node for binary arg1! arg_node_raw = %s' % arg_node_raw)
                    break
                node1_id = arg_node_raw[arg_node_raw.index(':-:') + 3:]

            if not node2_id == '' and node2_id not in node_in_actions:
                if node2_id.startswith('$'):
                    add_node_action = node_prefix + node2_id
                    node_in_actions.add(node2_id)
                    act_seq.append(add_node_action)
                elif ':' in node2_id:
                    if node2_id not in entity_character_map:
                        entity_character = '$' + chr(cur_character_int)
                        cur_character_int += 1
                        entity_character_map[node2_id] = entity_character
                        node_in_actions.add(entity_character)
                        add_node_action = node_prefix + entity_character
                        act_seq.append(add_node_action)
                        add_entity_node_action = entity_node_prefix + node2_id
                        act_seq.append(add_entity_node_action)
                        act_seq.append(arg_node_prefix + entity_character)
                else:
                    print('something wrong for node2_id in binary: %s' % node2_id)
                    break

            if node2_id == '':
                arg_fun_name = arg2[arg2.index(':-:') + 3:]
                if arg_fun_name not in argument_stack_map:
                    print('wrong fun arg for binary arg2! arg_fun_name = %s' % arg_fun_name)
                    break
                arg_node_raw = argument_stack_map[arg_fun_name][0]
                if not arg_node_raw.startswith('node:-:'):
                    print('wrong arg node for binary arg2! arg_node_raw = %s' % arg_node_raw)
                    break
                node2_id = arg_node_raw[arg_node_raw.index(':-:') + 3:]

            add_edge_action = edge_prefix + fun_from_stack
            act_seq.append(add_edge_action)
            if node1_id in entity_character_map:
                node1_id = entity_character_map[node1_id]
            if node2_id in entity_character_map:
                node2_id = entity_character_map[node2_id]
            act_seq.append(arg_node_prefix + node1_id)
            act_seq.append(arg_node_prefix + node2_id)

            binary = fun_from_stack
            if binary not in binary_map:
                binary_map[binary] = []

        elif fun_type == 'OR' or fun_type == 'AND':
            ope_end_action = operation_end_prefix + fun_from_stack
            act_seq.append(ope_end_action)

        elif fun_type == 'THE':
            arg1 = argument_list[0]
            if arg1.startswith('node:-:'):
                node1_id = arg1[7:]
            else:
                print('The arg1 Error: ' + arg1)
                break
            the_end_action = operation_end_prefix + fun_from_stack
            act_seq.append(the_end_action)
            act_seq.append(operation_arg_prefix + node1_id)

        elif fun_type == 'COMP':
            for node_id_raw in argument_list:
                node_id = node_id_raw[node_id_raw.index(':-:')+3:]
                if not node_id_raw.startswith('fun:-:') and node_id not in node_in_actions:
                    if node_id_raw.startswith('node:-:'):
                        add_node_action = node_prefix + node_id
                        node_in_actions.add(node_id)
                        act_seq.append(add_node_action)
                    elif ':' in node_id:
                        if node_id not in entity_character_map:
                            entity_character = '$' + chr(cur_character_int)
                            cur_character_int += 1
                            entity_character_map[node_id] = entity_character
                            node_in_actions.add(entity_character)
                            add_node_action = node_prefix + entity_character
                            act_seq.append(add_node_action)
                            add_entity_node_action = entity_node_prefix + node_id
                            act_seq.append(add_entity_node_action)
                            act_seq.append(arg_node_prefix + entity_character)
            comp_end_action = operation_end_prefix + fun_from_stack
            act_seq.append(comp_end_action)
            for node_id_raw in argument_list:
                node_id = node_id_raw[node_id_raw.index(':-:')+3:]
                if not node_id_raw.startswith('fun:-:'):
                    if node_id not in entity_character_map:
                        act_seq.append(operation_arg_prefix + node_id)
                    else:
                        entity_character = entity_character_map[node_id]
                        act_seq.append(operation_arg_prefix + entity_character)

        elif fun_type == 'EXIST':
            arg1 = argument_list[0]
            if arg1.startswith('node:-:'):
                node1_id = arg1[7:]
            else:
                print('Exist arg1 Error: ' + arg1)
                break
            exist_end_action = operation_end_prefix + fun_from_stack
            act_seq.append(exist_end_action)
            act_seq.append(operation_for_prefix + node1_id)

        elif fun_type == 'EQUAL':
            if fun_with_index_from_stack in fun_ope_map:
                for ope_fun in fun_ope_map[fun_with_index_from_stack]:
                    if ope_fun_flag_map[ope_fun]:
                        ope_name = ope_fun[:ope_fun.index('::')]
                        ope_action = operation_prefix + ope_name
                        act_seq.append(ope_action)
                        ope_fun_flag_map[ope_fun] = False
                        if fun_type_map[ope_fun] == 'EQUAL':
                            equal_arg_list = argument_stack_map[ope_fun]
                            for equal_arg in equal_arg_list:
                                if equal_arg.startswith('node:-:'):
                                    equal_arg_node_id = equal_arg[7:]
                                    if equal_arg_node_id in node_in_actions:
                                        act_seq.append(arg_node_prefix + equal_arg_node_id)

            if fun_with_index_from_stack in ope_fun_flag_map and ope_fun_flag_map[fun_with_index_from_stack]:
                ope_name = fun_from_stack
                ope_action = operation_prefix + ope_name
                act_seq.append(ope_action)

            arg1 = argument_list[0]
            arg2 = argument_list[1]
            if arg1.startswith('node:-:'):
                node1_id = arg1[7:]
            elif arg1.startswith('entity:-:'):
                node1_id = arg1[9:]
            elif arg1.startswith('fun:-:'):
                node1_id = ''
            else:
                print('Equal arg1 Error: ' + arg1)
                break
            if arg2.startswith('node:-:'):
                node2_id = arg2[7:]
            elif arg2.startswith('entity:-:'):
                node2_id = arg2[9:]
            elif arg2.startswith('fun:-:'):
                node2_id = ''
            else:
                print('Equal arg2 Error: ' + arg2)
                break
            if not node1_id == '' and node1_id not in node_in_actions:
                if node1_id.startswith('$'):
                    add_node_action = node_prefix + node1_id
                    node_in_actions.add(node1_id)
                    act_seq.append(add_node_action)
                elif ':' in node1_id:
                    if node1_id not in entity_character_map:
                        entity_character = '$' + chr(cur_character_int)
                        cur_character_int += 1
                        entity_character_map[node1_id] = entity_character
                        node_in_actions.add(entity_character)
                        add_node_action = node_prefix + entity_character
                        act_seq.append(add_node_action)
                        add_entity_node_action = entity_node_prefix + node1_id
                        act_seq.append(add_entity_node_action)
                        act_seq.append(arg_node_prefix + entity_character)
                else:
                    print('something wrong for node1_id in equal: %s' % node1_id)
                    break
            elif not node1_id == '' and len(act_seq) > 0 and act_seq[-1].startswith('add_operation:-:_equal'):
                if node1_id in entity_character_map:
                    node1_id = entity_character_map[node1_id]
                act_seq.append(arg_node_prefix + node1_id)

            if not node2_id == '' and node2_id not in node_in_actions:
                if node2_id.startswith('$'):
                    add_node_action = node_prefix + node2_id
                    node_in_actions.add(node2_id)
                    act_seq.append(add_node_action)
                elif ':' in node2_id:
                    if node2_id not in entity_character_map:
                        entity_character = '$' + chr(cur_character_int)
                        cur_character_int += 1
                        entity_character_map[node2_id] = entity_character
                        node_in_actions.add(entity_character)
                        add_node_action = node_prefix + entity_character
                        act_seq.append(add_node_action)
                        add_entity_node_action = entity_node_prefix + node2_id
                        act_seq.append(add_entity_node_action)
                        act_seq.append(arg_node_prefix + entity_character)
                else:
                    print('something wrong for node2_id in equal: %s' % node2_id)
                    break
            elif not node2_id == '' and len(act_seq) > 0 and act_seq[-1].startswith('add_operation:-:_equal'):
                if node2_id in entity_character_map:
                    node2_id = entity_character_map[node2_id]
                act_seq.append(arg_node_prefix + node2_id)

            end_equal_action = operation_end_prefix + fun_from_stack
            act_seq.append(end_equal_action)

        elif fun_type == 'MAX':
            max_end_action = operation_end_prefix + fun_from_stack
            act_seq.append(max_end_action)
            arg_for = argument_list[0][7:]
            ope_for_action = operation_for_prefix + arg_for
            act_seq.append(ope_for_action)

        elif fun_type == 'ARG':
            ope_end_action = operation_end_prefix + fun_from_stack
            act_seq.append(ope_end_action)
            ope_for = argument_list[0][7:]
            ope_for_action = operation_for_prefix + ope_for
            act_seq.append(ope_for_action)

        elif fun_type == 'SUM':
            ope_end_action = operation_end_prefix + fun_from_stack
            act_seq.append(ope_end_action)
            sum_for = argument_list[0][7:]
            sum_for_action = operation_for_prefix + sum_for
            act_seq.append(sum_for_action)

        elif fun_type == 'COUNT':
            ope_end_action = operation_end_prefix + fun_from_stack
            act_seq.append(ope_end_action)
            count_for = argument_list[0][7:]
            count_for_action = operation_for_prefix + count_for
            act_seq.append(count_for_action)

        elif fun_type == 'NOT':
            ope_end_action = operation_end_prefix + '_not'
            act_seq.append(ope_end_action)
            fun_name_map[fun_with_index_from_stack] = '_not'

        elif fun_type == 'LAMBDA':
            argument = argument_list[0]
            if argument.startswith('node:-:'):
                return_action = return_prefix + argument[7:]
                act_seq.append(return_action)
        else:
            print('TODO: ' + fun_type)

    if len(fun_trace) == 0 and '_root:-:0' in argument_stack_map and len(argument_stack_map['_root:-:0']) == 1:
        entity_raw = argument_stack_map['_root:-:0'][0]
        entity = entity_raw[entity_raw.index(':-:')+3:]
        if entity not in entity_character_map:
            entity_character = '$' + chr(cur_character_int)
            cur_character_int += 1
            entity_character_map[entity] = entity_character
            node_in_actions.add(entity_character)
            add_node_action = node_prefix + entity_character
            act_seq.append(add_node_action)
            add_entity_node_action = entity_node_prefix + entity
            act_seq.append(add_entity_node_action)
            act_seq.append(arg_node_prefix + entity_character)
            act_seq.append(return_prefix + entity_character)
    act_seq.append(end_signal_action)

    #print('####### argument_stack_map ##########')
    #print(argument_stack_map)
    #print('####### fun_argument_map ##########')
    #print(fun_argument_map)
    return act_seq

def write_grammar(entity_map, unary_map, binary_map):
    file_name = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "seq2action_entity\\ontology\\atis-raw.grammar")

    entity_type_set = set()
    for entity in entity_map:
        entity_type = entity[entity.index(':_')+2:]
        entity_type_set.add(entity_type)

    with open(file_name, 'w') as f:
        for entity in entity_type_set:
            print('entity:\t%s' % entity, file=f)
        for unary in unary_map:
            print('unary:\t%s' % unary, file=f)
        for binary in binary_map:
            print('binary:\ttype:flight\t%s\ttype:' % binary, file=f)

def test_convertion():
    lf = '( _lambda $0 e ( _and ( _flight $0 ) ( _from $0 denver:_ci ) ( _or ( _to $0 baltimore:_ci ) ( _to $0 washington:_ci ) ) ( _or ( _approx_arrival_time $0 1200:_ti ) ( _< ( _arrival_time $0 ) 1200:_ti ) ) ) )'
    print(lf)
    print('len = ' + str(len(lf.split(' '))))
    actions = seq2action(lf)
    print('actions: ' + ' '.join(actions))
    ii = 0
    jj = ii + 1
    print('----------------------------------------------')
    while ii < len(actions):
        while jj < len(actions) and not actions[jj].startswith('add') and not actions[jj].startswith('return')\
                and not actions[jj].startswith('end_operation') and not actions[jj].startswith('end_action'):
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
    #write_grammar(entity_map, unary_map, binary_map)


def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
    for filename in sorted(glob.glob(os.path.join(IN_DIR, '*.tsv'))):
        base_file_name = os.path.basename(filename)
        process(filename, base_file_name)


if __name__ == "__main__":
    main()
    test_convertion()