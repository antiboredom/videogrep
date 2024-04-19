import videogrep
import re
from collections import Counter
from pathlib import Path
from moviepy.editor import VideoFileClip
from pytest import approx
import glob
import subprocess


def get_duration(input_video):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            input_video,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return float(result.stdout)


def File(path):
    return str(Path(__file__).parent / Path(path))


def test_version():
    assert videogrep.__version__ == "2.3.0"


def test_srts():
    with open(File("test_inputs/manifesto.srt")) as infile:
        srt = infile.read()
    parsed = videogrep.srt.parse(srt)

    assert parsed[0]["content"] == "this audiobook is in the public domain"
    assert parsed[0]["start"] == approx(1.599)
    assert parsed[0]["end"] == approx(3.919)

    with open(File("test_inputs/manifesto.srt")) as infile:
        parsed = videogrep.srt.parse(infile)

    assert parsed[6]["content"] == "preamble a spectre is haunting europe"
    assert parsed[6]["start"] == approx(19.039)
    assert parsed[6]["end"] == approx(22.96)


def test_cued_vtts():
    testfile = File("test_inputs/manifesto.vtt")
    with open(testfile) as infile:
        parsed = videogrep.vtt.parse(infile)

    assert parsed[0]["content"] == "this audiobook is in the public domain"
    assert parsed[0]["start"] == approx(1.599)
    assert parsed[0]["end"] == approx(3.909)

    word = parsed[0]["words"][0]
    assert word["word"] == "this"
    assert word["start"] == approx(1.599)
    assert word["end"] == approx(1.92)

    word = parsed[-1]["words"][-1]
    assert word["word"] == "danish"
    assert word["start"] == approx(84.479)
    assert word["end"] == approx(84.87)


def test_find_sub():
    testvid = File("test_inputs/manifesto.mp4")
    testsubfile = File("test_inputs/manifesto.json")
    assert videogrep.find_transcript(testvid) == testsubfile

    testaud = File("test_inputs/manifesto_audio.mp3")
    testsubfile = File("test_inputs/manifesto_audio.json")
    assert videogrep.find_transcript(testaud) == testsubfile

    testvid = File("test_inputs/emptyvideo.mp4")
    testsubfile = File("test_inputs/emptyvideo.aa.vtt")
    assert videogrep.find_transcript(testvid) == testsubfile

    testaud = File("test_inputs/emptyaudio.mp3")
    testsubfile = File("test_inputs/emptyaudio.aa.vtt")
    assert videogrep.find_transcript(testaud) == testsubfile

    testvid = File("test_inputs/emptyvideo 2.mp4")
    testsubfile = File("test_inputs/emptyvideo 2.mp4.aa.vtt")
    assert videogrep.find_transcript(testvid) == testsubfile

    testaud = File("test_inputs/emptyaudio 2.mp3")
    testsubfile = File("test_inputs/emptyaudio 2.mp3.aa.vtt")
    assert videogrep.find_transcript(testaud) == testsubfile

    testvid = File("test_inputs/fakevideo.mp4")
    assert videogrep.find_transcript(testvid) == None

    testaud = File("test_inputs/fakeaudio.mp3")
    assert videogrep.find_transcript(testaud) == None

    testvid = File("test_inputs/Some Random Video [Pj-h6MEgE7I].mp4")
    testsubfile = File("test_inputs/Some Random Video [Pj-h6MEgE7I].de.vtt")
    assert videogrep.find_transcript(testvid) == testsubfile

    testaud = File("test_inputs/Some Random Audio [Wt-f9FErE64].mp3")
    testsubfile = File("test_inputs/Some Random Audio [Wt-f9FErE64].de.vtt")
    assert videogrep.find_transcript(testaud) == testsubfile


def test_parse_transcript():
    testvid = File("test_inputs/manifesto.mp4")
    transcript = videogrep.parse_transcript(testvid)
    assert transcript[0]["content"] == "this audiobook is in the public domain"


def test_export_xml():
    pass


def test_export_edl():
    pass


def test_export_m3u():
    pass


def test_remove_overlaps():
    segments = [{"start": 0, "end": 1}, {"start": 0.5, "end": 2}]
    cleaned = videogrep.remove_overlaps(segments)
    assert len(cleaned) == 1
    assert cleaned[-1]["end"] == 2

    segments = [{"start": 0, "end": 1}, {"start": 2, "end": 3}]
    cleaned = videogrep.remove_overlaps(segments)
    assert len(cleaned) == 2
    assert cleaned[-1]["end"] == 3


def test_pad_and_sync():
    # should remove overlap and make a single segment
    segments = [
        {"start": 0, "end": 1, "file": "1"},
        {"start": 0.5, "end": 2, "file": "1"},
    ]
    cleaned = videogrep.pad_and_sync(segments)
    assert len(cleaned) == 1
    assert cleaned[-1]["end"] == approx(2)

    # should not do anything
    segments = [
        {"start": 0, "end": 1, "file": "1"},
        {"start": 2, "end": 3, "file": "1"},
    ]
    cleaned = videogrep.pad_and_sync(segments)
    assert len(cleaned) == 2
    assert cleaned[-1]["end"] == approx(3)

    # should add padding, but not remove segments
    segments = [
        {"start": 0, "end": 1, "file": "1"},
        {"start": 2, "end": 3, "file": "1"},
    ]
    cleaned = videogrep.pad_and_sync(segments, padding=0.1)
    assert len(cleaned) == 2
    assert cleaned[0]["start"] == approx(0)
    assert cleaned[0]["end"] == approx(1.1)
    assert cleaned[-1]["start"] == approx(1.9)
    assert cleaned[-1]["end"] == approx(3.1)

    # should add padding and create a single segment
    segments = [
        {"start": 0, "end": 1, "file": "1"},
        {"start": 2, "end": 3, "file": "1"},
    ]
    cleaned = videogrep.pad_and_sync(segments, padding=1.1)
    assert len(cleaned) == 1
    assert cleaned[0]["start"] == approx(0)
    assert cleaned[0]["end"] == approx(4.1)

    # should move all timing +1.1
    segments = [
        {"start": 0, "end": 1, "file": "1"},
        {"start": 2, "end": 3, "file": "1"},
    ]
    cleaned = videogrep.pad_and_sync(segments, resync=1.1)
    assert len(cleaned) == 2
    assert cleaned[0]["start"] == approx(1.1)
    assert cleaned[0]["end"] == approx(2.1)
    assert cleaned[1]["start"] == approx(3.1)
    assert cleaned[1]["end"] == approx(4.1)

    # should move all timing -1.1, but not go below 0
    segments = [
        {"start": 0, "end": 1, "file": "1"},
        {"start": 2, "end": 3, "file": "1"},
    ]
    cleaned = videogrep.pad_and_sync(segments, resync=-1.1)
    assert len(cleaned) == 2
    assert cleaned[0]["start"] == approx(0)
    assert cleaned[0]["end"] == approx(0)
    assert cleaned[1]["start"] == approx(0.9)
    assert cleaned[1]["end"] == approx(1.9)

    # should move all timing +0.1, and add padding
    segments = [
        {"start": 0, "end": 1, "file": "1"},
        {"start": 2, "end": 3, "file": "1"},
    ]
    cleaned = videogrep.pad_and_sync(segments, resync=0.1, padding=0.2)
    assert len(cleaned) == 2
    assert cleaned[0]["start"] == approx(0)
    assert cleaned[0]["end"] == approx(1.3)
    assert cleaned[1]["start"] == approx(1.9)
    assert cleaned[1]["end"] == approx(3.3)


def test_ngrams():
    testvid = File("test_inputs/manifesto.mp4")

    grams = list(videogrep.get_ngrams(testvid, 1))
    assert len(grams) == 210

    most_common = Counter(grams).most_common(10)
    assert most_common[0] == (("the",), 20)

    grams = list(videogrep.get_ngrams(testvid, 2))
    assert len(grams) == 209

    most_common = Counter(grams).most_common(10)
    print(most_common[0])
    assert most_common[0] == (("of", "the"), 5)


def test_export_files():
    out1 = File("test_outputs/supercut_clip.mp4")
    videogrep.videogrep(
        File("test_inputs/manifesto.mp4"),
        "communist",
        search_type="fragment",
        export_clips=True,
        output=out1,
    )
    files = glob.glob(File("test_outputs/supercut_clip*.mp4"))
    assert len(files) == 4
    assert get_duration(File("test_outputs/supercut_clip_00000.mp4")) == approx(0.36)

    out2 = File("test_outputs/supercut_clip_audio.mp3")
    videogrep.videogrep(
        File("test_inputs/manifesto_audio.mp3"),
        "communist",
        search_type="fragment",
        export_clips=True,
        output=out2,
    )
    files = glob.glob(File("test_outputs/supercut_clip_audio*.mp3"))
    assert len(files) == 4
    assert get_duration(File("test_outputs/supercut_clip_audio_00002.mp3")) == approx(
        0.574694
    )


def test_videogrep():
    out1 = File("test_outputs/supercut1.mp4")
    videogrep.videogrep(
        File("test_inputs/manifesto.mp4"),
        "communist|communism",
        search_type="fragment",
        output=out1,
    )
    assert get_duration(out1) == approx(4.64)

    # if os.path.exists(out1):
    #     os.remove(out1)

    out2 = File("test_outputs/supercut2.mp4")
    videogrep.videogrep(
        File("test_inputs/manifesto.mp4"),
        "communist|communism",
        search_type="fragment",
        output=out2,
        padding=0.1,
    )
    assert get_duration(out2) == approx(6.24)

    # if os.path.exists(out2):
    #     os.remove(out2)

    out3 = File("test_outputs/supercut1.mp3")
    videogrep.videogrep(
        File("test_inputs/manifesto_audio.mp3"),
        "communist|communism",
        search_type="fragment",
        output=out3,
    )
    assert get_duration(out3) == approx(4.649796)

    out4 = File("test_outputs/supercut2.mp3")
    videogrep.videogrep(
        File("test_inputs/manifesto_audio.mp3"),
        "communist|communism",
        search_type="fragment",
        output=out4,
        padding=0.1,
    )
    assert get_duration(out4) == approx(6.269388)


def test_videogrep_vtt_out():
    out1 = File("test_outputs/supercut1.mp4")
    out1_vtt = Path(out1).with_suffix(".vtt")
    videogrep.videogrep(
        File("test_inputs/manifesto.mp4"),
        "communist|communism",
        search_type="fragment",
        output=out1,
    )
    # By default do not write WebVTT file
    assert not out1_vtt.exists()

    # if os.path.exists(out1):
    #     os.remove(out1)

    out2 = File("test_outputs/supercut2.mp4")
    out2_vtt = Path(out2).with_suffix(".vtt")
    videogrep.videogrep(
        File("test_inputs/manifesto.mp4"),
        "communist|communism",
        search_type="fragment",
        output=out2,
        padding=0.1,
        write_vtt=True,
    )
    assert out2_vtt.exists()
    with out2_vtt.open(encoding="utf-8") as vtt_file:
        lines = vtt_file.readlines()
        # each segment produces four lines, plus two for the header
        # and last line
        assert len(lines) == 8 * 4 + 1
        assert lines[0].strip() == "WEBVTT"
        # first cue timespan is on line 4
        # and starts at 0.0
        first_cue = lines[3].strip().split()
        first_cue_start_sec = videogrep.vtt.timestamp_to_secs(first_cue[0])
        assert first_cue_start_sec == approx(0.0)
        assert first_cue[1] == "-->"
        # last segment end time should be the same as the video duration
        print(lines)
        last_seg_end_ts = lines[-2].strip().split()[2]
        last_seg_end_sec = videogrep.vtt.timestamp_to_secs(last_seg_end_ts)
        assert last_seg_end_sec == approx(6.22)
        assert lines[-1].strip() == "communists"


def test_no_transcript():
    testvid = File("test_inputs/whatever.mp4")
    segments = videogrep.search(testvid, "*", search_type="fragment")
    assert len(segments) == 0

    testaud = File("test_inputs/whatever.mp3")
    segments_audio = videogrep.search(testaud, "*", search_type="fragment")
    assert len(segments_audio) == 0


def test_sentence_search_json():
    testvid = File("test_inputs/manifesto.mp4")

    query = "communist"
    segments = videogrep.search(testvid, query, prefer=".json")
    for s in segments:
        assert query in s["content"]
    assert len(segments) == 4

    assert segments[0]["start"] == approx(13.86)
    assert segments[0]["end"] == approx(15.81)

    query = "communist|communism"
    segments = videogrep.search(testvid, query, prefer=".json")
    for s in segments:
        assert re.search(query, s["content"])
    assert len(segments) == 8
    assert segments[-1]["start"] == approx(73.65)
    assert segments[-1]["end"] == approx(76.35)


def test_word_search_srt():
    testvid = File("test_inputs/manifesto.mp4")

    query = "communist"
    segments = videogrep.search(testvid, query, search_type="fragment", prefer=".srt")
    assert len(segments) == 0


def test_sentence_search_srt():
    testvid = File("test_inputs/manifesto.mp4")

    query = "communist"
    segments = videogrep.search(testvid, query, prefer=".srt")
    for s in segments:
        assert query in s["content"]
    assert len(segments) == 4
    assert segments[0]["start"] == approx(13.2)
    assert segments[0]["end"] == approx(15.28)

    query = "communist|communism"
    segments = videogrep.search(testvid, query, prefer=".srt")
    for s in segments:
        assert re.search(query, s["content"])
    assert len(segments) == 8
    assert segments[-1]["start"] == approx(73.52)
    assert segments[-1]["end"] == approx(75.52)


def test_word_search_json():
    testvid = File("test_inputs/manifesto.mp4")
    segments = videogrep.search(testvid, "communist", search_type="fragment")
    assert len(segments) == 4

    segments = videogrep.search(testvid, "communist party", search_type="fragment")
    assert len(segments) == 1
    assert segments[0]["start"] == approx(14.04)
    assert segments[0]["end"] == approx(14.79)

    segments = videogrep.search(testvid, "alskdfj asldjf", search_type="fragment")
    assert len(segments) == 0

    segments = videogrep.search(testvid, "alskdfj communist", search_type="fragment")
    assert len(segments) == 0

    segments = videogrep.search(testvid, "spectre .*", search_type="fragment")
    assert len(segments) == 2

    segments = videogrep.search(testvid, "ing$", search_type="fragment")
    assert len(segments) == 3

    segments = videogrep.search(
        testvid, ["a spectre", "communist party"], search_type="fragment"
    )
    assert len(segments) == 2


def test_word_search_vtt():
    testvid = File("test_inputs/manifesto.mp4")
    segments = videogrep.search(
        testvid, "communist", search_type="fragment", prefer=".vtt"
    )
    assert len(segments) == 4

    segments = videogrep.search(
        testvid, "communist party", search_type="fragment", prefer=".vtt"
    )
    assert len(segments) == 1
    assert segments[0]["start"] == approx(14.0)
    assert segments[0]["end"] == approx(14.799)

    segments = videogrep.search(
        testvid, "alskdfj asldjf", search_type="fragment", prefer=".vtt"
    )
    assert len(segments) == 0

    segments = videogrep.search(
        testvid, "alskdfj communist", search_type="fragment", prefer=".vtt"
    )
    assert len(segments) == 0

    segments = videogrep.search(
        testvid, "spectre .*", search_type="fragment", prefer=".vtt"
    )
    assert len(segments) == 2

    segments = videogrep.search(testvid, "ing$", search_type="fragment", prefer=".vtt")
    assert len(segments) == 3


def test_sentence_search_vtt():
    testvid = File("test_inputs/manifesto.mp4")
    segments = videogrep.search(testvid, "communist", prefer=".vtt")
    assert len(segments) == 4

    segments = videogrep.search(testvid, "communist party", prefer=".vtt")
    assert len(segments) == 1
    assert segments[0]["start"] == approx(13.2)
    assert segments[0]["end"] == approx(15.27)

    segments = videogrep.search(testvid, "alskdfj asldjf", prefer=".vtt")
    assert len(segments) == 0

    segments = videogrep.search(testvid, "alskdfj communist", prefer=".vtt")
    assert len(segments) == 0

    segments = videogrep.search(testvid, "ing$", prefer=".vtt")
    assert len(segments) == 0


def test_file_type():
    videofile_1 = File("test_inputs/somevid.mp4")
    assert videogrep.get_file_type(videofile_1) == "video"

    videofile_2 = File("test_inputs/othervid.ogv")
    assert videogrep.get_file_type(videofile_2) == "video"

    audiofile_1 = File("test_inputs/someaudio.wav")
    assert videogrep.get_file_type(audiofile_1) == "audio"

    audiofile_2 = File("test_inputs/otheraudio.flac")
    assert videogrep.get_file_type(audiofile_2) == "audio"

    audiofile_3 = File("test_inputs/moreaudio.mp3")
    assert videogrep.get_file_type(audiofile_3) == "audio"


def test_inputs_type():
    segments_audio = [
        {
            "file": File("test_inputs/long-audio-wav.wav"),
            "start": 548.97,
            "end": 550.92,
            "content": "on on the in the enemy right over there",
        },
        {
            "file": File("test_inputs/audio.flac"),
            "start": 563.139082,
            "end": 565.62,
            "content": "over there at the filter going to rewriting",
        },
        {
            "file": File("test_inputs/file.mp3"),
            "start": 754.965,
            "end": 756.525,
            "content": "i will be over the minute they were going",
        },
    ]

    segments_mixed = [
        {
            "file": File("test_inputs/long-audio-wav.wav"),
            "start": 548.97,
            "end": 550.92,
            "content": "on on the in the enemy right over there",
        },
        {
            "file": File("test_inputs/audio.flac"),
            "start": 563.139082,
            "end": 565.62,
            "content": "over there at the filter going to rewriting",
        },
        {
            "file": File("test_inputs/file.mov"),
            "start": 754.965,
            "end": 756.525,
            "content": "i will be over the minute they were going",
        },
    ]

    segments_video = [
        {
            "file": File("test_inputs/bigvid.mp4"),
            "start": 548.97,
            "end": 550.92,
            "content": "on on the in the enemy right over there",
        },
        {
            "file": File("test_inputs/video.webm"),
            "start": 563.139082,
            "end": 565.62,
            "content": "over there at the filter going to rewriting",
        },
        {
            "file": File("test_inputs/file.mov"),
            "start": 754.965,
            "end": 756.525,
            "content": "i will be over the minute they were going",
        },
    ]

    assert videogrep.get_input_type(segments_audio) == "audio"
    assert videogrep.get_input_type(segments_mixed) == "audio"
    assert videogrep.get_input_type(segments_video) == "video"


def test_plans():
    segments_audio = [
        {
            "file": File("test_inputs/long-audio-wav.wav"),
            "start": 548.97,
            "end": 550.92,
            "content": "on on the in the enemy right over there",
        },
        {
            "file": File("test_inputs/audio.flac"),
            "start": 563.139082,
            "end": 565.62,
            "content": "over there at the filter going to rewriting",
        },
        {
            "file": File("test_inputs/file.mp3"),
            "start": 754.965,
            "end": 756.525,
            "content": "i will be over the minute they were going",
        },
    ]

    segments_mixed = [
        {
            "file": File("test_inputs/long-audio-wav.wav"),
            "start": 548.97,
            "end": 550.92,
            "content": "on on the in the enemy right over there",
        },
        {
            "file": File("test_inputs/audio.flac"),
            "start": 563.139082,
            "end": 565.62,
            "content": "over there at the filter going to rewriting",
        },
        {
            "file": File("test_inputs/file.mov"),
            "start": 754.965,
            "end": 756.525,
            "content": "i will be over the minute they were going",
        },
    ]

    segments_video = [
        {
            "file": File("test_inputs/bigvid.mp4"),
            "start": 548.97,
            "end": 550.92,
            "content": "on on the in the enemy right over there",
        },
        {
            "file": File("test_inputs/video.webm"),
            "start": 563.139082,
            "end": 565.62,
            "content": "over there at the filter going to rewriting",
        },
        {
            "file": File("test_inputs/file.mov"),
            "start": 754.965,
            "end": 756.525,
            "content": "i will be over the minute they were going",
        },
    ]

    video_output = File("test_outputs/somevideo.mp4")
    audio_output = File("test_outputs/someaudio.mp3")
    default_output = "supercut.mp4"

    assert videogrep.plan_no_action(segments_audio, video_output) == True
    # no action plan should let default video output filename come through
    # and then audio output plan should kick in for all audio input
    assert (
        videogrep.plan_no_action(segments_audio, default_output) == False
        and videogrep.plan_audio_output(segments_audio, default_output) == True
    )
    assert videogrep.plan_video_output(segments_video, video_output) == True
    assert videogrep.plan_audio_output(segments_video, audio_output) == True
    assert videogrep.plan_audio_output(segments_mixed, audio_output) == True
    assert videogrep.plan_audio_output(segments_audio, audio_output) == True


def test_cli():
    infile = File("test_inputs/manifesto.mp4")
    outfile = File("test_outputs/supercut.mp4")
    subprocess.run(
        [
            "poetry",
            "run",
            "videogrep",
            "--input",
            infile,
            "--output",
            outfile,
            "--search",
            "communist",
            "--search-type",
            "fragment",
            "--max-clips",
            "1",
        ]
    )

    assert get_duration(outfile) == approx(0.36)

    infile_audio = File("test_inputs/manifesto_audio.mp3")
    outfile_audio = File("test_outputs/supercut.mp3")
    subprocess.run(
        [
            "poetry",
            "run",
            "videogrep",
            "--input",
            infile_audio,
            "--output",
            outfile_audio,
            "--search",
            "communist",
            "--search-type",
            "fragment",
            "--max-clips",
            "1",
        ]
    )

    assert get_duration(outfile_audio) == approx(0.365714)
