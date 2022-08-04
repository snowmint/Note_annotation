import sys
import os
from pathlib import Path
import numpy as np
import pandas as pd
import glob
import argparse
import csv
import re
import operator

import music21 as m21
import pretty_midi
import mir_eval.display
import librosa.display
import IPython.display as ipd

from matplotlib import pyplot as plt
from matplotlib import patches

sys.path.append('./')

piano_imcomplete_measure = ['4_Mozart_PianoSonata_No.11_Amajor_K.331W_rondo', '6_Brahms_Intermezzo_Op.118_No.2', '9_Chopin_Nocturne_Op.9_No.2_EflatMajor']
piano_imcomplete_duration = [-1, -1, -0.5]
violin_imcomplete_measure = ['Bach1']
violin_imcomplete_duration = [-0.25]
cello_imcomplete_measure = ['2_Bach_CelloSuite_No.3_BWV1009']
cello_imcomplete_duration = [-1]

downbeat_directory = {'piano':'./Beat_annotation/piano/dbeat/', 'violin':'./Beat_annotation/violin/dbeat/', 'cello':'./Beat_annotation/cello/dbeat/'}

def arg_parse_init():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path",
                        type=str,
                        help="Given the folder path of the .xml files.")
    args = parser.parse_args()
    return parser, args

def get_instrument(path_name):
    instrument = ''
    if 'piano' in path_name:
        instrument = 'piano'
    elif 'violin' in path_name:
        instrument = 'violin'
    elif 'cello' in path_name:
        instrument = 'cello'
    return instrument

def have_imcomplete(path_name, instrument):
    if instrument == 'piano':
        for index, item in enumerate(piano_imcomplete_measure):
            if item in path_name:
                return piano_imcomplete_duration[index], True
    if instrument == 'violin':
        for index, item in enumerate(violin_imcomplete_measure):
            if item in path_name:
                return violin_imcomplete_duration[index], True
    if instrument == 'cello':
        for index, item in enumerate(cello_imcomplete_measure):
            if item in path_name:
                return cello_imcomplete_duration[index], True
    return 0, False

def xml_to_list(xml, instrument, onset_adjust, measure_adjust):

    if isinstance(xml, str):
        xml_data = m21.converter.parse(xml)
    elif isinstance(xml, m21.stream.Score):
        xml_data = xml
    else:
        raise RuntimeError('midi must be a path to a midi file or music21.stream.Score')

    score = []
    i = 0
    for part in xml_data.parts:
        for note in part.stripTies().flat.notes:
            if note.isChord:
                onset = float(note.offset) + onset_adjust
                duration = float(note.duration.quarterLength) #duration = note.quarterLength
                offset = onset + duration

                for chord_note in note.pitches:
                    # volume = note.volume.realized
                    pitch = chord_note.ps
                    pitch_name = chord_note.nameWithOctave
                    pitch_name = pitch_name.replace("-", "b")
                    measure = float(note.measureNumber)-1 + measure_adjust
                    beat = float(note.beat)-1

                    score.append([onset, offset, pitch, pitch_name, duration, i, measure, beat])

            else:
                onset = float(note.offset) + onset_adjust
                duration = float(note.duration.quarterLength) #duration = note.quarterLength
                offset = onset + duration
                pitch = note.pitch.ps
                pitch_name = note.nameWithOctave
                pitch_name = pitch_name.replace("-", "b")
                measure = float(note.measureNumber)-1 + measure_adjust
                beat = float(note.beat)-1
                score.append([onset, offset, pitch, pitch_name, duration, i, measure, beat])
        i += 1
    score = sorted(score, key=lambda x: (x[0], x[2]))
    return score

def index_2d(score, value):
    length = len(score)
    for i in reversed(range(length-1)):
        if ((score[i][0] + score[i][4]) > score[length-1][0]) and (score[i][5] == score[length-1][5]) and (score[i][3] == score[length-1][3]):
            print(score[i][3], value, score[i][1], score[length-1][0])
            score[i][1] = score[length-1][0]
            score[i][4] = score[i][1] - score[i][0]

def midi_to_score(mid_data, got_instrument, onset_adjust, measure_adjust, midi_path_name, music21_df):
    print('There are {} time signature changes'.format(len(mid_data.time_signature_changes))) #not really....
    print('There are {} instruments'.format(len(mid_data.instruments)))
    #print('Instrument 0 has {} notes'.format(len(mid_data.instruments[0].notes)))
    #print('Instrument 1 has {} notes'.format(len(mid_data.instruments[1].notes)))

    # read downbeats file ##############################################
    downbeat_info = pd.DataFrame()
    number_of_file = midi_path_name.split('_')[0]
    root_path = downbeat_directory[got_instrument]
    downbeat_path_list = Path(root_path).glob('**/*.xlsx')

    for index, downbeat_path in enumerate(downbeat_path_list):
        str_path = str(downbeat_path)
        found_or_not = str_path.find((str(number_of_file) + "_"))
        if (found_or_not != -1):
            downbeat_info = pd.read_excel(downbeat_path, index_col=None, header=None)
            break
    ####################################################################
    score = []
    i = 0
    enharmonic = {"B":["A##", "B", "Cb"],
                  "Cb":["A##", "B", "Cb"],
                  "Bb":["A#", "Bb", "Cbb"],
                  "A#":["A#", "Bb", "Cbb"],
                  "A":["G##", "A", "Bbb"],
                  "G#":["G#", "Ab"],
                  "Ab":["G#", "Ab"],
                  "G":["F##", "G", "Abb"],
                  "F#":["E##", "F#", "Gb"],
                  "Gb":["E##", "F#", "Gb"],
                  "E#":["E#", "F", "Gbb"],
                  "F":["E#", "F", "Gbb"],
                  "E":["D##", "E", "Fb"],
                  "Fb":["D##", "E", "Fb"],
                  "D#":["D#", "Eb", "Fbb"],
                  "Eb":["D#", "Eb", "Fbb"],
                  "D":["C##", "D", "Ebb"],
                  "C#":["B##", "C#", "Db"],
                  "Db":["B##", "C#", "Db"],
                  "B#":["B#", "C", "Dbb"],
                  "C":["B#", "C", "Dbb"]}
    pitch_name_accumulate = {"B#":0, "C":0, "Dbb":0,
                            "B##":0, "C#":0, "Db":0,
                            "C##":0, "D":0,"Ebb":0,
                            "D#":0, "Eb":0, "Fbb":0,
                            "D##":0, "E":0, "Fb":0,
                            "E#":0, "F":0, "Gbb":0,
                            "E##":0, "F#":0, "Gb":0,
                            "F##":0, "G":0, "Abb":0,
                            "G#":0, "Ab":0,
                            "G##":0, "A":0, "Bbb":0,
                            "A#":0, "Bb":0, "Cbb":0,
                            "A##":0, "B":0, "Cb":0}

    for instruments in mid_data.instruments:
        for note in instruments.notes:
            duration = note.duration + 0.002083333333334
            onset = note.start + onset_adjust
            offset = note.start + duration + onset_adjust
            pitch = note.pitch
            duration = float('%f' % duration)
            onset = float('%f' % onset)
            offset = float('%f' % offset)

            # TODO: use music21 read xml's pitch_name
            #print(music21_df)
            get_pitch_name_df = music21_df[(music21_df['Onset'] == onset) & (music21_df['MIDI number'] == pitch)]
            #print("get_pitch_name_df", get_pitch_name_df)
            pitch_name = ""
            if get_pitch_name_df.empty: # can't find this note in music21
                #print("Missing in music21, so just use pretty_midi.note_number_to_name")
                old_pitch_name = pretty_midi.note_number_to_name(note.pitch)
                #print("** old pitch_name: ", pitch_name)
                # Don't just use pretty_midi.note_number_to_name
                pitch_wo_octave = re. sub(r"\d+", "", old_pitch_name)#''.join([i for i in pitch_name if not i.isdigit()])
                octave = re.findall(r'\d+', old_pitch_name)[0]#[int(s) for s in pitch_name.split() if s.isdigit()]
                #print("octave: ", octave)
                pitch_name_accumulate[pitch_wo_octave] += 1
                pitch_name_equivalence_list = enharmonic[pitch_wo_octave]
                selected = {x: pitch_name_accumulate[x] for x in pitch_name_equivalence_list}#select pitch_name_adjust column
                # Pick the most frequently use one as pitch_name
                if all(value == 0 for value in selected.values()):
                    pitch_name = pretty_midi.note_number_to_name(note.pitch)
                else:
                    max_selected = max(selected, key= lambda x: selected[x])
                    pitch_name = max_selected + octave
                if old_pitch_name != pitch_name:
                    print("selected: ", selected, " | max_selected: ", max_selected)
                    print("[*] old_pitch_name: " , old_pitch_name, " | new pitch_name: ", pitch_name, " | onset: ", onset)

                pitch_name_accumulate[pitch_wo_octave] -= 1
                pitch_name_accumulate[max_selected] += 1

            else:# use the note pitch_name in xml
                pitch_name = music21_df['Pitch name'][get_pitch_name_df.index[0]]
                pitch_wo_octave = re. sub(r"\d+", "", pitch_name)#''.join([i for i in pitch_name if not i.isdigit()])
                octave = re.findall(r'\d+', pitch_name)
                #print("pitch_wo_octave", pitch_wo_octave)
                pitch_name_accumulate[pitch_wo_octave] += 1
            #print("pitch_name:", pitch_name)

            staff = i
            get_measure_df = downbeat_info[downbeat_info[0] <= onset]
            get_measure = 0
            beat_in_measure = 0
            if get_measure_df.empty:
                get_measure = -1
                beat_in_measure = downbeat_info[0][1] + onset
            else:
                get_measure = get_measure_df.index[-1]
                beat_in_measure = onset - downbeat_info[0][get_measure]
            score.append([onset, offset, pitch, pitch_name, duration, i, get_measure, beat_in_measure])
            index_2d(score, pitch_name)
        i += 1
    return score

parser, args = arg_parse_init()
pathlist = Path(args.path).glob('**/*.mid')
pathlist_xml = Path(args.path).glob('**/*.xml')

note_count_midi = {}
music21_note_count = {}

for path, path_xml in zip(pathlist, pathlist_xml):
    print(path.name)
    path_name = path.name
    instrument = get_instrument(args.path)
    print(path)

    measure_adjust = 0
    onset_adjust, is_imcomplete = have_imcomplete(path_name, instrument)
    if is_imcomplete == True:
        measure_adjust = -1
    else:
        measure_adjust = 0
    print(onset_adjust, measure_adjust, is_imcomplete)

    # music21 ==================================================================
    xml_data = m21.converter.parse(path_xml)
    xml_list = xml_to_list(xml_data, instrument, onset_adjust, measure_adjust)
    music21_note_count[path.name] = len(xml_list)
    # Our Goal =  ['Onset', 'Offset = start + duration', 'Pitch in MIDI number', 'Pitch Name', 'Duration', 'Staff number', 'Measure', 'beat in measure']
    music21_df = pd.DataFrame(xml_list, columns=['Onset', 'Offset', 'MIDI number', 'Pitch name', 'Duration', 'Staff', 'Measure', 'Beat in Measure'])
    music21_df = music21_df.sort_values('Onset')
    # ==========================================================================

    mid_data = pretty_midi.PrettyMIDI('./' + str(path), initial_tempo=60)
    midi_score = midi_to_score(mid_data, instrument, onset_adjust, measure_adjust, path_name, music21_df)

    print("MIDI_score length: ", len(midi_score))
    note_count_midi[path.name] = len(midi_score)
    # Our Goal =  ['Onset', 'Offset = start + duration', 'Pitch in MIDI number', 'Pitch Name', 'Duration', 'Staff number', 'Measure', 'beat in measure']
    df = pd.DataFrame(midi_score, columns=['Onset', 'Offset', 'MIDI number', 'Pitch name', 'Duration', 'Staff', 'Measure', 'Beat in Measure']) # 'Measure', 'Beat in Measure'
    df = df.sort_values('Onset')
    print(df)

    # Write out the file as csv ================================================
    filepath = Path('./' + instrument + '_with_header/', str(path.name).split('.mid')[0] + '_annotation.csv')
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False)
    # ==========================================================================

print("Total Pretty MIDI note count:", note_count_midi)
print("Total Music21 note count: ", music21_note_count)

# pretty midi note attribute ===================================================
# dir(note): ['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__',
# '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__',
# '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__',
# '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__',
# '__subclasshook__', '__weakref__',
# 'duration', 'end', 'get_duration', 'pitch', 'start', 'velocity']


# WARNING: =====================================================================
# C:\Users\tp953\AppData\Local\Programs\Python\Python39\lib\site-packages
# \pretty_midi\pretty_midi.py:97:
# RuntimeWarning: Tempo, Key or Time signature change events found on non-zero tracks.
# This is not a valid type 0 or type 1 MIDI file.
# Tempo, Key or Time Signature may be wrong.
