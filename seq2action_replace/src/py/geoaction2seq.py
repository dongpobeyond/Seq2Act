""" code to convert action sequence to prolog sequence for geo880 dataset"""


import os
import sys
import glob

from geoontology import GeoOntology
from generalontology import GeneralOntology

IN_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action_entity\\action\\geo880\\action0")
OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action_entity\\action\\geo880\\seq1")


def read_examples(filename):
    examples = []
    utterance = None
    action_seq = None
    with open(filename) as f:
        for line in f:
            line = line.strip()
            utterance, action_seq, entity_lex_str = line.rstrip('\n').split('\t')
            examples.append((utterance, action_seq, entity_lex_str))
    return examples


def write(out_filename, out_data):
    out_path = os.path.join(OUT_DIR, out_filename)
    with open(out_path, "w") as f:
        for x, y in out_data:
            #print('%s\t%s' % (x, ' '.join(y)), file=f)
            print >> f, '%s\t%s' % (x, ' '.join(y))

def action2seq(action_seq, geo_controller, general_controller, entity_lex_map={}):
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

        geo_flag = geo_controller.is_legal_action(gen_pre_action_class_out, [], action_token, '', node_dict, type_node_dict, entity_node_dict,
                                                            operation_dict, edge_dict, return_node, db_triple, [], for_controller=False, entity_lex_map=entity_lex_map)

        #print('action_token = %s, gen_flag = %s, geo_flag = %s' % (action_token, gen_flag, geo_flag))
        if not gen_flag or not geo_flag:
            legal_action_seq = False
            break

        gen_pre_action_class_in = gen_pre_action_class_out
        gen_pre_arg_list_in = gen_pre_arg_list_out
        gen_pre_action_in = gen_pre_action_out
        fun_trace_list_in = fun_trace_list_out

    #print('node_dict: ', node_dict)
    #print('type_node_dict: ', type_node_dict)
    #print('entity_node_dict: ', entity_node_dict)
    #print('edge_dict: ', edge_dict)
    #print('operation_dict: ', operation_dict)
    #print('db_triple: ', db_triple)
    #print('return_node: ', return_node)
    #print('fun_trace_list: ', fun_trace_list_in)

    if not legal_action_seq:
        logical_form = ['a']
        return logical_form

    fun_arg_map = {}
    fun_arg_map['return'] = []
    fun_arg_map['return'].append(return_node['node'])
    fun_trace_flag = {}
    entity_name_map = {}
    entity_load_set = set()
    for node_id in node_dict:
        if not len(node_id) == 1:
            legal_action_seq = False
            break
        ord_id = ord(node_id)
        if ord_id < ord('A') or ord_id > ord('Z'):
            legal_action_seq = False
            break

    for fun_trace in fun_trace_list_in:
        #print('fun_trace: ', fun_trace)
        if fun_trace.startswith('add_type_node:-:'):
            type_edge = fun_trace[fun_trace.index(':-:')+3:]
            if type_edge not in db_triple:
                legal_action_seq = False
                break
            if type_edge in fun_trace_flag and fun_trace_flag[type_edge]:
                continue
            fun_trace_flag[type_edge] = False
        elif fun_trace.startswith('add_entity_node'):
            split1 = fun_trace.index(':-:')
            const_edge = fun_trace[split1+3:]
            if const_edge not in db_triple:
                legal_action_seq = False
                break
            if const_edge in fun_trace_flag and fun_trace_flag[const_edge]:
                continue
            fun_trace_flag[const_edge] = False
        elif fun_trace.startswith('add_edge:-:'):
            edge = fun_trace[fun_trace.index(':-:') + 3:]
            if edge not in db_triple:
                legal_action_seq = False
                break
            if edge in fun_trace_flag and fun_trace_flag[edge]:
                continue
            fun_trace_flag[edge] = False

        elif fun_trace.startswith('add_operation'):
            operation = fun_trace[fun_trace.index(':-:') + 3:]
            if operation not in operation_dict['core']:
                legal_action_seq = False
                break
            fun_trace_flag[operation] = False
            fun_arg_map[operation] = []
        elif fun_trace.startswith('end_operation'):
            operation_key = fun_trace[fun_trace.index(':-:') + 3:]
            operation = operation_dict['end'][operation_key]
            operation_arg = operation_dict['core'][operation]['arg0']
            for fun in operation_arg:
                fun_trace_flag[fun] = True
                fun_arg_map[operation].append(fun)
        elif fun_trace.startswith('return'):
            pass
        else:
            legal_action_seq = False
            break

    for fun_trace in fun_trace_list_in:
        if fun_trace.startswith('add_type_node:-:'):
            type_edge = fun_trace[fun_trace.index(':-:')+3:]
            if fun_trace_flag[type_edge]:
                continue
            fun_arg_map['return'].append(type_edge)
        elif fun_trace.startswith('add_entity_node:-:'):
            split1 = fun_trace.index(':-:')
            const_edge = fun_trace[split1+3:]
            if fun_trace_flag[const_edge]:
                continue
            fun_arg_map['return'].append(const_edge)
        elif fun_trace.startswith('add_edge:-:'):
            edge = fun_trace[fun_trace.index(':-:')+3:]
            if fun_trace_flag[edge]:
                continue
            fun_arg_map['return'].append(edge)
        elif fun_trace.startswith('add_operation'):
            operation = fun_trace[fun_trace.index(':-:')+3:]
            if fun_trace_flag[operation]:
                continue
            fun_arg_map['return'].append(operation)
        else:
            pass

    #print('fun_arg_map: ', fun_arg_map)
    key = 'return'
    operation_fun_list = ['_highest', '_longest', '_shortest', '_lowest', '_largest', '_smallest', '_most', '_fewest']
    build_seq(key, fun_arg_map, operation_dict, db_triple,
              entity_name_map, entity_load_set, logical_form, operation_fun_list)

    if not legal_action_seq:
        logical_form = ['b']
    return logical_form

def build_seq(fun, fun_arg_map, operation_dict, db_triple,
              entity_name_map, entity_load_set, logical_form, operation_fun_list):
    #print('fun in build_seq: ', fun)
    fun_name = fun[:fun.index(':_:')] if ':_:' in fun else fun
    if fun == 'return':
        logical_form.append('_answer')
        logical_form.append('(')
        logical_form.append(fun_arg_map[fun][0])
        if len(fun_arg_map[fun])  > 2:
            logical_form.append(',')
            logical_form.append('(')
            build_seq(fun_arg_map[fun][1], fun_arg_map, operation_dict, db_triple,
                      entity_name_map, entity_load_set, logical_form, operation_fun_list)
            for ii in range(2,len(fun_arg_map[fun])):
                logical_form.append(',')
                build_seq(fun_arg_map[fun][ii], fun_arg_map, operation_dict, db_triple,
                          entity_name_map, entity_load_set, logical_form, operation_fun_list)
            logical_form.append(')')
        elif len(fun_arg_map[fun]) > 1:
            logical_form.append(',')
            build_seq(fun_arg_map[fun][1], fun_arg_map, operation_dict, db_triple,
                      entity_name_map, entity_load_set, logical_form, operation_fun_list)
        else:
            pass
        logical_form.append(')')
    elif fun_name in operation_fun_list:
        logical_form.append(fun_name)
        logical_form.append('(')
        ope_for = operation_dict['core'][fun]['arg1'][0]
        logical_form.append(ope_for)
        if fun_name == '_most' or fun_name == '_fewest':
            ope_for = operation_dict['core'][fun]['arg2'][0]
            logical_form.append(',')
            logical_form.append(ope_for)
        if len(fun_arg_map[fun]) > 1:
            logical_form.append(',')
            logical_form.append('(')
            build_seq(fun_arg_map[fun][0], fun_arg_map, operation_dict, db_triple,
                      entity_name_map, entity_load_set, logical_form, operation_fun_list)
            for ii in range(1,len(fun_arg_map[fun])):
                logical_form.append(',')
                build_seq(fun_arg_map[fun][ii], fun_arg_map, operation_dict, db_triple,
                          entity_name_map, entity_load_set, logical_form, operation_fun_list)
            logical_form.append(')')
        elif len(fun_arg_map[fun]) > 0:
            logical_form.append(',')
            build_seq(fun_arg_map[fun][0], fun_arg_map, operation_dict, db_triple,
                      entity_name_map, entity_load_set, logical_form, operation_fun_list)
        else:
            pass
        logical_form.append(')')
    elif fun_name == '_count':
        logical_form.append('_count')
        logical_form.append('(')
        ope_for = operation_dict['core'][fun]['arg1'][0]
        logical_form.append(ope_for)
        if len(fun_arg_map[fun]) > 1:
            logical_form.append(',')
            logical_form.append('(')
            build_seq(fun_arg_map[fun][0], fun_arg_map, operation_dict, db_triple,
                      entity_name_map, entity_load_set, logical_form, operation_fun_list)
            for ii in range(1,len(fun_arg_map[fun])):
                logical_form.append(',')
                build_seq(fun_arg_map[fun][ii], fun_arg_map, operation_dict, db_triple,
                          entity_name_map, entity_load_set, logical_form, operation_fun_list)
            logical_form.append(')')
        elif len(fun_arg_map[fun]) > 0:
            logical_form.append(',')
            build_seq(fun_arg_map[fun][0], fun_arg_map, operation_dict, db_triple,
                      entity_name_map, entity_load_set, logical_form, operation_fun_list)
        else:
            pass
        logical_form.append(',')
        logical_form.append(operation_dict['core'][fun]['arg2'][0])
        logical_form.append(')')
    elif fun_name == '_sum':
        logical_form.append('_sum')
        logical_form.append('(')
        ope_for = operation_dict['core'][fun]['arg1'][0]
        logical_form.append(ope_for)
        if len(fun_arg_map[fun][:-1]) > 1:
            logical_form.append(',')
            logical_form.append('(')
            build_seq(fun_arg_map[fun][0], fun_arg_map, operation_dict, db_triple,
                      entity_name_map, entity_load_set, logical_form, operation_fun_list)
            for ii in range(1,len(fun_arg_map[fun][:-1])):
                logical_form.append(',')
                build_seq(fun_arg_map[fun][ii], fun_arg_map, operation_dict, db_triple,
                          entity_name_map, entity_load_set, logical_form, operation_fun_list)
            logical_form.append(')')
            logical_form.append(',')
            build_seq(fun_arg_map[fun][-1], fun_arg_map, operation_dict, db_triple,
                      entity_name_map, entity_load_set, logical_form, operation_fun_list)
        elif len(fun_arg_map[fun][:-1]) > 0:
            logical_form.append(',')
            build_seq(fun_arg_map[fun][0], fun_arg_map, operation_dict, db_triple,
                      entity_name_map, entity_load_set, logical_form, operation_fun_list)
            logical_form.append(',')
            build_seq(fun_arg_map[fun][-1], fun_arg_map, operation_dict, db_triple,
                      entity_name_map, entity_load_set, logical_form, operation_fun_list)
        else:
            pass
        logical_form.append(',')
        logical_form.append(operation_dict['core'][fun]['arg3'][0])
        logical_form.append(')')
    elif fun_name == '_not':
        logical_form.append('\+')
        add_right_paren_flag = False
        if len(fun_arg_map[fun]) > 1 or \
                (len(fun_arg_map[fun]) == 1 and not fun_arg_map[fun][0].startswith('_const')):
            logical_form.append('(')
            add_right_paren_flag = True
        if len(fun_arg_map[fun]) > 1:
            build_seq(fun_arg_map[fun][0], fun_arg_map, operation_dict, db_triple,
                      entity_name_map, entity_load_set, logical_form, operation_fun_list)
            for ii in range(1,len(fun_arg_map[fun])):
                logical_form.append(',')
                build_seq(fun_arg_map[fun][ii], fun_arg_map, operation_dict, db_triple,
                          entity_name_map, entity_load_set, logical_form, operation_fun_list)
        elif len(fun_arg_map[fun]) > 0:
            build_seq(fun_arg_map[fun][0], fun_arg_map, operation_dict, db_triple,
                      entity_name_map, entity_load_set, logical_form, operation_fun_list)
        else:
            pass
        if add_right_paren_flag:
            logical_form.append(')')

    elif fun.startswith('TYPE'):
        entity_type = fun[4:fun.index(':_:')]
        logical_form.append(entity_type)
        logical_form.append('(')
        arg = db_triple[fun]['arg']
        logical_form.append(arg)
        logical_form.append(')')
    else:
        add_entity_const_flag_1 = False
        add_entity_const_flag_2 = False
        edge = fun[:fun.index(':_:')]
        logical_form.append(edge)
        logical_form.append('(')
        arg1 = db_triple[fun]['arg1']
        if arg1 in entity_name_map and arg1 not in entity_load_set:
            add_entity_const_flag_1 = True
            logical_form.append(entity_name_map[arg1])
        elif arg1 in entity_name_map:
            logical_form.append(entity_name_map[arg1])
        else:
            logical_form.append(arg1)
        logical_form.append(',')
        arg2 = db_triple[fun]['arg2']
        if arg2 in entity_name_map and arg2 not in entity_load_set:
            add_entity_const_flag_2 = True
            logical_form.append(entity_name_map[arg2])
        elif arg2 in entity_name_map:
            logical_form.append(entity_name_map[arg2])
        else:
            if edge.startswith('_const'):
                entity_type = '_' + arg2[arg2.index(':=:') + 3:] + 'id'
                entity_name = arg2[:arg2.index(':=:')]
                logical_form.append(entity_type)
                logical_form.append('(')
                if entity_type.startswith('_cityid'):
                    if len(entity_name) > 3 and entity_name[-3] == '_':
                        state = entity_name[-2:]
                        entity_name = entity_name[:-3]
                        entity_name = entity_name.replace('_', ' ')
                        name_parts = entity_name.split(' ')
                        if len(name_parts) > 1:
                            logical_form.append('\'')
                            for name_part in name_parts:
                                logical_form.append(name_part)
                            logical_form.append('\'')
                        else:
                            logical_form.append(entity_name)
                        logical_form.append(',')
                        logical_form.append(state)
                    else:
                        entity_name = entity_name.replace('_', ' ')
                        name_parts = entity_name.split(' ')
                        if len(name_parts) > 1:
                            logical_form.append('\'')
                            for name_part in name_parts:
                                logical_form.append(name_part)
                            logical_form.append('\'')
                        else:
                            logical_form.append(entity_name)
                        logical_form.append(',')
                        logical_form.append('_')
                else:
                    entity_name = entity_name.replace('_', ' ')
                    name_parts = entity_name.split(' ')
                    if len(name_parts) > 1:
                        logical_form.append('\'')
                        for name_part in name_parts:
                            logical_form.append(name_part)
                        logical_form.append('\'')
                    else:
                        logical_form.append(entity_name)
                logical_form.append(')')
            else:
                logical_form.append(arg2)
        logical_form.append(')')
        if add_entity_const_flag_1:
            entity_load_set.add(arg1)
            logical_form.append(',')
            logical_form.append('_const')
            logical_form.append('(')
            logical_form.append(entity_name_map[arg1])
            logical_form.append(',')
            entity_type = '_' + arg1[arg1.index(':=:')+3:] + 'id'
            entity_name = arg1[:arg1.index(':=:')]
            logical_form.append(entity_type)
            logical_form.append('(')
            if entity_type.startswith('_cityid'):
                if len(entity_name) > 3 and entity_name[-3] == '_':
                    state = entity_name[-2:]
                    entity_name = entity_name[:-3]
                    entity_name = entity_name.replace('_', ' ')
                    name_parts = entity_name.split(' ')
                    if len(name_parts) > 1:
                        logical_form.append('\'')
                        for name_part in name_parts:
                            logical_form.append(name_part)
                        logical_form.append('\'')
                    else:
                        logical_form.append(entity_name)
                    logical_form.append(',')
                    logical_form.append(state)
                else:
                    entity_name = entity_name.replace('_', ' ')
                    name_parts = entity_name.split(' ')
                    if len(name_parts) > 1:
                        logical_form.append('\'')
                        for name_part in name_parts:
                            logical_form.append(name_part)
                        logical_form.append('\'')
                    else:
                        logical_form.append(entity_name)
                    logical_form.append(',')
                    logical_form.append('_')
            else:
                entity_name = entity_name.replace('_', ' ')
                name_parts = entity_name.split(' ')
                if len(name_parts) > 1:
                    logical_form.append('\'')
                    for name_part in name_parts:
                        logical_form.append(name_part)
                    logical_form.append('\'')
                else:
                    logical_form.append(entity_name)
            logical_form.append(')')
            logical_form.append(')')
        if add_entity_const_flag_2:
            entity_load_set.add(arg2)
            logical_form.append(',')
            logical_form.append('_const')
            logical_form.append('(')
            logical_form.append(entity_name_map[arg2])
            logical_form.append(',')
            entity_type = '_' + arg2[arg2.index(':=:') + 3:] + 'id'
            entity_name = arg2[:arg2.index(':=:')]
            logical_form.append(entity_type)
            logical_form.append('(')
            if entity_type.startswith('_cityid'):
                if len(entity_name) > 3 and entity_name[-3] == '_':
                    state = entity_name[-2:]
                    entity_name = entity_name[:-3]
                    entity_name = entity_name.replace('_', ' ')
                    name_parts = entity_name.split(' ')
                    if len(name_parts) > 1:
                        logical_form.append('\'')
                        for name_part in name_parts:
                            logical_form.append(name_part)
                        logical_form.append('\'')
                    else:
                        logical_form.append(entity_name)
                    logical_form.append(',')
                    logical_form.append(state)
                else:
                    entity_name = entity_name.replace('_', ' ')
                    name_parts = entity_name.split(' ')
                    if len(name_parts) > 1:
                        logical_form.append('\'')
                        for name_part in name_parts:
                            logical_form.append(name_part)
                        logical_form.append('\'')
                    else:
                        logical_form.append(entity_name)
                    logical_form.append(',')
                    logical_form.append('_')
            else:
                entity_name = entity_name.replace('_', ' ')
                name_parts = entity_name.split(' ')
                if len(name_parts) > 1:
                    logical_form.append('\'')
                    for name_part in name_parts:
                        logical_form.append(name_part)
                    logical_form.append('\'')
                else:
                    logical_form.append(entity_name)
            logical_form.append(')')
            logical_form.append(')')

def process(filename, base_file_name, geo_controller, general_controller):
    in_data = read_examples(filename)
    out_data = []
    for (utterance, action_seq, entity_lex_str) in in_data:
        print('*********************************************')
        print('utterance: ' + utterance)
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
    action_seq = 'add_operation:-:_count add_node:-:B add_type_node:-:_state arg_node:-:B add_operation:-:_not add_node:-:C add_edge:-:_loc arg_node:-:C arg_node:-:B end_operation:-:_not add_type_node:-:_river arg_node:-:C end_operation:-:_count ope_for:-:B ope_return:-:A return:-:A'
    print('actions: ' + action_seq)
    entity_lex = {'ent0:=:state':'texas:=:state'}
    #print('len = ' + str(len(action_seq.split(' '))))
    lf = action2seq(action_seq, geo_controller, general_controller, entity_lex_map=entity_lex)
    print('logical_form: ' + ' '.join(lf))
    #print('len = ' + str(len(lf)))

def test_legal(general_controller):
    action_seq = 'add_operation:-:_highest add_node:-:A add_type_node:-:_mountain arg_node:-:A add_node:-:B add_edge:-:_loc arg_node:-:A arg_node:-:B add_entity_node:-:usa:=:country arg_node:-:B end_operation:-:arg ope_for:-:A return:-:A'
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
    geo_grammar_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "seq2action_entity\\ontology\\geo.grammar")
    general_grammar_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "seq2action_entity\\ontology\\general.grammar")
    geo_controller = GeoOntology(geo_grammar_file, True)
    general_controller = GeneralOntology(general_grammar_file, True)
    #main(geo_controller, general_controller)
    test(geo_controller, general_controller)
    #test_legal(general_controller)