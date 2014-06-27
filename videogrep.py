FFMPEG_BINARY = '/usr/local/bin/ffmpeg'

import os
import re
import random
import gc
import search as Search

from collections import OrderedDict
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.concatenate import concatenate

usable_extensions = ['mp4', 'avi', 'mov', 'mkv', 'm4v']
batch_size = 20
debug = False

def log(string):
    if debug:
        print "[+] {}".format(string)

def error(string):
    print "[!] {}".format(string)

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
    seconds = seconds + hours * 60 * 60 + minutes * 60 + float(millis) / 1000
    return seconds


def clean_srt(srt):
    """Removes damaging line breaks and numbers from srt files and returns a dictionary"""
    with open(srt, 'r') as f:
        text = f.read()
    text = re.sub(r'^\d+[\n\r]', '', text, flags=re.MULTILINE)
    lines = text.splitlines()
    output = OrderedDict()
    key = ''

    for line in lines:
        line = line.strip()
        if line.find('-->') > -1:
            key = line
            output[key] = ''
        elif key != '':
            output[key] += line + ' '

    return output


def cleanup_log_files(outputfile):
    d = os.path.dirname(os.path.abspath(outputfile))
    logfiles = [f for f in os.listdir(d) if f.endswith('ogg.log')]
    for f in logfiles:
        os.remove(f)


def demo_supercut(composition, padding):
    for i, c in enumerate(composition):
        line = c['line']
        start = c['start']
        end = c['end']
        if i > 0 and composition[i - 1]['file'] == c['file'] and start < composition[i - 1]['end']:
            start = start + padding
        print "{1} to {2}:\t{0}".format(line, start, end)


def create_supercut(composition, outputfile, padding):
    log("Creating clips.")
    demo_supercut(composition, padding)

    # add padding when necessary
    for (clip, nextclip) in zip(composition, composition[1:]):
        if ((nextclip['file'] == clip['file']) and (nextclip['start'] < clip['end'])):
            nextclip['start'] += padding

    # put all clips together:
    all_filenames = set([c['file'] for c in composition])
    videofileclips = dict([(f, VideoFileClip(f)) for f in all_filenames])
    cut_clips = [videofileclips[c['file']].subclip(c['start'], c['end']) for c in composition]

    log("Concatenating clips.")
    final_clip = concatenate(cut_clips)

    log("Writing ouput file.")
    final_clip.to_videofile(outputfile, codec="libx264")


def create_supercut_in_batches(composition, outputfile, padding):
    total_clips = len(composition)
    start_index = 0
    end_index = batch_size
    batch_comp = []
    while start_index < total_clips:
        filename = outputfile + '.tmp' + str(start_index) + '.mp4'
        try:
            create_supercut(composition[start_index:end_index], filename, padding)
            batch_comp.append(filename)
            gc.collect()
            start_index += batch_size
            end_index += batch_size
        except:
            start_index += batch_size
            end_index += batch_size
            next

    clips = [VideoFileClip(filename) for filename in batch_comp]
    video = concatenate(clips)
    video.to_videofile(outputfile)

    #remove partial video files
    for filename in batch_comp:
        os.remove(filename)

    cleanup_log_files(outputfile)


def search_line(line, search, searchtype):
    if searchtype == 're':
        return re.search(search, line)  #, re.IGNORECASE)
    elif searchtype == 'pos':
        return Search.search_out(line, search)
    elif searchtype == 'hyper':
        return Search.hypernym_search(line, search)


def get_subtitle_files(inputfile):
    """Returns a list of subtitle files"""
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
        error("No subtitle files were found.")
        exit(1)

    return srts


def videogrep(inputfile, outputfile, search, searchtype, maxclips=0, padding=0, test=False, randomize=False, sync=0):
    srts = get_subtitle_files(inputfile)

    padding = padding / 1000.0
    sync = sync / 1000.0
    composition = []
    foundSearchTerm = False

    # Iterate over each subtitles file.
    for srt in srts:

        print srt
        lines = clean_srt(srt)

        videofile = ""
        foundVideoFile = False

        log("Searching for video file corresponding to '{}'.".format(srt))
        for ext in usable_extensions:
            tempVideoFile = srt.replace('.srt', '.' + ext)
            if os.path.isfile(tempVideoFile):
                videofile = tempVideoFile
                foundVideoFile = True
                log("Found '{}'.".format(tempVideoFile))

        # If a correspndong video file was found for this subtitles file...
        if foundVideoFile:

            # Check that the subtitles file contains subtitles.
            if lines:

                # Iterate over each line in the current subtitles file.
                for timespan in lines.keys():
                    line = lines[timespan].strip()

                    # If this line contains the search term
                    if search_line(line, search, searchtype):

                        foundSearchTerm = True

                        # Extract the timespan for this subtitle.
                        start, end = convert_timespan(timespan)
                        start = start + sync - padding
                        end = end + sync + padding

                        # Record this occurance of the search term.
                        composition.append({'file': videofile, 'time': timespan, 'start': start, 'end': end, 'line': line})

                # If the search was unsuccessful.
                if foundSearchTerm == False:
                    error("Search term '{}' was not found is subtitle \
                           file '{}'.".format(search, srt))

            # If no subtitles were found in the current file.
            else:
                error("Subtitle file '{}' is empty.".format(srt))

        # If no video file was found...
        else:
            error("No video file was found which corresponds to subtitle file '{}'.".format(srt))
            error("The following video formats are currently supported:")
            extList = ""
            for ext in usable_extensions:
                extList += ext + ", "
            print extList

    # If the search term was not found in any subtitle file...
    if foundSearchTerm == False:
        error("Search term '{}' was not found in any file.".format(search))
        exit(1)

    else:
        log("Search term '{search}' was found in {occurences} places.".\
            format(search=search, occurences=len(composition)))

        if maxclips > 0:
            composition = composition[:maxclips]

        if randomize == True:
            random.shuffle(composition)

        if test == True:
            demo_supercut(composition, padding)
        elif len(composition) > batch_size:
            log("Starting batch job.")
            create_supercut_in_batches(composition, outputfile, padding)
        else:
            create_supercut(composition, outputfile, padding)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate a "supercut" of one or more video files by searching through subtitle tracks.')
    parser.add_argument('--input', '-i', dest='inputfile', required=True, help='video or subtitle file, or folder')
    parser.add_argument('--search', '-s', dest='search', required=True, help='search term')
    parser.add_argument('--search-type', '-st', dest='searchtype', default='re', choices=['re', 'pos', 'hyper'], help='type of search')
    parser.add_argument('--max-clips', '-m', dest='maxclips', type=int, default=0, help='maximum number of clips to use for the supercut')
    parser.add_argument('--output', '-o', dest='outputfile', default='supercut.mp4', help='name of output file')
    parser.add_argument('--test', '-t', action='store_true', help='show results without making the supercut')
    parser.add_argument('--randomize', '-r', action='store_true', help='randomize the clips')
    parser.add_argument('--youtube', '-yt', help='grab clips from youtube based on your search')
    parser.add_argument('--padding', '-p', dest='padding', default=0, type=int, help='padding in milliseconds to add to the start and end of each clip')
    parser.add_argument('--resyncsubs', '-rs', dest='sync', default=0, type=int, help='Subtitle re-synch delay +/- in milliseconds')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print log messages')

    args = parser.parse_args()

    videogrep(args.inputfile, args.outputfile, args.search, args.searchtype, args.maxclips, args.padding, args.test, args.randomize, args.sync)


