FFMPEG_BINARY = '/usr/local/bin/ffmpeg'

import os, sys, re, random
from moviepy.editor import *


def convert_timespan(timespan):
    start, end = timespan.split('-->')
    start = convert_timestamp(start)
    end = convert_timestamp(end)
    return start, end

def convert_timestamp(timestamp):
    timestamp = timestamp.strip()
    chunk, millis = timestamp.split(',')
    hours, minutes, seconds = chunk.split(':')
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    seconds = seconds + hours * 60 * 60 + minutes * 60 + float(millis)/1000
    return seconds

search = sys.argv[1]
maxclips = int(sys.argv[2])

srts = [f for f in os.listdir('./') if f.lower().endswith('srt')]

composition = []

for srt in srts:
    file = open(srt, 'r')
    lines = file.readlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if re.search(search, line, re.IGNORECASE):
            j = 1
            previous_line = lines[i-j]
            while (previous_line.find('-->') == -1):
                j += 1
                previous_line = lines[i-j]
            previous_line = previous_line.strip()
            start, end = convert_timespan(previous_line)
            composition.append({'file': srt.replace('.srt', '.avi'), 'time': previous_line, 'start': start, 'end': end, 'line': line})

    file.close()

clips = []
composition = composition[:maxclips]

print "creating clips"
time = 0
for i, c in enumerate(composition):
    line = c['line']
    index = line.find(search)
    position = index / len(line)
    start = c['start']
    end = c['end']
    duration = end - start

    print "{0}: {1} to {2}".format(line, start, end)

    clip = VideoFileClip(c['file'])
    clip = clip.subclip(start, end)
    clip = clip.set_start(time)
    clip = clip.set_end(time + (end - start))
    clips.append(clip)
    time += end - start

print "stitching it together"
video = concatenate(clips)

try:
    print "saving file"
    video.to_videofile("test_output.mp4")
except:
    print 'NO'
