import json
import random
import os
import re
from . import vtt, srt, sphinx, transcribe
from moviepy.editor import VideoFileClip, concatenate

__version__ = "2.0.0"
BATCH_SIZE = 20
SUB_EXTS = [".json", ".srt", ".vtt", ".en.vtt", ".transcript"]


def find_transcript(videoname):
    for ext in SUB_EXTS:
        sub_path = os.path.splitext(videoname)[0] + ext
        if os.path.exists(sub_path):
            return sub_path

    print("No subtitle file found for ", videoname)
    return None


def parse_transcript(videoname):
    subfile = find_transcript(videoname)
    if subfile is None:
        return None

    with open(subfile, "r") as infile:
        if subfile.endswith(".srt"):
            transcript = srt.parse(infile)
        elif subfile.endswith(".vtt"):
            transcript = vtt.parse(infile)
        elif subfile.endswith(".json"):
            transcript = json.load(infile)
        elif subfile.endswith(".transcript"):
            transcript = sphinx.parse(infile)

    return transcript


def get_ngrams(files, n=1):
    """
    Get ngrams from a text
    Sourced from:
    https://gist.github.com/dannguyen/93c2c43f4e65328b85af
    """

    if not isinstance(files, list):
        files = [files]

    words = []

    for file in files:
        transcript = parse_transcript(file)
        if transcript is None:
            continue
        for line in transcript:
            if "words" in line:
                words += [w["word"] for w in line["words"]]
            else:
                words += re.split(r"[.?!,:\"]+\s*|\s+", line["content"])

    ngrams = zip(*[words[i:] for i in range(n)])
    return ngrams


def search(files, query, search_type="sentence"):
    if not isinstance(files, list):
        files = [files]

    segments = []

    for file in files:
        transcript = parse_transcript(file)
        if transcript is None:
            continue

        if search_type == "sentence":
            for line in transcript:
                if re.search(query, line["content"]):
                    segments.append(
                        {
                            "file": file,
                            "start": line["start"],
                            "end": line["end"],
                            "content": line["content"],
                        }
                    )

        elif search_type == "fragment":
            words = []
            for line in transcript:
                words += line["words"]

            queries = query.split(" ")
            queries = [q.strip() for q in queries if q.strip() != ""]
            fragments = zip(*[words[i:] for i in range(len(queries))])
            for fragment in fragments:
                found = all(re.search(q, w["word"]) for q, w in zip(queries, fragment))
                if found:
                    phrase = " ".join([w["word"] for w in fragment])
                    segments.append(
                        {
                            "file": file,
                            "start": fragment[0]["start"],
                            "end": fragment[-1]["end"],
                            "content": phrase,
                        }
                    )
    return segments


def create_supercut(composition, outputfile):
    """Concatenate video clips together and output finished video file to the
    output directory.
    """
    print("[+] Creating clips.")

    all_filenames = set([c["file"] for c in composition])
    videofileclips = dict([(f, VideoFileClip(f)) for f in all_filenames])
    cut_clips = [
        videofileclips[c["file"]].subclip(c["start"], c["end"]) for c in composition
    ]

    print("[+] Concatenating clips.")
    final_clip = concatenate(cut_clips)

    print("[+] Writing ouput file.")
    final_clip.to_videofile(
        outputfile,
        codec="libx264",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        audio_codec="aac",
    )


def create_supercut_in_batches(composition, outputfile):
    """Create & concatenate video clips in groups of size BATCH_SIZE and output
    finished video file to output directory.
    """
    total_clips = len(composition)
    start_index = 0
    end_index = BATCH_SIZE
    batch_comp = []
    while start_index < total_clips:
        filename = outputfile + ".tmp" + str(start_index) + ".mp4"
        try:
            create_supercut(composition[start_index:end_index], filename)
            batch_comp.append(filename)
            gc.collect()
            start_index += BATCH_SIZE
            end_index += BATCH_SIZE
        except:
            start_index += BATCH_SIZE
            end_index += BATCH_SIZE
            next

    clips = [VideoFileClip(filename) for filename in batch_comp]
    video = concatenate(clips)
    video.to_videofile(
        outputfile,
        codec="libx264",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        audio_codec="aac",
    )

    # remove partial video files
    for filename in batch_comp:
        os.remove(filename)

    cleanup_log_files(outputfile)


def export_individual_clips(composition, outputfile):
    all_filenames = set([c["file"] for c in composition])
    videofileclips = dict([(f, VideoFileClip(f)) for f in all_filenames])
    cut_clips = [
        videofileclips[c["file"]].subclip(c["start"], c["end"]) for c in composition
    ]

    basename, ext = os.path.splitext(outputfile)
    print("[+] Writing ouput files.")
    for i, clip in enumerate(cut_clips):
        clipfilename = basename + "_" + str(i).zfill(5) + ext
        clip.to_videofile(
            clipfilename,
            codec="libx264",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            audio_codec="aac",
        )


def cleanup_log_files(outputfile):
    """Search for and remove temp log files found in the output directory."""
    d = os.path.dirname(os.path.abspath(outputfile))
    logfiles = [f for f in os.listdir(d) if f.endswith("ogg.log")]
    for f in logfiles:
        os.remove(f)


def videogrep(
    files,
    query,
    search_type="sentence",
    output="supercut.mp4",
    resync=0,
    padding=0,
    maxclips=0,
    export_clips=False,
    random_order=False,
    demo=False,
):

    segments = search(files, query, search_type)

    if len(segments) == 0:
        print("No results found for", query)
        return False

    # padding
    for s in segments:
        if padding != 0:
            s["start"] -= padding
            s["end"] += padding
        if resync != 0:
            s["start"] += resync
            s["end"] += resync

    # random order
    if random_order:
        random.shuffle(segments)

    # max clips
    if maxclips != 0:
        segments = segments[0:maxclips]

    # demo and exit
    if demo:
        for s in segments:
            print(s["file"], s["start"], s["end"], s["content"])
        return True

    # export individual clips
    if export_clips:
        export_individual_clips(segments, output)
        return True

    # export supercut
    if len(segments) > BATCH_SIZE:
        create_supercut_in_batches(segments, output)
    else:
        create_supercut(segments, output)


def main():
    import argparse

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
    parser.add_argument("--search", "-s", dest="search", help="search term")
    parser.add_argument(
        "--search-type",
        "-st",
        dest="searchtype",
        default="sentence",
        choices=["sentence", "fragment"],
        help="type of search - can either be 'sentence' or 'fragment'",
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
        "--ngrams",
        "-n",
        dest="ngrams",
        type=int,
        default=0,
        help="return ngrams for videos",
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
        for f in args.inputfile:
            transcribe.transcribe(f)
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
