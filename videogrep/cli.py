import argparse
from . import get_ngrams, sphinx, videogrep, __version__


def main():
    """
    Run the command line version of Videogrep
    """

    parser = argparse.ArgumentParser(
        description='Generate a "supercut" of one or more video files by searching through subtitle tracks.'
    )
    parser.add_argument(
        "--input",
        "-i",
        dest="inputfile",
        nargs="*",
        required=True,
        help="video file or files",
    )
    parser.add_argument(
        "--search", "-s", dest="search", action="append", help="search term"
    )
    parser.add_argument(
        "--search-type",
        "-st",
        dest="searchtype",
        default="sentence",
        choices=["sentence", "fragment", "mash"],
        help="type of search - can either be 'sentence', 'fragment' or 'mash'",
    )
    parser.add_argument(
        "--max-clips",
        "-m",
        dest="maxclips",
        type=int,
        default=0,
        help="maximum number of clips to use for the supercut",
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="outputfile",
        default="supercut.mp4",
        help="name of output file",
    )
    parser.add_argument(
        "--export-clips",
        "-ec",
        dest="export_clips",
        action="store_true",
        help="Export individual clips",
    )
    parser.add_argument(
        "--demo",
        "-d",
        action="store_true",
        help="show results without making the supercut",
    )
    parser.add_argument(
        "--randomize", "-r", action="store_true", help="randomize the clips"
    )
    parser.add_argument(
        "--padding",
        "-p",
        dest="padding",
        default=0,
        type=float,
        help="padding in seconds to add to the start and end of each clip",
    )
    parser.add_argument(
        "--resyncsubs",
        "-rs",
        dest="sync",
        default=0,
        type=float,
        help="subtitle re-synch delay +/- in seconds",
    )
    parser.add_argument(
        "--sphinx-transcribe",
        "-str",
        dest="sphinxtranscribe",
        action="store_true",
        help="transcribe the video using pocketsphinx (must be installed)",
    )
    parser.add_argument(
        "--transcribe",
        "-tr",
        dest="transcribe",
        action="store_true",
        help="transcribe the video using vosk (built in)",
    )
    parser.add_argument(
        "--model",
        "-mo",
        dest="model",
        help="model folder for transcription",
    )
    parser.add_argument(
        "--ngrams",
        "-n",
        dest="ngrams",
        type=int,
        default=0,
        help="return ngrams for videos",
    )
    parser.add_argument(
        "--version",
        "-v",
        help="show version",
        action="version",
        version=__version__,
    )
    args = parser.parse_args()

    if args.ngrams > 0:
        from collections import Counter

        grams = get_ngrams(args.inputfile, args.ngrams)
        most_common = Counter(grams).most_common(100)
        for ngram, count in most_common:
            print(" ".join(ngram), count)

        return True

    if args.sphinxtranscribe:
        for f in args.inputfile:
            sphinx.transcribe(f)
        return True

    if args.transcribe:
        try:
            from . import transcribe
        except ModuleNotFoundError:
            print("You must install vosk to transcribe files: \n\npip install vosk\n")
            return False

        for f in args.inputfile:
            transcribe.transcribe(f, args.model)

        return True

    if args.search is None:
        parser.error("argument --search/-s is required")

    videogrep(
        files=args.inputfile,
        query=args.search,
        search_type=args.searchtype,
        output=args.outputfile,
        maxclips=args.maxclips,
        padding=args.padding,
        demo=args.demo,
        random_order=args.randomize,
        resync=args.sync,
        export_clips=args.export_clips,
    )
