import os
import sys

IN_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action\\ontology\\geobase.dlog")
OUT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "seq2action\\ontology\\geobase.txt")

def loadBase(infile):
    base_set = set()
    with open(infile) as f:
        for line in f:
            line = line.strip()
            line = line.replace('\'', '').replace(' ', '_')
            if line.startswith('state('):
                line = line[6:-2]
                parts = line.split(',')
                base = 'entity:\t' + parts[0] + '\t' + 'stateid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tstateid:' + parts[0] + '\ttype:state'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tstateid:' + parts[0] +  '\trel:loc\tcountryid:usa'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tstateid:' + parts[0] + '\trel:population\tpopvalue:' + parts[3]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tstateid:' + parts[0] + '\trel:area\tareavalue:' + parts[4]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tstateid:' + parts[0] + '\trel:size\tsizevalue:' + parts[4]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tstateid:' + parts[0] + '\trel:density\tdenvalue:' + str(float(parts[3])/float(parts[4]))
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tstateid:' + parts[0] + '\trel:capital\tcityid:' + parts[2]+ '_' + parts[1]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tcityid:' + parts[2]+ '_' + parts[1] + '\ttype:capital'
                if base not in base_set:
                    base_set.add(base)


                base = 'entity:\t' + parts[6] + ':' + parts[1] + '\t' + 'cityid:' + parts[6] + '_' + parts[1]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tcityid:' + parts[6] + '_' + parts[1] + '\ttype:city'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity:\t' + parts[6] + '\t' + 'cityid:' + parts[6]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tcityid:' + parts[6] + '\ttype:city'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcityid:' + parts[6] + '_' + parts[1] +   '\trel:loc\tstateid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcityid:' + parts[6] + '_' + parts[1] + '\trel:loc\tcountryid:usa'
                if base not in base_set:
                    base_set.add(base)

                base = 'entity:\t' + parts[7] + ':' + parts[1] + '\t' + 'cityid:' + parts[7] + '_' + parts[1]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tcityid:' + parts[7] + '_' + parts[1] + '\ttype:city'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity:\t' + parts[7] + '\t' + 'cityid:' + parts[7]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tcityid:' + parts[7] + '\ttype:city'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcityid:' + parts[7] + '_' + parts[1] + '\trel:loc\tstateid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcityid:' + parts[7] + '_' + parts[1] + '\trel:loc\tcountryid:usa'
                if base not in base_set:
                    base_set.add(base)

                base = 'entity:\t' + parts[8] + ':' + parts[1] + '\t' + 'cityid:' + parts[8] + '_' + parts[1]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tcityid:' + parts[8] + '_' + parts[1] + '\ttype:city'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity:\t' + parts[8] + '\t' + 'cityid:' + parts[8]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tcityid:' + parts[8] + '\ttype:city'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcityid:' + parts[8] + '_' + parts[1] + '\trel:loc\tstateid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcityid:' + parts[8] + '_' + parts[1] + '\trel:loc\tcountryid:usa'
                if base not in base_set:
                    base_set.add(base)

                base = 'entity:\t' + parts[9] + ':' + parts[1] + '\t' + 'cityid:' + parts[9] + '_' + parts[1]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tcityid:' + parts[9] + '_' + parts[1] + '\ttype:city'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity:\t' + parts[9] + '\t' + 'cityid:' + parts[9]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tcityid:' + parts[9] + '\ttype:city'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcityid:' + parts[9] + '_' + parts[1] + '\trel:loc\tstateid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcityid:' + parts[9] + '_' + parts[1] + '\trel:loc\tcountryid:usa'
                if base not in base_set:
                    base_set.add(base)

            elif line.startswith('city('):
                line = line[5:-2]
                parts = line.split(',')
                base = 'entity:\t' + parts[2] + ':' + parts[1] + '\t' + 'cityid:' + parts[2] + '_' + parts[1]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tcityid:' + parts[2] + '_' + parts[1] + '\ttype:city'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity:\t' + parts[2] + '\t' + 'cityid:' + parts[2]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tcityid:' + parts[2] + '\ttype:city'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcityid:' + parts[2] + '_' + parts[1] + '\trel:loc\tstateid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcityid:' + parts[2] + '_' + parts[1] + '\trel:loc\tcountryid:usa'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcityid:' + parts[2] + '_' + parts[1] + '\trel:population\t' + 'popvalue:' + parts[3]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcityid:' + parts[2] + '_' + parts[1] + '\trel:size\t' + 'sizevalue:' + parts[3]
                if base not in base_set:
                    base_set.add(base)

            elif line.startswith('river('):
                line = line[6:-2].replace('[', '').replace(']','')
                parts = line.split(',')
                base = 'entity:\t' + parts[0] + '\t' + 'riverid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\triverid:' + parts[0] + '\ttype:river'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\triverid:' + parts[0] + '\trel:loc\tcountryid:usa'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\triverid:' + parts[0] + '\trel:traverse\tcountryid:usa'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\triverid:' + parts[0] + '\trel:len\tlenvalue:' + parts[1]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\triverid:' + parts[0] + '\trel:size\tsizevalue:' + parts[1]
                if base not in base_set:
                    base_set.add(base)
                for part in parts[2:]:
                    base = 'entity_rel:\triverid:' + parts[0] + '\trel:loc\tstateid:' + part
                    if base not in base_set:
                        base_set.add(base)
                    base = 'entity_rel:\triverid:' + parts[0] + '\trel:traverse\tstateid:' + part
                    if base not in base_set:
                        base_set.add(base)

            elif line.startswith('lake('):
                line = line[5:-2].replace('[', '').replace(']', '')
                parts = line.split(',')
                base = 'entity:\t' + parts[0] + '\t' + 'lakeid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tlakeid:' + parts[0] + '\ttype:lake'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tlakeid:' + parts[0] + '\trel:loc\tcountryid:usa'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tlakeid:' + parts[0] + '\trel:area\tareavalue:' + parts[1]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tlakeid:' + parts[0] + '\trel:size\tsizevalue:' + parts[1]
                if base not in base_set:
                    base_set.add(base)
                for part in parts[2:]:
                    base = 'entity_rel:\tlakeid:' + parts[0] + '\trel:loc\tstateid:' + part
                    if base not in base_set:
                        base_set.add(base)

            elif line.startswith('mountain('):
                line = line[9:-2].replace('[', '').replace(']', '')
                parts = line.split(',')
                base = 'entity:\t' + parts[2] + '\t' + 'mountainid:' + parts[2]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tmountainid:' + parts[2] + '\ttype:mountain'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tmountainid:' + parts[2] + '\trel:loc\tcountryid:usa'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tmountainid:' + parts[2] + '\trel:loc\tstateid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tmountainid:' + parts[2] + '\trel:elevation\televalue:' + parts[3]
                if base not in base_set:
                    base_set.add(base)

            elif line.startswith('highlow('):
                line = line[8:-2].replace('[', '').replace(']', '')
                parts = line.split(',')
                base = 'entity:\t' + parts[2] + '\t' + 'placeid:' + parts[2]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity:\t' + parts[4] + '\t' + 'placeid:' + parts[4]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tplaceid:' + parts[2] + '\ttype:place'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tplaceid:' + parts[4] + '\ttype:place'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tplaceid:' + parts[2] + '\trel:loc\tcountryid:usa'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tplaceid:' + parts[4] + '\trel:loc\tcountryid:usa'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tplaceid:' + parts[2] + '\trel:loc\tstateid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tplaceid:' + parts[4] + '\trel:loc\tstateid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tplaceid:' + parts[2] + '\trel:high_point\tstateid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tplaceid:' + parts[4] + '\trel:low_point\tstateid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)

            elif line.startswith('border('):
                line = line[7:-2].replace('[', '').replace(']', '')
                parts = line.split(',')
                for part in parts[2:]:
                    base = 'entity_rel:\tstateid:' + parts[0] + '\trel:next_to\tstateid:' + part
                    if base not in base_set:
                        base_set.add(base)
                    base = 'entity_rel:\tstateid:' + part + '\trel:next_to\tstateid:' + parts[0]
                    if base not in base_set:
                        base_set.add(base)

            elif line.startswith('country('):
                line = line[8:-2].replace('[', '').replace(']', '')
                parts = line.split(',')
                print(parts)
                base = 'entity:\t' + parts[0] + '\t' + 'countryid:' + parts[0]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_type:\tcountryid:' + parts[0] + '\ttype:country'
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcountryid:' + parts[0] + '\trel:population\tareavalue:' + parts[1]
                if base not in base_set:
                    base_set.add(base)
                base = 'entity_rel:\tcountryid:' + parts[0] + '\trel:area\tareavalue:' + parts[2]
                if base not in base_set:
                    base_set.add(base)

            else:
                pass

    print('size: ', len(base_set))
    return base_set

def writeBase(bases, outfile):
    with open(outfile, "w") as f:
        for base in bases:
            print('%s' % base, file=f)

def process(infile, outfile):
    bases = loadBase(infile)
    writeBase(bases, outfile)

def main():
    process(IN_FILE, OUT_FILE)


if __name__ == '__main__':
    main()
