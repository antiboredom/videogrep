"""
This script will remove silences from videos, based on word-level timestamps
Adjust the min_duration variable to change the duration of silences to remove

to run: python3 remove_silences.py SOMEVIDEO.mp4
"""

import sys
from videogrep import parse_transcript, create_supercut_in_batches

# the min duration of silences to remove
min_duration = 1.0

filenames = sys.argv[1:]

clips = []

for filename in filenames:
    timestamps = parse_transcript(filename)

    words = []
    for sentence in timestamps:
        words += sentence['words']

    clip = {'start': words[0]['start'], 'end': words[0]['end'], 'file': filename}

    for word1, word2 in zip(words[:-2], words[1:]):
        silence_start = word1['end']
        silence_end = word2['start']
        duration = silence_end - silence_start

        if duration < min_duration:
            clip['end'] = word2['end']

        elif duration >= min_duration:
            clip['end'] = word1['end']
            clips.append(clip)
            clip = {'start': word2['start'], 'end': word2['end'], 'file': filename}

create_supercut_in_batches(clips, 'no_silences.mp4')
