"""Reads a lexicon for GEO.

A lexicon simply maps natural language phrases to identifiers in the GEO database.
"""
import collections
import os
import re
import sys

from lexicon import Lexicon

LEXICON_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'lexicon')

def get_lexicon_from_raw_lexicon_then_write(basename, newname):
  filename = os.path.join(LEXICON_DIR, basename)
  newfilename = os.path.join(LEXICON_DIR, newname)
  lex = Lexicon()
  entries = []
  with open(filename) as f:
    for line in f:
      lexicon_tuple = parse_entry(line)
      name = lexicon_tuple[0]
      entity = normalize_entity(lexicon_tuple[1])
      if entity == '':
        continue
      entries.append((name, entity))
  lex.add_entries(entries, False)
  with open(newfilename, 'w') as f:
    for name, entity in lex.entries.items():
      #print('%s :- NP : %s' % (name, entity), file=f)
      pass
  return lex

def normalize_entity(entity):
  if ' ' in entity or ':' not in entity:
    print('wrong entity: ', entity)

  new_entity = ''
  entity_cat_map = {}
  entity_cat_map['s'] = 'state'
  entity_cat_map['c'] = 'city'
  entity_cat_map['r'] = 'river'
  entity_cat_map['l'] = 'lake'
  entity_cat_map['m'] = 'mountain'
  entity_cat_map['co'] = 'country'
  entity_cat_map['p'] = 'place'
  entity_name = entity[:entity.index(':')]
  entity_cat = entity[entity.index(':')+1:]
  if entity_cat not in entity_cat_map:
    print('category %s not in entity_cat_map: ' % entity_cat)
    return new_entity
  new_entity = entity_name + ':-:' + entity_cat_map[entity_cat]
  return new_entity

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
  lexicon = Lexicon()
  filename = os.path.join(LEXICON_DIR, 'geo-lexicon.txt')
  entries = []
  with open(filename) as f:
    for line in f:
      x, y = line.strip().split(' :- NP : ')
      entries.append((x, y))
  lexicon.add_entries(entries, False)
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
  basename = 'np-fixedlex.geo'
  newname = 'geo-lexicon.txt'
  lex = get_lexicon(basename, newname)

  entries = lex.entries
  name = 'the mississippi'
  if name in entries:
    print(entries[name])

  print('Lexicon entries:')
  for name, entity in lex.entries.items():
    print('  %s -> %s' % (name, entity))
  print('Unique word map:')
  for word, entity in lex.unique_word_map.items():
    print('  %s -> %s'  % (word, entity))

  file_name = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action_entity\\action\\geo880\\action0\\geo880_test280.tsv")

  with open(file_name) as f:
    for line in f:
      words = line.split('\t')[0].split(' ')
      y_toks = line.split('\t')[1].split(' ')
      entities = [entity.replace(':-:', ':=:') for entity in lex.map_over_sentence(words)]
      print('-' * 80)
      print_aligned(words, entities, indent=2)
      print(entities)
      copy_toks = [x if x else '<COPY>' for x in entities]
      print(copy_toks)
      y_in_x_inds = ([
                       [int(x_tok == extract_entity_from_action(y_tok)) for x_tok in copy_toks] + [0]
                       for y_tok in y_toks
                     ])
      print('len of words: ', len(words))
      print('len of y_toks: ', len(y_toks))
      print('len = ', len(y_in_x_inds))
      print('len of row: ', len(y_in_x_inds[0]))
      print('y_toks: ', ' '.join(y_toks))
      entity_flag = False
      lex_name_exist_flag = False
      lex_entity_exist_flag = False
      for c_tok in copy_toks:
        if c_tok == '<COPY>':
          continue
        else:
          lex_name_exist_flag = True
        if entity_flag:
          break
        for y_tok in y_toks:
          if c_tok in y_tok:
            entity_flag = True
            break
      for y_tok in y_toks:
        if ':=:' in y_tok:
          lex_entity_exist_flag = True
          break
      if lex_name_exist_flag and not entity_flag:
        print('error 1: entity lexicon is wrong!!!!!')
      if lex_entity_exist_flag and not lex_name_exist_flag:
        print('error 2: lex entity exists, but lex name not!!!!')
      for ii in range(len(y_in_x_inds)):
        #print(y_in_x_inds[ii])
        pass