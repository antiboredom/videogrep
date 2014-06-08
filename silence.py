import videogrep
import os

def silence(inputfile, outputfile, maxclips, minsilence, maxsilence, padding=0, test=False, randomize=False):
    if os.path.isfile(inputfile):
        filename = inputfile.split('.')
        filename[-1] = 'srt'
        srts = ['.'.join(filename)]

    elif os.path.isdir(inputfile):
        if inputfile.endswith('/') == False:
            inputfile += '/'
        srts = [inputfile + f for f in os.listdir(inputfile) if f.lower().endswith('srt')]

    timestamps = []
    for srt in srts:
        lines = videogrep.clean_srt(srt)
        for timestamp in lines.keys():
            start, end = videogrep.convert_timespan(timestamp)
            for ext in videogrep.usable_extensions:
                videofile = srt.replace('.srt', '.' + ext)
                if os.path.isfile(videofile):
                    timestamps.append({'start': start, 'end': end, 'file': videofile})

    composition = []
    for i, t in enumerate(timestamps):
        if i == 0:
            next
        prevt = timestamps[i-1]
        if t['file'] == prevt['file'] and t['start'] - prevt['end'] >= minsilence/1000.0 and t['start'] - prevt['end'] <= maxsilence/1000.0:
            composition.append({'file': t['file'], 'start': prevt['end'], 'end': t['start'], 'line': 'SILENCE'})

    composition = composition[:maxclips]

    if randomize == True:
        random.shuffle(composition)

    if len(composition) > 0:
        if len(composition) > 30:
            videogrep.create_supercut_in_batches(composition, outputfile, 0)
        else:
            videogrep.create_supercut(composition, outputfile, 0)
    else:
        print "No silence found"

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate a "supercut" of silences based on subtitle tracks.')
    parser.add_argument('--input', '-i', dest='inputfile', required=True, help='video or subtitle file, or folder')
    parser.add_argument('--max-clips', '-m', dest='maxclips', type=int, default=200, help='maximum number of clips to use for the supercut')
    parser.add_argument('--minsilence', '-s', dest='minsilence', type=int, default=1000, help='minimum silence?')
    parser.add_argument('--maxsilence', '-ms', dest='maxsilence', type=int, default=2000, help='maximum silence?')
    parser.add_argument('--output', '-o', dest='outputfile', default='supercut.mp4', help='name of output file')
    parser.add_argument('--test', '-t', action='store_true', help='show results without making the supercut')
    parser.add_argument('--randomize', '-r', action='store_true', help='randomize the clips')
    parser.add_argument('--padding', '-p', dest='padding', default=0, type=int, help='padding in milliseconds to add to the start and end of each clip')

    args = parser.parse_args()

    silence(inputfile=args.inputfile, outputfile=args.outputfile, maxclips=args.maxclips, minsilence=args.minsilence, maxsilence=args.maxsilence, padding=args.padding, test=args.test, randomize=args.randomize)
