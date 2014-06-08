FFMPEG_BINARY = '/usr/local/bin/ffmpeg'

import os, re, random, gc
import ngrams
import search as Search
from collections import OrderedDict
from moviepy.editor import *

usable_extensions = ['mp4', 'avi', 'mov']
batch_size = 30

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

def demo_supercut(composition, padding):
    for i, c in enumerate(composition):
        line = c['line']
        start = c['start']
        end = c['end']
        if i > 0 and composition[i-1]['file'] == c['file'] and start < composition[i-1]['end']:
            start = start + padding
        print "{1} to {2}:\t{0}".format(line, start, end)

def create_supercut(composition, outputfile, padding):
    print "Creating clips"
    clips = []
    time = 0
    for i, c in enumerate(composition):
        line = c['line']
        start = c['start']
        end = c['end']
        if i > 0 and composition[i-1]['file'] == c['file'] and start < composition[i-1]['end']:
            start = start + padding

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

def create_supercut_in_batches(composition, outputfile, padding):
    total_clips = len(composition)
    start_index = 0
    end_index = batch_size
    batch_comp = []
    while start_index < total_clips:
        filename = outputfile + '.tmp' + str(start_index) + '.mp4'
        end = 0
        for clip in composition[start_index:end_index]:
            end += clip['end'] - clip['start']
        try:
            create_supercut(composition[start_index:end_index], filename, padding)
            batch_comp.append({'file': filename, 'start': 0, 'end': end, 'line': 'PARTIAL SILENCE'})
            gc.collect()
        except:
            next
        start_index += batch_size
        end_index += batch_size

    clips = [VideoFileClip(batch['file']) for batch in batch_comp]
    video = concatenate(clips)
    video.to_videofile(outputfile)

    for batch in batch_comp:
        os.remove(batch['file'])

def search_line(line, search, searchtype):
    if searchtype == 're':
        return re.search(search, line)#, re.IGNORECASE)
    elif searchtype == 'pos':
        return Search.search_out(line, search)
    elif searchtype == 'hyper':
        return Search.hypernym_search(line, search)


def videogrep(inputfile, outputfile, search, searchtype, maxclips, padding=0, test=False, randomize=False):
    srts = []
    padding = padding / 1000.0

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
                        start = start - padding
                        end = end + padding
                        composition.append({'file': videofile, 'time': timespan, 'start': start, 'end': end, 'line': line})

    composition = composition[:maxclips]

    if randomize == True:
        random.shuffle(composition)

    if test == True:
        demo_supercut(composition, padding)
    else:
        if len(composition) > batch_size:
            create_supercut_in_batches(composition, outputfile, padding)
        else:
            create_supercut(composition, outputfile, padding)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate a "supercut" of one or more video files by searching through subtitle tracks.')
    parser.add_argument('--input', '-i', dest='inputfile', required=True, help='video or subtitle file, or folder')
    parser.add_argument('--search', '-s', dest='search', required=True, help='search term')
    parser.add_argument('--search-type', '-st', dest='searchtype', default='re', choices=['re', 'pos', 'hyper'], help='type of search')
    parser.add_argument('--max-clips', '-m', dest='maxclips', type=int, default=100, help='maximum number of clips to use for the supercut')
    parser.add_argument('--output', '-o', dest='outputfile', default='supercut.mp4', help='name of output file')
    parser.add_argument('--test', '-t', action='store_true', help='show results without making the supercut')
    parser.add_argument('--randomize', '-r', action='store_true', help='randomize the clips')
    parser.add_argument('--youtube', '-yt', help='grab clips from youtube based on your search')
    parser.add_argument('--padding', '-p', dest='padding', default=0, type=int, help='padding in milliseconds to add to the start and end of each clip')

    args = parser.parse_args()

    videogrep(args.inputfile, args.outputfile, args.search, args.searchtype, args.maxclips, args.padding, args.test, args.randomize)
