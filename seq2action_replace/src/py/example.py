"""A single example in a dataset."""
import lexicon

class Example(object):
  """A single example in a dataset.

  Basically a struct after it's initialized, with the following fields:
    - self.x_str, self.y_str: input/output as single space-separated strings
    - self.x_toks, self.y_toks: input/output as list of strings
    - self.input_vocab, self.output_vocab: Vocabulary objects
    - self.x_inds, self.y_inds: input/output as indices in corresponding vocab
    - self.copy_toks: list of length len(x_toks), having tokens that should
        be generated if copying is performed.
    - self.y_in_x_inds: ji-th entry is whether copy_toks[i] == y_toks[j].

  Treat these objects as read-only.
  """
  def __init__(self, x_str, y_str, y_str_lf, entity_lex_map, input_vocab, output_vocab,
               reverse_input=False):
    """Create an Example object.
    
    Args:
      x_str: Input sequence as a space-separated string
      y_str: Output sequence as a space-separated string
      input_vocab: Vocabulary object for input
      input_vocab: Vocabulary object for output
      reverse_input: If True, reverse the input.
    """
    self.x_str = x_str  # Don't reverse this, used just for printing out
    self.y_str = y_str
    self.y_str_lf = y_str_lf
    self.entity_lex_map = entity_lex_map
    self.input_vocab = input_vocab
    self.output_vocab = output_vocab
    self.reverse_input = reverse_input
    self.x_toks = x_str.split(' ')
    if reverse_input:
      self.x_toks = self.x_toks[::-1]
    self.y_toks = y_str.split(' ')
    self.input_vocab = input_vocab
    self.output_vocab = output_vocab
    self.y_inds = output_vocab.action_seq_to_indices(y_str)
    self.x_inds = input_vocab.sentence_to_indices(self.x_str)
    if reverse_input:
      self.x_inds = self.x_inds[::-1]
    # Make sure to add EOS tags for x

