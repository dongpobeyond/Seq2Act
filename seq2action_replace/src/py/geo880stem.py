"""Some code to deal with geo880 data."""
import collections
import glob
from nltk.stem.snowball import SnowballStemmer
import os
import re
import sys
import geolexicon

IN_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action\\action\\geo880\\seq0")
OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action\\action\\geo880\\stem_seq0")

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
    for x, y in out_data:
      #print >> f, '%s\t%s' % (x, y)
      print('%s\t%s' % (x, y), file=f)

def process(filename, stemmer, lex):
  print('Processing %s' % filename)
  basename = os.path.basename(filename)
  
  in_data = read_examples(filename)
  out_data = []
  for (x_str, y_str) in in_data:
      x_toks = x_str.split(' ')
      entities = [entity.replace(':-:', ':=:') for entity in lex.map_over_sentence(x_toks)]
      copy_toks = [x if x else '<COPY>' for x in entities]
      x_stem_toks = []
      for ii in range(len(x_toks)):
          w = x_toks[ii]
          if copy_toks[ii] == '<COPY>':
              w = stemmer.stem(w)
          x_stem_toks.append(w)
      x_stem_str = ' '.join(x_stem_toks)
      print('copy_toks (%d) : ' % len(copy_toks), copy_toks)
      print('x_str (%d) : ' % len(x_toks), x_str)
      print('x_stem_str (%d) : ' % len(x_stem_toks), x_stem_str)
      print('x_str == x_stem_str : ', x_str == x_stem_str)
      out_data.append((x_stem_str, y_str))
  write(basename, out_data)

def main():
  if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)
  stemmer = SnowballStemmer("english")
  lex = geolexicon.get_lexicon()
  for filename in sorted(glob.glob(os.path.join(IN_DIR, '*.tsv'))):
    process(filename, stemmer, lex)
  print('xin')

if __name__ == '__main__':
  main()
