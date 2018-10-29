"""A soft attention model

We use the global attention model with input feeding
used by Luong et al. (2015).
See http://stanford.edu/~lmthang/data/papers/emnlp15_attn.pdf
"""
import itertools
import numpy
import theano
from theano import tensor as T
from theano.ifelse import ifelse
import sys
import copy

from attnspec import AttentionSpec
from derivation import Derivation
from neural import NeuralModel, CLIP_THRESH, NESTEROV_MU
from vocabulary import Vocabulary
from action_vocabulary import ActionVocabulary

class AttentionModel(NeuralModel):
  """An encoder-decoder RNN model."""
  def setup(self):
    self.setup_encoder()
    self.setup_decoder_step()
    self.setup_decoder_write()
    self.setup_backprop()

  @classmethod
  def get_spec_class(cls):
    return AttentionSpec

  def _symb_encoder(self, x):
    """The encoder (symbolically), for decomposition."""
    def fwd_rec(x_t, h_prev, *params):
      return self.spec.f_enc_fwd(x_t, h_prev)
    def bwd_rec(x_t, h_prev, *params):
      return self.spec.f_enc_bwd(x_t, h_prev)

    fwd_states, _ = theano.scan(fwd_rec, sequences=[x],
                                outputs_info=[self.spec.get_init_fwd_state()],
                                non_sequences=self.spec.get_all_shared())
    bwd_states, _ = theano.scan(bwd_rec, sequences=[x],
                                outputs_info=[self.spec.get_init_bwd_state()],
                                non_sequences=self.spec.get_all_shared(),
                                go_backwards=True)
    enc_last_state = T.concatenate([fwd_states[-1], bwd_states[-1]])
    dec_init_state = self.spec.get_dec_init_state(enc_last_state)

    bwd_states = bwd_states[::-1]  # Reverse backward states.
    annotations = T.concatenate([fwd_states, bwd_states], axis=1)
    return (dec_init_state, annotations)

  def setup_encoder(self):
    """Run the encoder.  Used at test time."""
    x = T.lvector('x_for_enc')
    dec_init_state, annotations = self._symb_encoder(x)
    self._encode = theano.function(
        inputs=[x], outputs=[dec_init_state, annotations])

  def setup_decoder_step(self):
    """Advance the decoder by one step.  Used at test time."""
    y_t = T.lscalar('y_t_for_dec')
    c_prev = T.vector('c_prev_for_dec')
    h_prev = T.vector('h_prev_for_dec')
    h_t = self.spec.f_dec(y_t, c_prev, h_prev)
    self._decoder_step = theano.function(inputs=[y_t, c_prev, h_prev], outputs=h_t)

  def setup_decoder_write(self):
    """Get the write distribution of the decoder.  Used at test time."""
    annotations = T.matrix('annotations_for_write')
    h_prev = T.vector('h_prev_for_write')
    h_for_write = self.spec.decoder.get_h_for_write(h_prev)
    scores = self.spec.get_attention_scores(h_for_write, annotations)
    alpha = self.spec.get_alpha(scores)
    c_t = self.spec.get_context(alpha, annotations)
    write_dist = self.spec.f_write(h_for_write, c_t)
    self._decoder_write = theano.function(
        inputs=[annotations, h_prev], outputs=[write_dist, c_t, alpha])

  def setup_backprop(self):
    eta = T.scalar('eta_for_backprop')
    x = T.lvector('x_for_backprop')
    y = T.lvector('y_for_backprop')
    l2_reg = T.scalar('l2_reg_for_backprop')

    # Normal operation
    dec_init_state, annotations = self._symb_encoder(x)
    nll, p_y_seq, objective, updates  = self._setup_backprop_with(
        dec_init_state, annotations, y, eta, l2_reg)
    self._get_nll = theano.function(
        inputs=[x, y], outputs=nll, on_unused_input='warn')
    self._backprop = theano.function(
        inputs=[x, y, eta, l2_reg],
        outputs=[p_y_seq, objective],
        updates=updates)

    # Add distractors
    self._get_nll_distract = []
    self._backprop_distract = []
    if self.distract_num > 0:
      x_distracts = [T.lvector('x_distract_%d_for_backprop' % i) 
                     for i in range(self.distract_num)]
      all_annotations = [annotations]
      for i in range(self.distract_num):
        _, annotations_distract = self._symb_encoder(x_distracts[i])
        all_annotations.append(annotations_distract)
      annotations_with_distract = T.concatenate(all_annotations, axis=0)
      nll_d, p_y_seq_d, objective_d, updates_d = self._setup_backprop_with(
          dec_init_state, annotations_with_distract, y, eta, l2_reg)
      self._get_nll_distract = theano.function(
          inputs=[x, y] + x_distracts, outputs=nll_d,
          on_unused_input='warn')
      self._backprop_distract = theano.function(
          inputs=[x, y, eta, l2_reg] + x_distracts,
          outputs=[p_y_seq_d, objective_d],
          updates=updates_d)

  def _setup_backprop_with(self, dec_init_state, annotations, y, eta, l2_reg):
    def decoder_recurrence(y_t, h_prev, annotations, *params):
      h_for_write = self.spec.decoder.get_h_for_write(h_prev)
      scores = self.spec.get_attention_scores(h_for_write, annotations)
      alpha = self.spec.get_alpha(scores)
      c_t = self.spec.get_context(alpha, annotations)
      write_dist = self.spec.f_write(h_for_write, c_t)
      p_y_t = write_dist[y_t]
      h_t = self.spec.f_dec(y_t, c_t, h_prev)
      return (h_t, p_y_t)

    dec_results, _ = theano.scan(
        fn=decoder_recurrence, sequences=[y],
        outputs_info=[dec_init_state, None],
        non_sequences=[annotations] + self.spec.get_all_shared())
    p_y_seq = dec_results[1]
    log_p_y = T.sum(T.log(p_y_seq))
    nll = -log_p_y
    # Add L2 regularization
    regularization = l2_reg / 2 * sum(T.sum(p**2) for p in self.params)
    objective = nll + regularization
    gradients = T.grad(objective, self.params)

    # Do the updates here
    updates = []
    if self.spec.step_rule in ('adagrad', 'rmsprop'):
      # Adagrad updates
      for p, g, c in zip(self.params, gradients, self.grad_cache):
        grad_norm = g.norm(2)
        clipped_grad = ifelse(grad_norm >= CLIP_THRESH, 
                              g * CLIP_THRESH / grad_norm, g)
        if self.spec.step_rule == 'adagrad':
          new_c = c + clipped_grad ** 2
        else:  # rmsprop
          decay_rate = 0.9  # Use fixed decay rate of 0.9
          new_c = decay_rate * c + (1.0 - decay_rate) * clipped_grad ** 2
        new_p = p - eta * clipped_grad / T.sqrt(new_c + 1e-4)
        has_non_finite = T.any(T.isnan(new_p) + T.isinf(new_p))
        updates.append((p, ifelse(has_non_finite, p, new_p)))
        updates.append((c, ifelse(has_non_finite, c, new_c)))
    elif self.spec.step_rule == 'nesterov':
      # Nesterov momentum
      for p, g, v in zip(self.params, gradients, self.grad_cache):
        grad_norm = g.norm(2)
        clipped_grad = ifelse(grad_norm >= CLIP_THRESH, 
                              g * CLIP_THRESH / grad_norm, g)
        new_v = NESTEROV_MU * v - eta * clipped_grad
        new_p = p - NESTEROV_MU * v + (1 + NESTEROV_MU) * new_v
        has_non_finite = (T.any(T.isnan(new_p) + T.isinf(new_p)) +
                          T.any(T.isnan(new_v) + T.isinf(new_v)))
        updates.append((p, ifelse(has_non_finite, p, new_p)))
        updates.append((v, ifelse(has_non_finite, v, new_v)))
    else:
      # Simple SGD updates
      for p, g in zip(self.params, gradients):
        grad_norm = g.norm(2)
        clipped_grad = ifelse(grad_norm >= CLIP_THRESH, 
                              g * CLIP_THRESH / grad_norm, g)
        new_p = p - eta * clipped_grad
        has_non_finite = T.any(T.isnan(new_p) + T.isinf(new_p))
        updates.append((p, ifelse(has_non_finite, p, new_p)))
    return nll, p_y_seq, objective, updates

  def get_legal_action_list(self, controller, gen_pre_action_class_in, gen_pre_arg_list_in,
                                                     gen_pre_action_in, node_dict, type_node_dict, entity_node_dict,
                                                     operation_dict, edge_dict, return_node, db_triple,
                                                     fun_trace_list_in, action_all, entity_lex_map={}):
      #print('entity_lex in get_legal_action_list = %s' % entity_lex_map)
      ret_list = numpy.zeros(len(action_all)).astype(T.config.floatX)
      legal_list = controller.get_legal_action_list(gen_pre_action_class_in, gen_pre_arg_list_in,
                                                     gen_pre_action_in, node_dict, type_node_dict, entity_node_dict,
                                                     operation_dict, edge_dict, return_node, db_triple,
                                                     fun_trace_list_in, action_all, entity_lex_map=entity_lex_map)
      for i in range(len(legal_list)):
        if legal_list[i]:
          ret_list[i] = 1.0
      return ret_list

  def decode_greedy(self, domain, ex, domain_convertor, domain_controller, general_controller, max_len=100):
    h_t, annotations = self._encode(ex.x_inds)
    y_tok_seq = []
    p_y_seq = []  # Should be handy for error analysis
    p = 1
    break_flag = False
    action_all = self.out_vocabulary.get_action_list()

    gen_pre_action_in = ''
    gen_pre_action_class_in = 'start'
    gen_pre_arg_list_in = []
    node_dict = {}
    type_node_dict = {}
    entity_node_dict = {}
    operation_dict = {}
    edge_dict = {}
    return_node = {}
    db_triple = {}
    fun_trace_list_in = []

    for i in range(max_len):
      write_dist, c_t, alpha = self._decoder_write(annotations, h_t)
      legal_dist_gen = self.get_legal_action_list(general_controller, gen_pre_action_class_in, gen_pre_arg_list_in,
                                                     gen_pre_action_in, node_dict, type_node_dict, entity_node_dict,
                                                     operation_dict, edge_dict, return_node, db_triple,
                                                     fun_trace_list_in, action_all)


      legal_dist_dom = self.get_legal_action_list(domain_controller, gen_pre_action_class_in, gen_pre_arg_list_in,
                                                     gen_pre_action_in, node_dict, type_node_dict, entity_node_dict,
                                                     operation_dict, edge_dict, return_node, db_triple,
                                                     fun_trace_list_in, action_all)


      final_dist = write_dist * legal_dist_gen * legal_dist_dom
      #print('write_dist: ', write_dist)
      #print('legal_dist_gen: ', legal_dist_gen)
      #print('legal_dist_dom: ', legal_dist_dom)
      #print('final_dist: ', final_dist)
      y_t = numpy.argmax(final_dist)

      p_y_t = write_dist[y_t]
      p_y_seq.append(p_y_t)
      p *= p_y_t
      if self.out_vocabulary.action_is_end(y_t):
        break_flag = True
      y_tok = self.out_vocabulary.get_action(y_t)
      if y_t >= self.out_vocabulary.all_size():
        print('error in attention for out vocabulary')
      y_tok_seq.append(y_tok)
      action_token = y_tok
      gen_flag, gen_pre_action_class_out, gen_pre_arg_list_out, gen_pre_action_out, fun_trace_list_out = \
        general_controller.is_legal_action_then_read(gen_pre_action_class_in, gen_pre_arg_list_in, action_token,
                                                     gen_pre_action_in, node_dict, type_node_dict, entity_node_dict,
                                                     operation_dict, edge_dict, return_node, db_triple,
                                                     fun_trace_list_in)
      gen_pre_action_class_in = gen_pre_action_class_out
      gen_pre_arg_list_in = gen_pre_arg_list_out
      gen_pre_action_in = gen_pre_action_out
      fun_trace_list_in = fun_trace_list_out

      if break_flag:
        break
      h_t = self._decoder_step(y_t, c_t, h_t)
    y_tok_lf = domain_convertor(' '.join(y_tok_seq), domain_controller, general_controller)
    return [Derivation(ex, p, y_tok_seq, y_tok_lf)]

  def decode_beam(self, domain, ex, domain_convertor, domain_controller, general_controller, beam_size=1, max_len=100):
    h_t, annotations = self._encode(ex.x_inds)
    beam = [[Derivation(ex, 1, [], [], hidden_state=h_t,p_list=[],entity_lex_map=ex.entity_lex_map,
                        attention_list=[])]]
    finished = []
    final_finished = []
    action_all = self.out_vocabulary.get_action_list()

    #print('entity_lex in decode_beam = %s' % ex.entity_lex_map)

    for i in range(1, max_len):
      #print >> sys.stderr, 'decode_beam: length = %d' % i
      if len(beam[i-1]) == 0: break
      # See if beam_size-th finished deriv is best than everything on beam now.
      if len(finished) >= beam_size:
        finished_p = finished[beam_size-1].p
        cur_best_p = beam[i-1][0].p
        if cur_best_p < finished_p:
          break
      new_beam = []

      for deriv in beam[i-1]:
        cur_p = deriv.p
        h_t = deriv.hidden_state
        y_tok_seq = deriv.y_toks
        p_list = deriv.p_list
        attention_list = deriv.attention_list
        entity_lex_map = deriv.entity_lex_map

        #print('entity_lex in loop for beam = %s' % entity_lex_map)

        gen_pre_action_for_test = deriv.gen_pre_action_in_deriv
        gen_pre_action_class_for_test = deriv.gen_pre_action_class_in_deriv
        gen_pre_arg_list_for_test = copy.deepcopy(deriv.gen_pre_arg_list_in_deriv)

        node_dict_for_test = copy.deepcopy(deriv.node_dict_in_deriv)
        type_node_dict_for_test = copy.deepcopy(deriv.type_node_dict_in_deriv)
        entity_node_dict_for_test = copy.deepcopy(deriv.entity_node_dict_in_deriv)
        operation_dict_for_test = copy.deepcopy(deriv.operation_dict_in_deriv)
        edge_dict_for_test = copy.deepcopy(deriv.edge_dict_in_deriv)
        return_node_for_test = copy.deepcopy(deriv.return_node_in_deriv)
        db_triple_for_test = copy.deepcopy(deriv.db_triple_in_deriv)
        fun_trace_list_for_test = copy.deepcopy(deriv.fun_trace_list_in_deriv)
        #print('***************************************')
        #print('y_tok_seq: %s' % ' '.join(y_tok_seq))
        #print('pre_action_for_test: ', gen_pre_action_for_test)
        #print('pre_action_class_for_test: ', gen_pre_action_class_for_test)
        #print('pre_arg_list_for_test: ', gen_pre_arg_list_for_test)
        #print('type_node_dict_for_test: ', type_node_dict_for_test)
        #print('edge_dict_for_test: ', edge_dict_for_test)
        #print('node_dict_for_test: ', node_dict_for_test)
        #print('entity_node_dict_for_test: ', entity_node_dict_for_test)
        #print('db_trible_for_test: ', db_triple_for_test)
        #print('operation_dict_for_test: ', operation_dict_for_test)
        #print('return_node_for_test: ', return_node_for_test)
        #print('fun_trace_list_for_test: ', fun_trace_list_for_test)

        write_dist, c_t, alpha = self._decoder_write(annotations, h_t)

        legal_dist_gen = self.get_legal_action_list(general_controller, gen_pre_action_class_for_test, gen_pre_arg_list_for_test,
                                                     gen_pre_action_for_test, node_dict_for_test, type_node_dict_for_test, entity_node_dict_for_test,
                                                     operation_dict_for_test, edge_dict_for_test, return_node_for_test, db_triple_for_test,
                                                     fun_trace_list_for_test, action_all, entity_lex_map=entity_lex_map)

        action_all_for_domain = []
        for ii in range(len(legal_dist_gen)):
            if legal_dist_gen[ii]:
                action_all_for_domain.append(action_all[ii])
            else:
                action_all_for_domain.append('<COPY>')

        legal_dist_dom = self.get_legal_action_list(domain_controller, gen_pre_action_class_for_test, gen_pre_arg_list_for_test,
                                                     gen_pre_action_for_test, node_dict_for_test, type_node_dict_for_test, entity_node_dict_for_test,
                                                     operation_dict_for_test, edge_dict_for_test, return_node_for_test, db_triple_for_test,
                                                     fun_trace_list_for_test, action_all_for_domain, entity_lex_map=entity_lex_map)

        #print('write_dist: (', len(write_dist), ') ', write_dist)
        #print('legal_dist_gen: (', len(legal_dist_gen), ') ', legal_dist_gen)
        #print('legal_dist_dom: (', len(legal_dist_dom), ') ', legal_dist_dom)

        final_dist = write_dist * legal_dist_gen * legal_dist_dom

        #print('final_dist: (', len(final_dist), ') ', final_dist)


        sorted_dist = sorted([(p_y_t, y_t) for y_t, p_y_t in enumerate(final_dist)],
                             reverse=True)

        for j in range(beam_size):
          gen_pre_action_for_read = gen_pre_action_for_test
          gen_pre_action_class_for_read = gen_pre_action_class_for_test
          gen_pre_arg_list_for_read = copy.deepcopy(gen_pre_arg_list_for_test)

          node_dict_for_read = copy.deepcopy(node_dict_for_test)
          type_node_dict_for_read = copy.deepcopy(type_node_dict_for_test)
          entity_node_dict_for_read = copy.deepcopy(entity_node_dict_for_test)
          operation_dict_for_read = copy.deepcopy(operation_dict_for_test)
          edge_dict_for_read = copy.deepcopy(edge_dict_for_test)
          return_node_for_read = copy.deepcopy(return_node_for_test)
          db_triple_for_read = copy.deepcopy(db_triple_for_test)
          fun_trace_list_for_read = copy.deepcopy(fun_trace_list_for_test)

          #print('--------------')
          #print('pre_action_for_read: ', gen_pre_action_for_read)
          #print('pre_action_class_for_read: ', gen_pre_action_class_for_read)
          #print('pre_arg_list_for_read: ', gen_pre_arg_list_for_read)
          #print('type_node_dict_for_read: ', type_node_dict_for_read)
          #print('edge_dict_for_read: ', edge_dict_for_read)
          #print('node_dict_for_read: ', node_dict_for_read)
          #print('entity_node_dict_for_read: ', entity_node_dict_for_read)
          #print('db_trible_for_read: ', db_triple_for_read)
          #print('operation_dict_for_read: ', operation_dict_for_read)
          #print('return_node_for_read: ', return_node_for_read)
          #print('fun_trace_list_for_read: ', fun_trace_list_for_read)
          #print('--------------')

          p_y_t, y_t = sorted_dist[j]
          if p_y_t == 0.0:
            continue
          new_p = cur_p * p_y_t
          append_flag = False
          if self.out_vocabulary.action_is_end(domain, y_t):
            append_flag = True
          if y_t < self.out_vocabulary.size():
            y_tok = self.out_vocabulary.get_action(y_t)
          else:
            print('error action index!')
          new_h_t = self._decoder_step(y_t, c_t, h_t)
          #print('y_tok: ', y_tok, ' p_y_t: ', p_y_t)
          action_token = y_tok
          gen_flag, gen_pre_action_class_out, gen_pre_arg_list_out, gen_pre_action_out, fun_trace_list_out = \
            general_controller.is_legal_action_then_read(gen_pre_action_class_for_read, gen_pre_arg_list_for_read, action_token,
                                                         gen_pre_action_for_read, node_dict_for_read, type_node_dict_for_read, entity_node_dict_for_read,
                                                         operation_dict_for_read, edge_dict_for_read, return_node_for_read, db_triple_for_read,
                                                         fun_trace_list_for_read)
          if not gen_flag:
            print('test is right, but read is wrong!')
            continue
          if append_flag:
            finished.append(Derivation(ex, new_p, y_tok_seq + [y_tok], [], p_list=p_list+[p_y_t], entity_lex_map=entity_lex_map,
                                       attention_list=attention_list + [alpha],
                                 gen_pre_action_in_deriv = gen_pre_action_out, gen_pre_action_class_in_deriv = gen_pre_action_class_out,
                                 gen_pre_arg_list_in_deriv = gen_pre_arg_list_out, node_dict_in_deriv = node_dict_for_read, type_node_dict_in_deriv = type_node_dict_for_read,
                                 entity_node_dict_in_deriv = entity_node_dict_for_read, operation_dict_in_deriv = operation_dict_for_read,
                                 edge_dict_in_deriv = edge_dict_for_read, return_node_in_deriv = return_node_for_read,
                                  db_triple_in_deriv = db_triple_for_read, fun_trace_list_in_deriv = fun_trace_list_out))
            continue
          new_entry = Derivation(ex, new_p, y_tok_seq + [y_tok], [],
                                 hidden_state=new_h_t, p_list=p_list+[p_y_t], entity_lex_map=entity_lex_map,
                                 attention_list=attention_list + [alpha],
                                 gen_pre_action_in_deriv = gen_pre_action_out, gen_pre_action_class_in_deriv = gen_pre_action_class_out,
                                 gen_pre_arg_list_in_deriv = gen_pre_arg_list_out, node_dict_in_deriv = node_dict_for_read, type_node_dict_in_deriv = type_node_dict_for_read,
                                 entity_node_dict_in_deriv = entity_node_dict_for_read, operation_dict_in_deriv = operation_dict_for_read,
                                 edge_dict_in_deriv = edge_dict_for_read, return_node_in_deriv = return_node_for_read,
                                  db_triple_in_deriv = db_triple_for_read, fun_trace_list_in_deriv = fun_trace_list_out)
          new_beam.append(new_entry)

      new_beam.sort(key=lambda x: x.p, reverse=True)
      beam.append(new_beam[:beam_size])
      finished.sort(key=lambda x: x.p, reverse=True)
    for deriv in finished:
      y_new_toks = []
      entity_lex = deriv.example.entity_lex_map
      for y_tok in deriv.y_toks:
        if y_tok.startswith('add_entity_node:'):
            entity = y_tok[y_tok.index(':-:')+3:]
            if entity in entity_lex:
                new_entity = entity_lex[entity]
                y_new_tok = y_tok.replace(entity, new_entity)
                y_new_toks.append(y_new_tok)
                continue
        y_new_toks.append(y_tok)
      y_new_str = ' '.join(y_new_toks)

      #print('entity_lex in finished = %s' % entity_lex)
      #print('y_new_str: %s' % y_new_str)
      y_toks_lf = domain_convertor(y_new_str, domain_controller, general_controller, entity_lex_map=entity_lex)
      #print('y_toks_lf: %s' % ' '.join(y_toks_lf))
      new_entry = Derivation(deriv.example, deriv.p, deriv.y_toks, y_toks_lf,
                             deriv.hidden_state, deriv.p_list, deriv.entity_lex_map, deriv.attention_list)
      final_finished.append(new_entry)
    return sorted(final_finished, key=lambda x: x.p, reverse=True)
