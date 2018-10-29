"""Some code to deal with geo880 data."""
import collections
import glob
import os
import re
import sys
import geolexiconreplace

IN_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action_entity\\action\\geo880\\action0")
OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action_entity\\action\\geo880\\entity_action0")

def read_examples(filename):
  examples = []
  with open(filename) as f:
    for line in f:
        utterance, logical_form = line.rstrip('\n').split('\t')
        examples.append((utterance, logical_form))
  return examples

def write(basename, out_data):
  out_path = os.path.join(OUT_DIR, basename)
  with open(out_path, 'w') as f:
    for x, y, z in out_data:
      print >> f, '%s\t%s\t%s' % (x, y, z)
      #print('%s\t%s\t%s' % (x, y, z), file=f)

def normalize_entity(entity):
    entity_type = entity[entity.index(':=:')+3:]
    return entity_type

def entity_in_y_str(entity_list_str, y_str):
    for entity in entity_list_str.split(' '):
        if entity in y_str:
            return True
    return False

def process(filename, lex):
  print('Processing %s' % filename)
  basename = os.path.basename(filename)
  
  in_data = read_examples(filename)
  out_data = []
  for (x_str, y_str) in in_data:
      local_entity_map = {}
      entity_count_map = {}
      x_toks = x_str.split(' ')
      y_toks = y_str.split(' ')
      entity_in_y = []
      for y_tok in y_toks:
          if y_tok.startswith('add_entity_node'):
              entity = y_tok[y_tok.index(':-:')+3:]
              entity_in_y.append(entity)
      entities = [entity.replace(':-:', ':=:') for entity in lex.map_over_sentence(x_toks)]
      copy_toks = [x if x else '<COPY>' for x in entities]
      print('copy_toks: ', copy_toks)
      x_new_toks = []
      y_new_toks = []
      ii = 0
      while ii < len(x_toks):
          name_toks = []
          while ii < len(x_toks) and not copy_toks[ii] == '<COPY>' and entity_in_y_str(copy_toks[ii], y_str):
            entity_list_str = copy_toks[ii]
            name_toks.append(x_toks[ii])
            ii += 1

          if name_toks == []:
              x_new_toks.append(x_toks[ii])
              ii += 1
          else:
              print('entity_list_str: ', entity_list_str)
              for entity in entity_list_str.split(' '):
                  if entity in entity_in_y:
                    normalized_entity = normalize_entity(entity)
                    if normalized_entity not in entity_count_map:
                        entity_count_map[normalized_entity] = 0
                    new_entity = 'ent' + str(entity_count_map[normalized_entity]) + ':=:' + normalized_entity
                    entity_count_map[normalized_entity] += 1
                    local_entity_map[entity] = new_entity
                    x_new_toks.append(new_entity)
                    break

      x_new_str = ' '.join(x_new_toks)
      print('entity in y: ', entity_in_y)
      print('local_entity_map: ', local_entity_map)
      print('entity_count_map: ', entity_count_map)
      for y_tok in y_toks:
          if y_tok.startswith('add_entity_node'):
              entity = y_tok[y_tok.index(':-:')+3:]
              new_entity = local_entity_map[entity]
              y_new_tok = y_tok.replace(entity, new_entity)
              y_new_toks.append(y_new_tok)
          else:
              y_new_toks.append(y_tok)

      y_new_str = ' '.join(y_new_toks)

      print('copy_toks (%d) : ' % len(copy_toks), copy_toks)
      print('local_entity_map: ', local_entity_map)
      print('x_str (%d) : ' % len(x_toks), x_str)
      print('x_new_str (%d) : ' % len(x_new_toks), x_new_str)
      print('y_str (%d) : ' % len(y_toks), y_str)
      print('y_new_str (%d) : ' % len(y_new_toks), y_new_str)
      if not len(local_entity_map) == len(entity_in_y):
          print('error: entity number does not match!')
      local_entity_map_list = []
      for entity_key in local_entity_map:
        entity_value = local_entity_map[entity_key]
        local_entity_map_list.append(entity_value + ':::' + entity_key)
      local_entity_map_str = ' '.join(local_entity_map_list)
      out_data.append((x_new_str, y_new_str, local_entity_map_str))
  write(basename, out_data)

def main():
  if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)
  lex = geolexiconreplace.get_lexicon()
  for filename in sorted(glob.glob(os.path.join(IN_DIR, '*.tsv'))):
    process(filename, lex)
  print('xin')

if __name__ == '__main__':
  main()
