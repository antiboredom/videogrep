import argparse

from videogrep import videogrep

if __name__ == '__main__':
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

    args = parser.parse_args()

    videogrep.videogrep(args.inputfile, args.outputfile, args.search, args.searchtype, args.maxclips, args.padding, args.test, args.randomize, args.sync)

