import os


class Ontology(object):

    def __init__(self, grammar_file, use_ontology):
        self.grammars = self.read_grammars(grammar_file)
        self.use_ontology = use_ontology

    def read_grammars(self, grammar_file):
        raise NotImplementedError

    def is_legal_action(self, pre_action_class, pre_arg_list, action_token, pre_action, node_dict, type_node_dict, entity_node_dict, operation_dict, edge_dict, return_node, db_triple, fun_trace_list, for_controller=True):
        raise NotImplementedError

    def is_legal_action_then_read(self, pre_action_class, pre_arg_list, action_token, pre_action, node_dict, type_node_dict, entity_node_dict, operation_dict, edge_dict, return_node, db_triple, fun_trace_list, for_controller=True):
        raise NotImplementedError

    def get_legal_action_list(self, pre_action_class, pre_arg_list, pre_action, node_dict, type_node_dict, entity_node_dict, operation_dict, edge_dict, return_node, db_triple, fun_trace_list, action_all, for_controller=True):
        raise NotImplementedError