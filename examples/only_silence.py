import sys
from videogrep import parse_transcript, create_supercut

# the min and max duration of silences to extract
min_duration = 0.5
max_duration = 1.0

# value to to trim off the end of each clip
adjuster = 0.1


filenames = sys.argv[1:]

silences = []
for filename in filenames:
    timestamps = parse_transcript(filename)


    # this uses the sentences in the transcript
    # for sentence1, sentence2 in zip(timestamps[:-2], timestamps[1:]):
    #     start = sentence1['end']
    #     end = sentence2['start'] - adjuster
    #     duration = end - start
    #     if duration > min_duration and duration < max_duration:
    #        silences.append({'start': start, 'end': end, 'file': filename})

    # this uses the words, if available
    words = []
    for sentence in timestamps:
        words += sentence['words']

    for word1, word2 in zip(words[:-2], words[1:]):
        start = word1['end']
        end = word2['start'] - adjuster
        duration = end - start
        if duration > min_duration and duration < max_duration:
            silences.append({'start': start, 'end': end, 'file': filename})

create_supercut(silences, 'silences.mp4')
