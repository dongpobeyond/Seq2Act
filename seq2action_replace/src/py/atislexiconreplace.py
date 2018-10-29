"""Reads a lexicon for GEO.

A lexicon simply maps natural language phrases to identifiers in the GEO database.
"""
import collections
import os
import re
import sys

from lexiconreplace import LexiconReplace

LEXICON_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'lexicon')

def get_lexicon_from_raw_lexicon_then_write(basename, newname):
  filename = os.path.join(LEXICON_DIR, basename)
  newfilename = os.path.join(LEXICON_DIR, newname)
  lex = LexiconReplace()
  entries = []
  with open(filename) as f:
    for line in f:
      lexicon_tuple = parse_entry(line)
      name = lexicon_tuple[0]
      entity = lexicon_tuple[1].replace(':', ':_')
      if entity == '':
        continue
      entries.append((name, entity))
  lex.add_entries(entries)
  with open(newfilename, 'w') as f:
    for name, entity_list in lex.entries.items():
      for entity in entity_list:
        print('%s :- NP : %s' % (name, entity), file=f)
        pass
  return lex

def print_aligned(a, b, indent=0):
  a_toks = []
  b_toks = []
  for x, y in zip(a, b):
    cur_len = max(len(x), len(y))
    a_toks.append(x.ljust(cur_len))
    b_toks.append(y.ljust(cur_len))

  prefix = ' ' * indent
  print('%s%s' % (prefix, ' '.join(a_toks)))
  print('%s%s' % (prefix, ' '.join(b_toks)))

def parse_entry(line):
  """Parse an entry from the CCG lexicon."""
  return tuple(line.strip().split(' :- NP : '))

def get_ccg_lexicon():
  lexicon = LexiconReplace()
  filename = os.path.join(LEXICON_DIR, 'atis-lexicon-for-replace.txt')
  entries = []
  with open(filename) as f:
    for line in f:
      x, y = line.strip().split(' :- NP : ')
      entries.append((x, y))
  lexicon.add_entries(entries)
  return lexicon

def get_lexicon(basename='', newname=''):
  return get_ccg_lexicon()
  #return get_lexicon_from_raw_lexicon_then_write(basename, newname)

def extract_entity_from_action(action):
  entity = ''
  if action.startswith('add_entity'):
    entity = action[action.index(':-:')+3:]
  return entity

if __name__ == '__main__':
  # Print out the lexicon
  basename = 'atis-lexicon-raw.txt'
  newname = 'atis-lexicon-for-replace.txt'
  lex = get_lexicon(basename, newname)

  entries = lex.entries

  print('Lexicon entries:')
  for name, entity_list in lex.entries.items():
    print('  %s -> %s' % (name, entity_list))

  file_name = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action_entity\\action\\atis\\action0\\atis_test.tsv")

  outfile_name = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                              "seq2action_entity\\debug\\atis1.txt")
  with open(outfile_name, 'w') as o_f:
    with open(file_name) as f:
      for line in f:
        words = line.split('\t')[0].split(' ')
        print('words: %s' % ' '.join(words), file=o_f)
        y_toks = line.split('\t')[1].split(' ')
        entities = [entity.replace(':-:', ':=:') for entity in lex.map_over_sentence(words)]
        #print('-' * 80)
        #print_aligned(words, entities, indent=2)
        #print(entities)
        copy_toks = [x if x else '<COPY>' for x in entities]
        print(copy_toks, file=o_f)
        y_in_x_inds = ([
                         [int(x_tok == extract_entity_from_action(y_tok)) for x_tok in copy_toks] + [0]
                         for y_tok in y_toks
                       ])
        #print('len of words: ', len(words))
        #print('len of y_toks: ', len(y_toks))
        #print('len = ', len(y_in_x_inds))
        #print('len of row: ', len(y_in_x_inds[0]))
        print('y_toks: ', ' '.join(y_toks), file=o_f)

        entity_in_nl_set = set()
        entity_in_lf_set = set()

        for copy_tok in copy_toks:
          if not copy_tok == '<COPY>':
            entity_list = copy_tok.split(' ')
            for entity in entity_list:
              entity_in_nl_set.add(entity)

        for y_tok in y_toks:
          if y_tok.startswith('add_entity_node:-:'):
            #print('y_tok: %s' % y_tok)
            entity = y_tok[y_tok.index(':-:')+3:]
            entity_in_lf_set.add(entity)

        entity_share = entity_in_nl_set & entity_in_lf_set

        if not len(entity_share) == len(entity_in_nl_set):
          print('error 1 : entity list [%s] not in nl' % (entity_in_nl_set - entity_share), file=o_f)

        if not len(entity_share) == len(entity_in_lf_set):
          print('error 2: entity list [%s] not in lf' % (entity_in_lf_set - entity_share), file=o_f)

        for ii in range(len(y_in_x_inds)):
          #print(y_in_x_inds[ii])
          pass