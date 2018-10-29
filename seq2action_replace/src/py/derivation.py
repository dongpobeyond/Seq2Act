"""A full or partial derivation."""
class Derivation(object):
  def __init__(self, example, p, y_toks, y_toks_lf, hidden_state=None, p_list=None, entity_lex_map=None,
               attention_list=None, gen_pre_action_in_deriv = '', gen_pre_action_class_in_deriv = 'start', gen_pre_arg_list_in_deriv = [],
            node_dict_in_deriv = {}, type_node_dict_in_deriv = {}, entity_node_dict_in_deriv = {}, operation_dict_in_deriv = {}, edge_dict_in_deriv = {}, return_node_in_deriv = {},
          db_triple_in_deriv = {}, fun_trace_list_in_deriv = []):
    self.example = example
    self.p = p
    self.y_toks = y_toks
    self.y_toks_lf = y_toks_lf
    self.hidden_state = hidden_state
    self.p_list = p_list
    self.entity_lex_map = entity_lex_map
    self.attention_list = attention_list

    self.gen_pre_action_in_deriv = gen_pre_action_in_deriv
    self.gen_pre_action_class_in_deriv = gen_pre_action_class_in_deriv
    self.gen_pre_arg_list_in_deriv = gen_pre_arg_list_in_deriv
    self.node_dict_in_deriv = node_dict_in_deriv
    self.type_node_dict_in_deriv = type_node_dict_in_deriv
    self.entity_node_dict_in_deriv = entity_node_dict_in_deriv
    self.operation_dict_in_deriv = operation_dict_in_deriv
    self.edge_dict_in_deriv = edge_dict_in_deriv
    self.return_node_in_deriv = return_node_in_deriv
    self.db_triple_in_deriv = db_triple_in_deriv
    self.fun_trace_list_in_deriv = fun_trace_list_in_deriv
