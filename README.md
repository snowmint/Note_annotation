# Note_annotation
Turn XML score into note annotation automatically. Combine Music21 and PrettyMIDI method to double check.

### 1. Turn the .xml file into .ly
Ideally, I want to eliminate all the decorations, like accent, staccato, any kind of ornament, and tempo-related expression.

Such as `--nd, do not convert directions (^, _ or -) for articulations, dynamics, etc.`
#### Command example: `musicxml2ly -v --nd --midi --output="1_Bach_Prelude1.ly" ./1_Bach_Prelude1.xml`

### 2. Convert the instrument into String instrument
In the .ly file, convert the instrument into Violin or Cello, no matter what kind of instrument the score was originally made for, because the String instrument will get a more stable note duration of MIDI file than the Woodwind or Piano.

### 3. Set tempo to BPM=60
In the .ly file, eliminate all the tempo expressions, and set the tempo to BPM=60.
For the same reason as 2nd step, this step aims to get a more stable note duration.

#### The steps 2 and 3 I wrote a python code to replace the tempo and want to change the instrument clef, see the file `replace_tempo.py`.
#### Command example: `python replace_tempo.py --path ./1_Bach_Prelude1.ly`, then output the file named just add the `_replace` afterward, like: `1_Bach_Prelude1_replace.ly`

### 4. Convert .ly file into MIDI file
Then use the lilypond command `lilypond -dmidi-extension=mid 1_Bach_Prelude1_replace.ly` to convert the .ly file into a .mid file.
The output file has 2 formats PDF and MIDI, the filename here called: `1_Bach_Prelude1_replace.mid` and `1_Bach_Prelude1_replace.pdf`

#### Problem: After I change the tempo and instrument by the command `lilypond -dmidi-extension=mid MyFile.ly`, the output .pdf show the change of instrument and tempo, but the .mid file didn't apply the instrument change....

### 5. Get note annotation, note by note
Using the MIDI and original XML file, I can use my python script to get each note’s information, specifically, the attribute I want is listed below: `['Onset', 'Offset', 'MIDI number', 'Pitch name', 'Duration', 'Staff', 'Measure', 'Beat in Measure']`, see the file `merge_music21_prettyMIDI_get_annotation.py`

I've done the few annotations by manually going through steps 1~4, now I want to automate the full workflow, the target annotation example is put in the directory, ./ideal_piano_example.
