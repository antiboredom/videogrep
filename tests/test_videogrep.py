import videogrep
import os
import re
from collections import Counter
from moviepy.editor import VideoFileClip
from pytest import approx
import glob
import subprocess


def File(path):
    return os.path.join(os.path.dirname(__file__), path)


def test_version():
    assert videogrep.__version__ == "2.1.1"


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

    testvid = File("test_inputs/emptyvideo.mp4")
    testsubfile = File("test_inputs/emptyvideo.aa.vtt")
    assert videogrep.find_transcript(testvid) == testsubfile

    testvid = File("test_inputs/emptyvideo 2.mp4")
    testsubfile = File("test_inputs/emptyvideo 2.mp4.aa.vtt")
    assert videogrep.find_transcript(testvid) == testsubfile

    testvid = File("test_inputs/fakevideo.mp4")
    assert videogrep.find_transcript(testvid) == None

    testvid = File("test_inputs/Some Random Video [Pj-h6MEgE7I].mp4")
    testsubfile = File("test_inputs/Some Random Video [Pj-h6MEgE7I].de.vtt")
    assert videogrep.find_transcript(testvid) == testsubfile


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
    files = glob.glob(File("test_outputs/") + "supercut_clip*.mp4")
    assert len(files) == 4
    testfile = VideoFileClip(files[0])
    assert testfile.duration == approx(0.52)


def test_videogrep():
    out1 = File("test_outputs/supercut1.mp4")
    videogrep.videogrep(
        File("test_inputs/manifesto.mp4"),
        "communist|communism",
        search_type="fragment",
        output=out1,
    )
    testfile = VideoFileClip(out1)
    assert testfile.duration == approx(4.64)

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
    testfile = VideoFileClip(out2)
    assert testfile.duration == approx(6.24)

    # if os.path.exists(out2):
    #     os.remove(out2)


def test_no_transcript():
    testvid = File("test_inputs/whatever.mp4")
    segments = videogrep.search(testvid, "*", search_type="fragment")
    assert len(segments) == 0


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

    clip = VideoFileClip(outfile)
    assert clip.duration == approx(0.36)
