"""A lexicon maps input substrings to an output token."""
import collections
import itertools
import re
import sys

def strip_unk(w):
  # Strip unk:%06d identifiers
  m = re.match('^unk:[0-9]{6,}:(.*)$', w)
  if m:
    return m.group(1)
  else:
    return w

class LexiconReplace:
  """A Lexicon class.

  The lexicon stores two types of rules:
    1. Entries are pairs (name, entity), 
       where name could be a single word or multi-word phrase.
    2. Handlers are pairs (regex, func(match) -> entity).
       regex is checked to see if it matches any span of the input.
       If so, the function is applied to the match object to yield an entity.

  We additionally keep track of:
    3. Unique words.  If a word |w| appears in exactly one entry (|n|, |e|),
       then a lower-precision rule maps |w| directly to |e|, even if the
       entire name |n| is not present.

  Rules take precedence in the order given: 1, then 2, then 3.
  Within each block, rules that match larger spans take precedence
  over ones that match shorter spans.
  """
  def __init__(self):
    self.entries = collections.OrderedDict()

  def add_entries(self, entries):
    for name, entity in entries:
      # Update self.entries
      if name not in self.entries:
        self.entries[name] = []
      if entity not in self.entries[name]:
        self.entries[name].append(entity)
      else:
        print('same entity entry: (%s, %s)' % (name, entity))

  def test_map(self, s):
    words = s.split(' ')
    entities = self.map_over_sentence(words)
    print('  %s -> %s' % (s, entities))

  def map_over_sentence(self, words, return_entries=False):
    """Apply unambiguous lexicon rules to an entire sentence.
    
    Args:
      words: A list of words
      return_entries: if True, return a list (span_inds, entity) pairs instead.
    Returns: 
      A list of length len(words), where words[i] maps to retval[i]
    """
    #print('words: ', ' '.join(words))
    entities = ['' for i in range(len(words))]
    ind_pairs = sorted(list(itertools.combinations(range(len(words) + 1), 2)),
                       key=lambda x: x[0] - x[1])
    ret_entries = []
    words = [strip_unk(w) for w in words]  # Strip unk:%06d stuff

    # Entries
    for i, j in ind_pairs:
      if any(x for x in entities[i:j]): 
        # Something in this span has already been assinged
        continue
      span = ' '.join(words[i:j])
      if span in self.entries:
        entity_list = self.entries[span]
        for k in range(i, j):
          entities[k] = ' '.join(entity_list)
        ret_entries.append(((i, j), ' '.join(entity_list)))

    if return_entries:
      return ret_entries
    print('entities: ', ' '.join(entities))
    return entities
