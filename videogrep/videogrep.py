import json
import random
import os
import re
import gc
import time
import mimetypes
import sys
from . import vtt, srt, sphinx, fcpxml
from pathlib import Path
from typing import Optional, List, Union, Iterator

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    concatenate_audioclips
)

BATCH_SIZE = 20
SUB_EXTS = [".json", ".vtt", ".srt", ".transcript"]


def find_transcript(videoname: str, prefer: Optional[str] = None) -> Optional[str]:
    """
    Takes a video file path and finds a matching subtitle file.

    :param videoname str: Video file path
    :param prefer Optiona[str]: Transcript file type preference. Can be vtt, srt, or json
    :rtype Optional[str]: Subtitle file path
    """

    subfile = None

    _sub_exts = SUB_EXTS

    if prefer is not None:
        _sub_exts = [prefer] + SUB_EXTS

    all_files = [str(f) for f in Path(videoname).parent.iterdir() if f.is_file()]

    for ext in _sub_exts:
        pattern = (
            re.escape(os.path.splitext(videoname)[0])
            + r"\..*?\.?"
            + ext.replace(".", "")
        )
        for f in all_files:
            if re.search(pattern, f):
                subfile = f
                break
        if subfile:
            break

    return subfile


def parse_transcript(
    videoname: str, prefer: Optional[str] = None
) -> Optional[List[dict]]:
    """
    Helper function to parse a subtitle file and returns timestamps.

    :param videoname str: Video file path
    :param prefer Optiona[str]: Transcript file type preference. Can be vtt, srt, or json
    :rtype Optional[List[dict]]: List of timestamps or None
    """

    subfile = find_transcript(videoname, prefer)

    if subfile is None:
        print("No subtitle file found for ", videoname)
        return None

    transcript = None

    with open(subfile, "r", encoding="utf8") as infile:
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


def remove_overlaps(segments: List[dict]) -> List[dict]:
    """
    Removes any time overlaps from clips

    :param segments List[dict]: Segments to clean up
    :rtype List[dict]: Cleaned output
    """

    if len(segments) == 0:
        return []

    segments = sorted(segments, key=lambda k: k["start"])
    out = [segments[0]]
    for segment in segments[1:]:
        prev_end = out[-1]["end"]
        start = segment["start"]
        end = segment["end"]
        if prev_end >= start:
            out[-1]["end"] = end
        else:
            out.append(segment)

    return out


def pad_and_sync(
    segments: List[dict], padding: float = 0, resync: float = 0
) -> List[dict]:
    """
    Adds padding and resyncs

    :param segments List[dict]: Segments
    :param padding float: Time in seconds to pad each clip
    :param resync float: Time in seconds to shift subtitle timestamps
    :rtype List[dict]: Padded and cleaned output
    """

    if len(segments) == 0:
        return []

    for s in segments:
        if padding != 0:
            s["start"] -= padding
            s["end"] += padding
        if resync != 0:
            s["start"] += resync
            s["end"] += resync

        if s["start"] < 0:
            s["start"] = 0
        if s["end"] < 0:
            s["end"] = 0

    out = [segments[0]]
    for segment in segments[1:]:
        prev_file = out[-1]["file"]
        current_file = segment["file"]
        if current_file != prev_file:
            out.append(segment)
            continue
        prev_end = out[-1]["end"]
        start = segment["start"]
        end = segment["end"]
        if prev_end >= start:
            out[-1]["end"] = end
        else:
            out.append(segment)

    return out


def search(
    files: Union[str, list],
    query: Union[str, list],
    search_type: str = "sentence",
    prefer: Optional[str] = None,
) -> List[dict]:
    """
    Searches for a query in a video file or files and returns a list of timestamps in the format [{file, start, end, content}]

    :param files Union[str, list]: List of files or file
    :param query str: Query as a regular expression, or a list of queries
    :param search_type str: Return timestamps for "sentence" or "fragment"
    :param prefer str: Transcript file type preference. Can be vtt, srt, or json
    :rtype List[dict]: A list of timestamps that match the query
    """
    if not isinstance(files, list):
        files = [files]

    if not isinstance(query, list):
        query = [query]

    all_segments = []

    for file in files:
        segments = []
        transcript = parse_transcript(file, prefer=prefer)
        if transcript is None:
            continue

        if search_type == "sentence":
            for line in transcript:
                for _query in query:
                    if re.search(_query, line["content"]):
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

            for _query in query:
                queries = _query.split(" ")
                queries = [q.strip() for q in queries if q.strip() != ""]
                fragments = zip(*[words[i:] for i in range(len(queries))])
                for fragment in fragments:
                    found = all(
                        re.search(q, w["word"]) for q, w in zip(queries, fragment)
                    )
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

        elif search_type == "mash":
            if "words" not in transcript[0]:
                print("Could not find word-level timestamps for", file)
                continue

            words = []
            for line in transcript:
                words += line["words"]

            for _query in query:
                queries = _query.split(" ")

                for q in queries:
                    matches = [w for w in words if w["word"].lower() == q.lower()]
                    if len(matches) == 0:
                        print("Could not find", q, "in transcript")
                        return []
                    random.shuffle(matches)
                    word = matches[0]
                    segments.append(
                        {
                            "file": file,
                            "start": word["start"],
                            "end": word["end"],
                            "content": word["word"],
                        }
                    )

        segments = sorted(segments, key=lambda k: k["start"])

        all_segments += segments

    return all_segments


def get_file_type(filename: str):
    """
    Get filetype ('audio', 'video', 'text', etc...) for filename based on the
    IANA Media Type, aka MIME type.

    :param filename str: filename or Path of file
    """
    mimetypes.init()
    ftype = mimetypes.guess_type(filename)[0]

    if ftype != None:
        filetype = ftype.split("/")[0]

        return filetype

    return "unknown"


def get_input_type(composition: List[dict]):
    """
    Get input type of files ('audio' or 'video') for inputs based on the
    IANA Media Type, aka MIME type, and using videgrep's composition dict.

    :param composition List[dict]: List of timestamps in the format [{start, end, file}]
    """
    filenames = set([c["file"] for c in composition])
    types = []

    for f in filenames:
        type = get_file_type(f)
        types.append(type)

    if "audio" in types:
        input_type = "audio"
    else:
        input_type = "video"

    return input_type


def plan_no_action(composition: List[dict], outputfile: str):
    """
    Check if user has asked to convert audio to video, which videogrep does not do.

    :param composition List[dict]: List of timestamps in the format [{start, end, file}]
    :param outputfile str: Path to save the video to
    """
    input_type = get_input_type(composition)
    output_type = get_file_type(outputfile)

    if (
            (input_type == "audio") and (output_type == "video") and
            (outputfile != "supercut.mp4")
        ):
        return True
    else:
        return False


def plan_video_output(composition: List[dict], outputfile: str):
    """
    Check if videogrep should create a video output

    :param composition List[dict]: List of timestamps in the format [{start, end, file}]
    :param outputfile str: Path to save the video to
    """
    input_type = get_input_type(composition)
    output_type = get_file_type(outputfile)

    if (input_type == "video") and (output_type != "audio"):
        return True
    else:
        return False


def plan_audio_output(composition: List[dict], outputfile: str):
    """
    Check if videogrep should create an audio output

    :param composition List[dict]: List of timestamps in the format [{start, end, file}]
    :param outputfile str: Path to save the video to
    """
    input_type = get_input_type(composition)
    output_type = get_file_type(outputfile)

    if (input_type == "audio") or (output_type == "audio"):
        return True
    else:
        return False


def create_supercut(composition: List[dict], outputfile: str):
    """
    Concatenate video clips together.

    :param composition List[dict]: List of timestamps in the format [{start, end, file}]
    :param outputfile str: Path to save the video to
    """

    all_filenames = set([c["file"] for c in composition])

    if plan_no_action(composition, outputfile):
        print("Videogrep is not able to convert audio input to video output.")
        print("Try using an audio output instead, like 'supercut.mp3'.")
        sys.exit("Exiting...")
    elif plan_video_output(composition, outputfile):
        print("[+] Creating clips.")
        videofileclips = dict([(f, VideoFileClip(f)) for f in all_filenames])
        cut_clips = []
        for c in composition:
            if c["start"] < 0:
                c["start"] = 0
            if c["end"] > videofileclips[c["file"]].duration:
                c["end"] = videofileclips[c["file"]].duration
            cut_clips.append(videofileclips[c["file"]].subclip(c["start"], c["end"]))

        print("[+] Concatenating clips.")
        final_clip = concatenate_videoclips(cut_clips, method="compose")

        print("[+] Writing ouput file.")
        final_clip.write_videofile(
            outputfile,
            codec="libx264",
            temp_audiofile=f"{outputfile}_temp-audio{time.time()}.m4a",
            remove_temp=True,
            audio_codec="aac",
        )
    elif plan_audio_output(composition, outputfile):
        print("[+] Creating clips.")
        audiofileclips = dict([(f, AudioFileClip(f)) for f in all_filenames])
        cut_clips = []

        for c in composition:
            if c["start"] < 0:
                c["start"] = 0
            if c["end"] > audiofileclips[c["file"]].duration:
                c["end"] = audiofileclips[c["file"]].duration
            cut_clips.append(audiofileclips[c["file"]].subclip(c["start"], c["end"]))

        print("[+] Concatenating clips.")
        final_clip = concatenate_audioclips(cut_clips)

        print("[+] Writing output file.")
        if outputfile == "supercut.mp4":
            outputfile = "supercut.mp3"

        # we don't currently use this, but may be useful for certain libraries
        outputformat = outputfile.split('.')[-1]

        final_clip.write_audiofile(outputfile)


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

    if plan_no_action(composition, outputfile):
        print("Videogrep is not able to convert audio input to video output.")
        print("Try using an audio output instead, like 'supercut.mp3'.")
        sys.exit("Exiting...")
    elif plan_video_output(composition, outputfile):
        file_ext = ".mp4"
    elif plan_audio_output(composition, outputfile):
        file_ext = ".mp3"
        if outputfile == "supercut.mp4":
            outputfile = "supercut.mp3"

    while start_index < total_clips:
        filename = outputfile + ".tmp" + str(start_index) + file_ext
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

    if plan_video_output(composition, outputfile):
        clips = [VideoFileClip(filename) for filename in batch_comp]
        video = concatenate_videoclips(clips, method="compose")
        video.write_videofile(
            outputfile,
            codec="libx264",
            temp_audiofile=f"{outputfile}_temp-audio{time.time()}.m4a",
            remove_temp=True,
            audio_codec="aac",
        )
    elif plan_audio_output(composition, outputfile):
        clips = [AudioFileClip(filename) for filename in batch_comp]
        audio = concatenate_audioclips(clips)
        audio.write_audiofile(outputfile)

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

    if plan_no_action(composition, outputfile):
        print("Videogrep is not able to convert audio input to video output.")
        print("Try using an audio output instead, like 'supercut.mp3'.")
        sys.exit("Exiting...")
    elif plan_video_output(composition, outputfile):
        videofileclips = dict([(f, VideoFileClip(f)) for f in all_filenames])
        cut_clips = []
        for c in composition:
            if c["start"] < 0:
                c["start"] = 0
            if c["end"] > videofileclips[c["file"]].duration:
                c["end"] = videofileclips[c["file"]].duration
            cut_clips.append(videofileclips[c["file"]].subclip(c["start"], c["end"]))

        basename, ext = os.path.splitext(outputfile)
        print("[+] Writing output files.")
        for i, clip in enumerate(cut_clips):
            clipfilename = basename + "_" + str(i).zfill(5) + ext
            clip.write_videofile(
                clipfilename,
                codec="libx264",
                temp_audiofile="{clipfilename}_temp-audio.m4a",
                remove_temp=True,
                audio_codec="aac",
            )
    elif plan_audio_output(composition, outputfile):
        audiofileclips = dict([(f, AudioFileClip(f)) for f in all_filenames])
        cut_clips = []

        for c in composition:
            if c["start"] < 0:
                c["start"] = 0
            if c["end"] > audiofileclips[c["file"]].duration:
                c["end"] = audiofileclips[c["file"]].duration
            cut_clips.append(audiofileclips[c["file"]].subclip(c["start"], c["end"]))

        if outputfile == "supercut.mp4":
            outputfile = "supercut.mp3"

        basename, ext = os.path.splitext(outputfile)
        print("[+] Writing output files.")
        for i, clip in enumerate(cut_clips):
            clipfilename = basename + "_" + str(i).zfill(5) + ext
            clip.write_audiofile(clipfilename)


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
    query: Union[List[str], str],
    search_type: str = "sentence",
    output: str = "supercut.mp4",
    resync: float = 0,
    padding: float = 0,
    maxclips: int = 0,
    export_clips: bool = False,
    random_order: bool = False,
    demo: bool = False,
    write_vtt: bool = False,
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
    :param write_vtt bool: Write a WebVTT file next to the supercut (default False)
    """

    segments = search(files, query, search_type)

    if len(segments) == 0:
        if isinstance(query, list):
            query = " ".join(query)
        print("No results found for", query)
        return False

    # padding
    segments = pad_and_sync(segments, padding=padding, resync=resync)

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

    # write WebVTT file
    if write_vtt:
        basename, ext = os.path.splitext(output)
        vtt.render(segments, basename + ".vtt")
