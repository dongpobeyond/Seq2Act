""" code to convert action sequence to prolog sequence for geo880 dataset"""


import os
import sys
import glob

from atisontology import AtisOntology
from atisgeneralontology import AtisGeneralOntology

IN_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action_copy\\action\\atis\\action0")
OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action_copy\\action\\atis\\seq1")


def read_examples(filename):
    examples = []
    utterance = None
    action_seq = None
    with open(filename) as f:
        for line in f:
            line = line.strip()
            #utterance, action_seq, entity_lex_str = line.rstrip('\n').split('\t')
            #examples.append((utterance, action_seq, entity_lex_str))
            utterance, action_seq = line.rstrip('\n').split('\t')
            examples.append((utterance, action_seq))
    return examples


def write(out_filename, out_data):
    out_path = os.path.join(OUT_DIR, out_filename)
    with open(out_path, "w") as f:
        for x, y in out_data:
            #print('%s\t%s' % (x, ' '.join(y)), file=f)
            print >> f, '%s\t%s' % (x, ' '.join(y))

def action2seq(action_seq, atis_controller, general_controller, entity_lex_map={}):
    action_seq = action_seq.split(' ')
    #print('action_seq: ', action_seq)
    logical_form = []
    gen_pre_action_in = ''
    gen_pre_action_class_in = 'start'
    gen_pre_arg_list_in = []
    legal_action_seq = True
    node_dict = {}
    type_node_dict = {}
    entity_node_dict = {}
    operation_dict = {}
    edge_dict = {}
    return_node = {}
    db_triple = {}
    fun_trace_list_in = []
    for action_token in action_seq:
        gen_flag, gen_pre_action_class_out, gen_pre_arg_list_out, gen_pre_action_out, fun_trace_list_out = \
            general_controller.is_legal_action_then_read(gen_pre_action_class_in, gen_pre_arg_list_in, action_token, gen_pre_action_in,
                                                         node_dict, type_node_dict, entity_node_dict, operation_dict, edge_dict, return_node,
                                                         db_triple, fun_trace_list_in, for_controller=False)

        atis_flag = atis_controller.is_legal_action(gen_pre_action_class_out, [], action_token, '', node_dict, type_node_dict, entity_node_dict,
                                                            operation_dict, edge_dict, return_node, db_triple, [], for_controller=False, entity_lex_map=entity_lex_map)

        #print('action_token = %s, gen_flag = %s, geo_flag = %s' % (action_token, gen_flag, geo_flag))
        if not gen_flag or not atis_flag:
            legal_action_seq = False
            break

        gen_pre_action_class_in = gen_pre_action_class_out
        gen_pre_arg_list_in = gen_pre_arg_list_out
        gen_pre_action_in = gen_pre_action_out
        fun_trace_list_in = fun_trace_list_out

    #print('node_dict = %s' % node_dict)
    #print('type_node_dict = %s' % type_node_dict)
    #print('entity_node_dict = %s' % entity_node_dict)
    #print('edge_dict = %s' % edge_dict)
    #print('operation_dict = %s' % operation_dict)
    #print('db_triple = %s' % db_triple)
    #print('return_node = %s' % return_node)
    #print('fun_trace_list_in = %s' % fun_trace_list_in)
    #print('*******************************************')

    if not legal_action_seq:
        logical_form = ['a']
        return logical_form

    if 'node' not in return_node:
        return_node['node'] = []

    fun_arg_map = {}
    fun_arg_map['return'] = []
    fun_arg_map['return'].append(return_node['node'])
    fun_trace_flag = {}
    fun_arg_has_argmax_or_the_map = {}
    argmax_or_the_in_fun_arg_map = {}
    argmax_or_the_operation_in_fun_arg_map = {}

    ll = len(fun_trace_list_in)
    index = 0
    pre_fun_trace = ''
    while index < ll:
        fun_trace = fun_trace_list_in[index]
        if index > 0:
            pre_fun_trace = fun_trace_list_in[index-1]
        #print('fun_trace: ', fun_trace)
        if fun_trace.startswith('add_type_node:-:'):
            type_edge = fun_trace[fun_trace.index(':-:')+3:]
            if type_edge not in db_triple:
                legal_action_seq = False
                break
            if type_edge in fun_trace_flag and fun_trace_flag[type_edge]:
                index += 1
                continue
            fun_trace_flag[type_edge] = False
            type_node = db_triple[type_edge]['arg']
            if pre_fun_trace.startswith('end_operation:-:_arg') or pre_fun_trace.startswith('end_operation:-:_the') or \
                    pre_fun_trace.startswith('end_operation:-:_max') or pre_fun_trace.startswith('end_operation:-:_min'):
                pre_operation = pre_fun_trace[pre_fun_trace.index(':-:')+3:]
                ope_node = operation_dict['core'][pre_operation]['arg1'][0]
                operation_name = 'add_operation:-:' + pre_operation
                if type_node == ope_node:
                    fun_arg_has_argmax_or_the_map[type_edge] = pre_operation
                    argmax_or_the_in_fun_arg_map[pre_operation] = type_edge
                    argmax_or_the_operation_in_fun_arg_map[operation_name] = fun_trace

        elif fun_trace.startswith('add_entity_node'):
            split1 = fun_trace.index(':-:')
            const_edge = fun_trace[split1+3:]
            if const_edge not in db_triple:
                legal_action_seq = False
                break
            if const_edge in fun_trace_flag and fun_trace_flag[const_edge]:
                index += 1
                continue
            fun_trace_flag[const_edge] = False

        elif fun_trace.startswith('add_edge:-:'):
            edge = fun_trace[fun_trace.index(':-:') + 3:]
            if edge not in db_triple:
                legal_action_seq = False
                break
            if edge in fun_trace_flag and fun_trace_flag[edge]:
                index += 1
                continue
            fun_trace_flag[edge] = False
            arg1_node = db_triple[edge]['arg1']
            arg2_node = db_triple[edge]['arg2']
            if pre_fun_trace.startswith('end_operation:-:_arg') or pre_fun_trace.startswith('end_operation:-:_the') or \
                    pre_fun_trace.startswith('end_operation:-:_max') or pre_fun_trace.startswith('end_operation:-:_min'):
                pre_operation = pre_fun_trace[pre_fun_trace.index(':-:') + 3:]
                ope_node = operation_dict['core'][pre_operation]['arg1'][0]
                operation_name = 'add_operation:-:' + pre_operation
                if arg1_node == ope_node:
                    fun_arg_has_argmax_or_the_map[edge] = (pre_operation, 'arg1')
                    argmax_or_the_operation_in_fun_arg_map[operation_name] = fun_trace
                    argmax_or_the_in_fun_arg_map[pre_operation] = edge
                if arg2_node == ope_node:
                    fun_arg_has_argmax_or_the_map[edge] = (pre_operation, 'arg2')
                    argmax_or_the_operation_in_fun_arg_map[operation_name] = fun_trace
                    argmax_or_the_in_fun_arg_map[pre_operation] = edge
        elif fun_trace.startswith('add_operation'):
            operation = fun_trace[fun_trace.index(':-:') + 3:]
            if operation not in operation_dict['core']:
                legal_action_seq = False
                break
            fun_trace_flag[operation] = False
            fun_arg_map[operation] = []
        elif fun_trace.startswith('add_compare'):
            operation = fun_trace[fun_trace.index(':-:') + 3:]
            if operation not in operation_dict['comp_core']:
                legal_action_seq = False
                break
            fun_trace_flag[operation] = False
            fun_arg_map[operation] = []
        elif fun_trace.startswith('end_operation'):
            operation_key = fun_trace[fun_trace.index(':-:') + 3:]
            operation = operation_dict['end'][operation_key]
            if 'arg0' in operation_dict['core'][operation]:
                operation_arg = operation_dict['core'][operation]['arg0']
                for fun in operation_arg:
                    fun_trace_flag[fun] = True
                    fun_arg_map[operation].append(fun)
        elif fun_trace.startswith('return'):
            pass
        else:
            legal_action_seq = False
            break
        index += 1

    fun_trace_list = []
    for fun_trace in fun_trace_list_in:
        if fun_trace in fun_trace_list:
            continue
        if fun_trace in argmax_or_the_operation_in_fun_arg_map:
            inserted_fun_trace = argmax_or_the_operation_in_fun_arg_map[fun_trace]
            fun_trace_list.append(inserted_fun_trace)
        fun_trace_list.append(fun_trace)

    index = 0
    while index < ll:
        fun_trace = fun_trace_list[index]
        #print('fun_trace: ', fun_trace)
        if fun_trace.startswith('add_type_node:-:'):
            type_edge = fun_trace[fun_trace.index(':-:')+3:]
            if fun_trace_flag[type_edge]:
                index += 1
                continue
            fun_arg_map['return'].append(type_edge)
        elif fun_trace.startswith('add_entity_node:-:'):
            split1 = fun_trace.index(':-:')
            const_edge = fun_trace[split1+3:]
            if fun_trace_flag[const_edge]:
                index += 1
                continue
            fun_arg_map['return'].append(const_edge)
        elif fun_trace.startswith('add_edge:-:'):
            edge = fun_trace[fun_trace.index(':-:')+3:]
            if fun_trace_flag[edge]:
                index += 1
                continue
            fun_arg_map['return'].append(edge)
        elif fun_trace.startswith('add_operation'):
            operation = fun_trace[fun_trace.index(':-:')+3:]
            if fun_trace_flag[operation] or fun_trace in argmax_or_the_operation_in_fun_arg_map:
                index += 1
                continue
            fun_arg_map['return'].append(operation)
        elif fun_trace.startswith('add_the_node:-:'):
            the_node = fun_trace[fun_trace.index(':-:')+3:]
            if fun_trace_flag[the_node]:
                index += 1
                continue
            fun_arg_map['return'].append(the_node)
        elif fun_trace.startswith('add_compare'):
            compare_name = fun_trace[fun_trace.index(':-:')+3:]
            if fun_trace_flag[compare_name]:
                index += 1
                continue
            fun_arg_map['return'].append(compare_name)
        else:
            pass

        index += 1

    #print('fun_arg_map = %s' % fun_arg_map)
    #print('fun_arg_has_argmax_or_the_map = %s' % fun_arg_has_argmax_or_the_map)
    #print('argmax_or_the_in_fun_arg_map = %s' % argmax_or_the_in_fun_arg_map)
    #print('fun_trace_list = %s' % fun_trace_list)
    key = 'return'
    build_seq(key, fun_arg_map, entity_node_dict, operation_dict, db_triple,
              fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)

    if not legal_action_seq:
        logical_form = ['b']

    if len(fun_trace_list_in) == 0 and len(entity_node_dict) == 1:
        for entity in entity_node_dict:
            logical_form = [entity]

    return logical_form

def build_seq(fun, fun_arg_map, entity_node_dict, operation_dict, db_triple,
              fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form):
    fun_name = fun[:fun.index(':_:')] if ':_:' in fun else fun
    #print('fun in build_seq: %s, fun_name = %s' % (fun, fun_name))
    if fun == 'return':
        return_node_count = 0
        for node in reversed(fun_arg_map[fun][0]):
            if len(node) > 1 and node[1].isdigit():
                logical_form.append('(')
                logical_form.append('_lambda')
                logical_form.append(node)
                logical_form.append('e')
                return_node_count += 1
            else:
                node_entity = node
                if node.startswith('$'):
                    for entity in entity_node_dict:
                        if not entity.startswith('_const:'):
                            continue
                        if 'arg1' not in entity_node_dict[entity] or 'arg2' not in entity_node_dict[entity]:
                            continue
                        if node == entity_node_dict[entity]['arg1']:
                            node_entity = entity_node_dict[entity]['arg2']
                        elif node == entity_node_dict[entity]['arg2']:
                            node_entity = entity_node_dict[entity]['arg1']
                logical_form.append(node_entity)
        for ii in range(1,len(fun_arg_map[fun])):
            build_seq(fun_arg_map[fun][ii], fun_arg_map, entity_node_dict, operation_dict, db_triple,
                        fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)
        for i in range(return_node_count):
            logical_form.append(')')
    elif fun_name == '_count' or fun_name == '_max' or fun_name == '_min':
        logical_form.append('(')
        logical_form.append(fun_name)
        ope_for = operation_dict['core'][fun]['arg1'][0]
        logical_form.append(ope_for)
        for ii in range(len(fun_arg_map[fun])):
            if fun_arg_map[fun][ii] in argmax_or_the_in_fun_arg_map:
                continue
            build_seq(fun_arg_map[fun][ii], fun_arg_map, entity_node_dict, operation_dict, db_triple,
                      fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)
        logical_form.append(')')
    elif fun_name == '_sum':
        logical_form.append('(')
        logical_form.append('_sum')
        ope_for = operation_dict['core'][fun]['arg1'][0]
        logical_form.append(ope_for)
        for ii in range(len(fun_arg_map[fun])):
            if fun_arg_map[fun][ii] in argmax_or_the_in_fun_arg_map:
                continue
            build_seq(fun_arg_map[fun][ii], fun_arg_map, entity_node_dict, operation_dict, db_triple,
                      fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)
        logical_form.append(')')

    elif fun_name == '_argmax' or fun_name == '_argmin':
        logical_form.append('(')
        logical_form.append(fun_name)
        ope_for = operation_dict['core'][fun]['arg1'][0]
        logical_form.append(ope_for)
        for ii in range(len(fun_arg_map[fun])):
            if fun_arg_map[fun][ii] in argmax_or_the_in_fun_arg_map:
                continue
            build_seq(fun_arg_map[fun][ii], fun_arg_map, entity_node_dict, operation_dict, db_triple,
                      fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)
        logical_form.append(')')

    elif fun_name == '_not' or fun_name == '_and' or fun_name == '_or':
        logical_form.append('(')
        logical_form.append(fun_name)
        for ii in range(len(fun_arg_map[fun])):
            if fun_arg_map[fun][ii] in argmax_or_the_in_fun_arg_map:
                continue
            build_seq(fun_arg_map[fun][ii], fun_arg_map, entity_node_dict, operation_dict, db_triple,
                      fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)
        logical_form.append(')')

    elif fun_name == '_=' or fun_name == '_>' or fun_name == '_<':
        logical_form.append('(')
        logical_form.append(fun_name)
        for ii in range(len(fun_arg_map[fun])):
            if fun_arg_map[fun][ii] in argmax_or_the_in_fun_arg_map:
                continue
            build_seq(fun_arg_map[fun][ii], fun_arg_map, entity_node_dict, operation_dict, db_triple,
                      fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)
        if 'arg1' in operation_dict['core'][fun]:
            ope_arg = operation_dict['core'][fun]['arg1'][0]
            arg_entity = ope_arg
            if ope_arg.startswith('$'):
                for entity in entity_node_dict:
                    if not entity.startswith('_const:'):
                        continue
                    if 'arg1' not in entity_node_dict[entity] or 'arg2' not in entity_node_dict[entity]:
                        continue
                    if ope_arg == entity_node_dict[entity]['arg1']:
                        arg_entity = entity_node_dict[entity]['arg2']
                    elif ope_arg == entity_node_dict[entity]['arg2']:
                        arg_entity = entity_node_dict[entity]['arg1']
            logical_form.append(arg_entity)
        logical_form.append(')')

    elif fun_name == '_the':
        logical_form.append('(')
        logical_form.append(fun_name)
        ope_arg = operation_dict['core'][fun]['arg1'][0]
        if ope_arg.startswith('$'):
            logical_form.append(ope_arg)
        for ii in range(len(fun_arg_map[fun])):
            if fun_arg_map[fun][ii] in argmax_or_the_in_fun_arg_map:
                continue
            build_seq(fun_arg_map[fun][ii], fun_arg_map, entity_node_dict, operation_dict, db_triple,
                      fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)
        logical_form.append(')')
    elif fun_name == '_exists':
        logical_form.append('(')
        logical_form.append(fun_name)
        ope_for = operation_dict['core'][fun]['arg1'][0]
        logical_form.append(ope_for)

        for ii in range(len(fun_arg_map[fun])):
            if fun_arg_map[fun][ii] in argmax_or_the_in_fun_arg_map:
                continue
            build_seq(fun_arg_map[fun][ii], fun_arg_map, entity_node_dict, operation_dict, db_triple,
                      fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)

        logical_form.append(')')

    elif fun_name == '_equals' or fun_name == '_equals:_t':
        logical_form.append('(')
        logical_form.append(fun_name)
        const_count = 0
        for arg_fun in fun_arg_map[fun]:
            if arg_fun.startswith('_const'):
                const_count += 1
        arg_add_len = 2 - len(fun_arg_map[fun]) + const_count
        arg_add_num = 0
        if 'arg00' in operation_dict['core'][fun]:
            arg_list = operation_dict['core'][fun]['arg00']
            if len(fun_arg_map[fun]) - const_count == 1:
                arg_list = reversed(arg_list)
            for arg in arg_list:
                if arg_add_num < arg_add_len:
                    arg_entity = arg
                    if arg.startswith('$'):
                        for entity in entity_node_dict:
                            if not entity.startswith('_const:'):
                                continue
                            if 'arg1' not in entity_node_dict[entity] or 'arg2' not in entity_node_dict[entity]:
                                continue
                            if arg == entity_node_dict[entity]['arg1']:
                                arg_entity = entity_node_dict[entity]['arg2']
                            elif arg == entity_node_dict[entity]['arg2']:
                                arg_entity = entity_node_dict[entity]['arg1']
                    logical_form.append(arg_entity)
                    arg_add_num += 1
                else:
                    break
        for ii in range(len(fun_arg_map[fun])):
            if fun_arg_map[fun][ii] in argmax_or_the_in_fun_arg_map:
                continue
            build_seq(fun_arg_map[fun][ii], fun_arg_map, entity_node_dict, operation_dict, db_triple,
                      fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)
        logical_form.append(')')

    elif fun.startswith('_const'):
        pass

    elif fun.startswith('TYPE'):
        logical_form.append('(')
        entity_type = fun[4:fun.index(':_:')]
        logical_form.append(entity_type)
        arg = db_triple[fun]['arg']
        if fun in fun_arg_has_argmax_or_the_map:
            arg_fun = fun_arg_has_argmax_or_the_map[fun]
            build_seq(arg_fun, fun_arg_map, entity_node_dict, operation_dict, db_triple,
                      fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)
        else:
            arg_entity = arg
            if arg.startswith('$'):
                for entity in entity_node_dict:
                    if not entity.startswith('_const:'):
                        continue
                    if 'arg1' not in entity_node_dict[entity] or 'arg2' not in entity_node_dict[entity]:
                        continue
                    if arg == entity_node_dict[entity]['arg1']:
                        arg_entity = entity_node_dict[entity]['arg2']
                    elif arg == entity_node_dict[entity]['arg2']:
                        arg_entity = entity_node_dict[entity]['arg1']
            logical_form.append(arg_entity)

        logical_form.append(')')

    else:
        arg1 = db_triple[fun]['arg1']
        arg2 = db_triple[fun]['arg2']
        arg1_entity = arg1
        arg2_entity = arg2

        for entity in entity_node_dict:
            if not entity.startswith('_const:'):
                continue
            if 'arg1' not in entity_node_dict[entity] or 'arg2' not in entity_node_dict[entity]:
                continue
            if arg1.startswith('$'):
                if arg1 == entity_node_dict[entity]['arg1']:
                    arg1_entity = entity_node_dict[entity]['arg2']
                elif arg1 == entity_node_dict[entity]['arg2']:
                    arg1_entity = entity_node_dict[entity]['arg1']
            if arg2.startswith('$'):
                if arg2 == entity_node_dict[entity]['arg1']:
                    arg2_entity = entity_node_dict[entity]['arg2']
                elif arg2 == entity_node_dict[entity]['arg2']:
                    arg2_entity = entity_node_dict[entity]['arg1']

        logical_form.append('(')
        edge = fun[:fun.index(':_:')]
        logical_form.append(edge)
        if fun in fun_arg_has_argmax_or_the_map:
            arg_fun, arg_position = fun_arg_has_argmax_or_the_map[fun]
            if arg_position == 'arg1':
                build_seq(arg_fun, fun_arg_map, entity_node_dict, operation_dict, db_triple,
                          fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)
                logical_form.append(arg2_entity)
            else:
                logical_form.append(arg1_entity)
                build_seq(arg_fun, fun_arg_map, entity_node_dict, operation_dict, db_triple,
                          fun_arg_has_argmax_or_the_map, argmax_or_the_in_fun_arg_map, logical_form)

        else:
            logical_form.append(arg1_entity)
            logical_form.append(arg2_entity)
        logical_form.append(')')


def process(filename, base_file_name, geo_controller, general_controller):
    in_data = read_examples(filename)
    out_data = []
    #for (utterance, action_seq, entity_lex_str) in in_data:
    for (utterance, action_seq) in in_data:
        print('*********************************************')
        print('utterance: ' + utterance)
        entity_lex_str = ''
        entity_lex = {}
        if not entity_lex_str == '':
            entity_lex_items = entity_lex_str.split(' ')
            for entity_lex_item in entity_lex_items:
                parts = entity_lex_item.split(':::')
                entity = parts[0]
                entity_name = parts[1]
                entity_lex[entity] = entity_name
        #print('action_seq: ' + action_seq)
        y = action2seq(action_seq, geo_controller, general_controller, entity_lex_map=entity_lex)
        print('logical_form: ' + ' '.join(y))
        out_data.append((utterance, y))
    write(base_file_name, out_data)


def test(geo_controller, general_controller):
    action_seq = 'add_operation:-:_exists add_operation:-:_and add_node:-:$1 add_type_node:-:_flight arg_node:-:$1 add_node:-:$A add_entity_node:-:ent0:_ap arg_node:-:$A add_edge:-:_from_airport arg_node:-:$1 arg_node:-:$A add_edge:-:_to_city arg_node:-:$1 arg_node:-:$A add_edge:-:_to_city arg_node:-:$1 arg_node:-:$A add_operation:-:_= add_type_node:-:_aircraft_code arg_node:-:$1 add_node:-:$0 end_operation:-:_= ope_arg:-:$0 end_operation:-:_and add_operation:-:_equals ope_for:-:$1 end_action:-:end'
    print('actions: ' + action_seq)
    entity_lex = {'mke:_ap':'ent0:_ap'}
    #print('len = ' + str(len(action_seq.split(' '))))
    lf = action2seq(action_seq, geo_controller, general_controller, entity_lex_map=entity_lex)
    print('logical_form: ' + ' '.join(lf))
    #print('len = ' + str(len(lf)))

def test_legal(general_controller):
    action_seq = 'add_operation:-:_equals ope_for:-:$0 ope_for:-:$0 end_operation:-:_equals end_action:-:end'
    print('action: ' + action_seq)
    legal_flag_test, legal_flag = general_controller.is_legal_action_seq(action_seq.split(' '))
    print('legal_flag_test: ', legal_flag_test)
    print('legal_flag: ', legal_flag)

def main(geo_controller, general_controller):
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
    for filename in sorted(glob.glob(os.path.join(IN_DIR, '*.tsv'))):
        base_file_name = os.path.basename(filename)
        process(filename, base_file_name, geo_controller, general_controller)

if __name__ == "__main__":
    atis_grammar_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "seq2action_copy\\ontology\\atis.grammar")
    general_grammar_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "seq2action_copy\\ontology\\atis-general.grammar")
    atis_controller = AtisOntology(atis_grammar_file, False)
    general_controller = AtisGeneralOntology(general_grammar_file, True)
    main(atis_controller, general_controller)
    #test(atis_controller, general_controller)
    #test_legal(general_controller)