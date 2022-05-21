import json
import random
import os
import re
import gc
from . import vtt, srt, sphinx, fcpxml
from typing import Optional, List, Union, Iterator

from moviepy.editor import VideoFileClip, concatenate_videoclips

BATCH_SIZE = 20
SUB_EXTS = [".json", ".srt", ".vtt", ".en.vtt", ".transcript"]


def find_transcript(videoname: str, prefer: str = "json") -> Optional[str]:
    """
    Takes a video file path and finds a matching subtitle file.
    (i'm phasing this out, just leaving as a reference for now)

    :param videoname str: Video file path
    :rtype Optional[str]: Subtitle file path
    """

    for ext in SUB_EXTS:
        sub_path = os.path.splitext(videoname)[0] + ext
        if os.path.exists(sub_path):
            return sub_path

    print("No subtitle file found for ", videoname)
    return None


def parse_transcript(
    videoname: str, prefer: Optional[str] = None
) -> Optional[List[dict]]:
    """
    Helper function to parse a subtitle file and returns timestamps.

    :param videoname str: Video file path
    :param prefer Optiona[str]: Transcript file type preference. Can be vtt, srt, or json
    :rtype Optional[List[dict]]: List of timestamps or None
    """

    subfile = None

    _sub_exts = SUB_EXTS

    if prefer is not None:
        _sub_exts = [prefer] + SUB_EXTS

    for ext in _sub_exts:
        subpath = os.path.splitext(videoname)[0] + ext
        if os.path.exists(subpath):
            subfile = subpath
            break

    if subfile is None:
        print("No subtitle file found for ", videoname)
        return None

    transcript = None

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


def get_ngrams(files: Union[str, list], n: int = 1) -> Iterator[tuple]:
    """
    Get n-grams from video file(s)
    Sourced from: https://gist.github.com/dannguyen/93c2c43f4e65328b85af

    :param files Union[str, list]: Path or paths to video files
    :param n int: N-gram size
    :rtype Iterator[tuple]: List of (n-gram, occurrences)
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


def search(
    files: Union[str, list],
    query: str,
    search_type: str = "sentence",
    prefer: Optional[str] = None,
) -> List[dict]:
    """
    Searches for a query in a video file or files and returns a list of timestamps in the format [{file, start, end, content}]

    :param files Union[str, list]: List of files or file
    :param query str: Query as a regular expression
    :param search_type str: Return timestamps for "sentence" or "fragment"
    :param prefer str: Transcript file type preference. Can be vtt, srt, or json
    :rtype List[dict]: A list of timestamps that match the query
    """
    if not isinstance(files, list):
        files = [files]

    segments = []

    for file in files:
        transcript = parse_transcript(file, prefer=prefer)
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
            if "words" not in transcript[0]:
                print("Could not find word-level timestamps for", file)
                continue

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


def create_supercut(composition: List[dict], outputfile: str):
    """
    Concatenate video clips together.

    :param composition List[dict]: List of timestamps in the format [{start, end, file}]
    :param outputfile str: Path to save the video to
    """
    print("[+] Creating clips.")

    all_filenames = set([c["file"] for c in composition])
    videofileclips = dict([(f, VideoFileClip(f)) for f in all_filenames])
    cut_clips = [
        videofileclips[c["file"]].subclip(c["start"], c["end"]) for c in composition
    ]

    print("[+] Concatenating clips.")
    final_clip = concatenate_videoclips(cut_clips, method="compose")

    print("[+] Writing ouput file.")
    final_clip.write_videofile(
        outputfile,
        codec="libx264",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        audio_codec="aac",
    )


def create_supercut_in_batches(composition: List[dict], outputfile: str):
    """
    Concatenate video clips together in groups of size BATCH_SIZE.

    :param composition List[dict]: List of timestamps in the format [{start, end, file}]
    :param outputfile str: Path to save the video to
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
        except Exception as e:
            start_index += BATCH_SIZE
            end_index += BATCH_SIZE
            next

    clips = [VideoFileClip(filename) for filename in batch_comp]
    video = concatenate_videoclips(clips, method="compose")
    video.write_videofile(
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


def export_individual_clips(composition: List[dict], outputfile: str):
    """
    Exports videogrep composition to individual clips.

    :param composition List[dict]: List of timestamps in the format [{start, end, file}]
    :param outputfile str: Path to save the videos to
    """

    all_filenames = set([c["file"] for c in composition])
    videofileclips = dict([(f, VideoFileClip(f)) for f in all_filenames])
    cut_clips = [
        videofileclips[c["file"]].subclip(c["start"], c["end"]) for c in composition
    ]

    basename, ext = os.path.splitext(outputfile)
    print("[+] Writing ouput files.")
    for i, clip in enumerate(cut_clips):
        clipfilename = basename + "_" + str(i).zfill(5) + ext
        clip.write_videofile(
            clipfilename,
            codec="libx264",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            audio_codec="aac",
        )


def export_m3u(composition: List[dict], outputfile: str):
    """
    Exports supercut as an m3u file that can be played in VLC

    :param composition List[dict]: List of timestamps in the format [{start, end, file}]
    :param outputfile str: Path to save the playlist to
    """

    lines = []
    lines.append("#EXTM3U")
    for c in composition:
        lines.append(f"#EXTINF:")
        lines.append(f"#EXTVLCOPT:start-time={c['start']}")
        lines.append(f"#EXTVLCOPT:stop-time={c['end']}")
        lines.append(c["file"])

    with open(outputfile, "w") as outfile:
        outfile.write("\n".join(lines))


def export_mpv_edl(composition: List[dict], outputfile: str):
    """
    Exports supercut as an edl file that can be played in mpv. Good for previewing!

    :param composition List[dict]: List of timestamps in the format [{start, end, file}]
    :param outputfile str: Path to save the playlist to
    """
    lines = []
    lines.append("# mpv EDL v0")
    for c in composition:
        lines.append(f"{os.path.abspath(c['file'])},{c['start']},{c['end']-c['start']}")

    with open(outputfile, "w") as outfile:
        outfile.write("\n".join(lines))


def export_xml(composition: List[dict], outputfile: str):
    """
    Exports supercut as a Final Cut Pro xml file. This can be imported to Premiere or Resolve.

    :param composition List[dict]: List of timestamps in the format [{start, end, file}]
    :param outputfile str: Path to save the xml file to
    """
    fcpxml.compose(composition, outputfile)


def cleanup_log_files(outputfile: str):
    """Search for and remove temp log files found in the output directory."""
    d = os.path.dirname(os.path.abspath(outputfile))
    logfiles = [f for f in os.listdir(d) if f.endswith("ogg.log")]
    for f in logfiles:
        os.remove(f)


def videogrep(
    files: Union[List[str], str],
    query: str,
    search_type: str = "sentence",
    output: str = "supercut.mp4",
    resync: float = 0,
    padding: float = 0,
    maxclips: int = 0,
    export_clips: bool = False,
    random_order: bool = False,
    demo: bool = False,
):
    """
    Creates a supercut of videos based on a search query

    :param files List[str]: Video file to search through
    :param query str: A query, as a regular expression
    :param search_type str: Either 'sentence' or 'fragment'
    :param output str: Filename to save to
    :param resync float: Time in seconds to shift subtitle timestamps
    :param padding float: Time in seconds to pad each clip
    :param maxclips int: Maximum clips to use (0 is unlimited)
    :param export_clips bool: Export individual clips rather than a single file (default False)
    :param random_order bool: Randomize the order of clips (default False)
    :param demo bool: Show the results of the search but don't actually make a supercut
    """

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

    # m3u
    if output.endswith(".m3u"):
        export_m3u(segments, output)
        return True

    # mpv edls
    if output.endswith(".mpv.edl"):
        export_mpv_edl(segments, output)
        return True

    # fcp xml (compatible with premiere/davinci)
    if output.endswith(".xml"):
        export_xml(segments, output)
        return True

    # export supercut
    if len(segments) > BATCH_SIZE:
        create_supercut_in_batches(segments, output)
    else:
        create_supercut(segments, output)
