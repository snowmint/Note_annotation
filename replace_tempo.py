import os
import sys
import fileinput
import argparse
import re

def arg_parse_init():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path",
                        type=str,
                        help="Given the folder path of the .xml files.")
    args = parser.parse_args()
    return parser, args

def flatten(input_list):
    return [item for sublist in input_list for item in sublist]

parser, args = arg_parse_init()

filename = args.path

# m = re.search('AAA(.+?)ZZZ', text)
#re.search('\tempo (.+?) \', line)

#input file
print(filename)
fin = open(filename, "rt")
#output file to write the result to
fout = open("./" + filename.split('.')[1] + "_replace.ly", "wt")
#for each line in the input file
for line in fin:
	#read replace the string and write to output file
    line = line.replace("PianoStaff", "Staff")
    line = line.replace("acoustic grand", "violin")
    line = line.replace("Piano", "Violin")

    finded = re.findall(r"\\tempo (.*?) \}", line, re.DOTALL)
    finded2 = re.findall(r"\\tempo (.*?) \\", line, re.DOTALL)
    finded3 = re.findall(r"\\tempo (.*?) \|", line, re.DOTALL)
    jointed_find =  finded + finded2 + finded3
    if jointed_find:
        print(jointed_find)
        for item in jointed_find:
            fout.write(line.replace(item, "4=60"))
    else:
        fout.write(line)
    

    # \set PianoStaff.instrumentName = "Piano"
    # \set PianoStaff.midiInstrument = #"acoustic grand"

    # \set Staff.instrumentName = "Violin"
    # \set Staff.shortInstrumentName = "Vln."

#close input and output files
fin.close()
fout.close()


#with fileinput.FileInput(filename, inplace=True, backup='.bak') as file:
#    for line in file:
#        re.search('\tempo (.+?) \', line)
#        print(line.replace(text_to_search, replacement_text), end='')



