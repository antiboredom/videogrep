FFMPEG_BINARY = '/usr/local/bin/ffmpeg'

import os, re, random
import search as Search
from collections import OrderedDict
from moviepy.editor import *

usable_extensions = ['mp4', 'avi', 'mov']

def convert_timespan(timespan):
    """Converts an srt timespan into a start and end timestamp"""
    start, end = timespan.split('-->')
    start = convert_timestamp(start)
    end = convert_timestamp(end)
    return start, end

def convert_timestamp(timestamp):
    """Converts an srt timestamp into seconds"""
    timestamp = timestamp.strip()
    chunk, millis = timestamp.split(',')
    hours, minutes, seconds = chunk.split(':')
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    seconds = seconds + hours * 60 * 60 + minutes * 60 + float(millis)/1000
    return seconds

def clean_srt(srt):
    """Removes damaging line breaks and numbers from srt files and returns a dictionary"""
    f = open(srt, 'r')
    text = f.read()
    f.close()
    text = re.sub(r'^\d+[\n\r]', '', text, flags=re.MULTILINE)
    lines = text.splitlines()
    output = OrderedDict()
    key = ''

    for line in lines:
        line = line.strip()
        if line.find('-->') > -1:
            key = line
            output[key] = ''
        else:
            if key != '':
                output[key] += line + ' '

    return output

def demo_supercut(composition):
    for i, c in enumerate(composition):
        line = c['line']
        start = c['start']
        end = c['end']
        print "{1} to {2}:\t{0}".format(line, start, end)

def create_supercut(composition, outputfile):
    print "Creating clips"
    clips = []
    time = 0
    for i, c in enumerate(composition):
        line = c['line']
        start = c['start']
        end = c['end']
        duration = end - start

        print "{1} to {2}:\t{0}".format(line, start, end)

        clip = VideoFileClip(c['file'])
        clip = clip.subclip(start, end)
        clip = clip.set_start(time)
        clip = clip.set_end(time + (end - start))
        clips.append(clip)
        time += end - start

    video = concatenate(clips)

    try:
        video.to_videofile(outputfile)
    except:
        print "Sorry, couldn't output your video file"


def search_line(line, search, searchtype):
    if searchtype == 're':
        return re.search(search, line, re.IGNORECASE)
    elif searchtype == 'pos':
        return Search.search_out(line, search)
    elif searchtype == 'hyper':
        return Search.hypernym_search(line, search)


def videogrep(inputfile, outputfile, search, searchtype, maxclips, test=False, randomize=False):
    srts = []

    if os.path.isfile(inputfile):
        filename = inputfile.split('.')
        filename[-1] = 'srt'
        srts = ['.'.join(filename)]

    elif os.path.isdir(inputfile):
        if inputfile.endswith('/') == False:
            inputfile += '/'
        srts = [inputfile + f for f in os.listdir(inputfile) if f.lower().endswith('srt')]

    else:
        print 'no file found'
        return False

    composition = []

    for srt in srts:
        lines = clean_srt(srt)
        for timespan in lines.keys():
            line = lines[timespan].strip()
            if search_line(line, search, searchtype):
                start, end = convert_timespan(timespan)
                for ext in usable_extensions:
                    videofile = srt.replace('.srt', '.' + ext)
                    if os.path.isfile(videofile):
                        composition.append({'file': videofile, 'time': timespan, 'start': start, 'end': end, 'line': line})

    composition = composition[:maxclips]

    if randomize == True:
        random.shuffle(composition)

    if test == True:
        demo_supercut(composition)
    else:
        create_supercut(composition, outputfile)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate a "supercut" of one or more video files by searching through subtitle tracks.')
    parser.add_argument('--input', '-i', dest='inputfile', required=True, help='video or subtitle file, or folder')
    parser.add_argument('--search', '-s', dest='search', required=True, help='search term')
    parser.add_argument('--search-type', '-st', dest='searchtype', default='re', choices=['re', 'pos', 'hyper'], help='type of search')
    parser.add_argument('--max-clips', '-m', dest='maxclips', default=100, help='maximum number of clips to use for the supercut')
    parser.add_argument('--output', '-o', dest='outputfile', default='supercut.mp4', help='name of output file')
    parser.add_argument('--test', '-t', action='store_true', help='show results without making the supercut')
    parser.add_argument('--randomize', '-r', action='store_true', help='randomize the clips')
    parser.add_argument('--youtube', '-yt', help='grab clips from youtube based on your search')

    args = parser.parse_args()

    videogrep(inputfile=args.inputfile, outputfile=args.outputfile, search=args.search, searchtype=args.searchtype, maxclips=args.maxclips, test=args.test, randomize=args.randomize)
