import videogrep
import os
from pytest import approx

srt_subs = """
1
00:00:00,498 --> 00:00:02,827
A spectre is haunting Europe.

2
00:00:02,827 --> 00:00:06,383
The spectre of Communism.
All the powers of old Europe

3
00:00:06,383 --> 00:00:09,427
have entered into a holy alliance
"""


def File(path):
    return os.path.join(os.path.dirname(__file__), path)


def test_version():
    assert videogrep.__version__ == "2.0.0"


def test_srts():
    parsed = videogrep.srt.parse(srt_subs)
    assert parsed[0]["content"] == "A spectre is haunting Europe."
    assert parsed[0]["start"] == approx(0.498)
    assert parsed[0]["end"] == approx(2.827)

    assert (
        parsed[1]["content"] == "The spectre of Communism. All the powers of old Europe"
    )
    assert parsed[1]["start"] == approx(2.827)
    assert parsed[1]["end"] == approx(6.383)


def test_cued_vtts():
    testfile = File("test.vtt")
    with open(testfile) as infile:
        parsed = videogrep.vtt.parse(infile)
    assert parsed[0]["content"] == "hi i'm sam and i'm the inventor"
    assert parsed[0]["start"] == approx(0.16)
    assert parsed[0]["end"] == approx(3.59)

    word = parsed[0]["words"][0]
    assert word["word"] == "hi"
    assert word["start"] == approx(0.16)
    assert word["end"] == approx(0.96)


def test_find_sub():
    testvid = File("test.mp4")
    testvtt = File("test.vtt")
    assert videogrep.find_transcript(testvid) == testvtt


def test_parse_transcript():
    pass


def test_export_xml():
    pass


def test_export_edl():
    pass


def test_export_m3u():
    pass


def test_ngrams():
    pass


def test_export_files():
    pass


def test_videogrep():
    pass


def test_create_supercut():
    pass


def test_sentence_search():
    testvid = File("test.mp4")
    query = "zoom"
    segments = videogrep.search(testvid, query)
    for s in segments:
        assert query in s["content"]
    assert len(segments) == 11


def test_no_transcript():
    testvid = File("whatever.mp4")
    segments = videogrep.search(testvid, "*", search_type="fragment")
    assert len(segments) == 0


def test_word_search():
    testvid = File("test.mp4")
    segments = videogrep.search(testvid, "zoom", search_type="fragment")
    assert len(segments) == 11

    segments = videogrep.search(testvid, "zoom escaper", search_type="fragment")
    assert len(segments) == 5

    segments = videogrep.search(testvid, "alskdfj asldjf", search_type="fragment")
    assert len(segments) == 0

    segments = videogrep.search(testvid, "alskdfj zoom", search_type="fragment")
    assert len(segments) == 0

    segments = videogrep.search(testvid, "zoom .*", search_type="fragment")
    assert len(segments) == 10

    segments = videogrep.search(testvid, "ing$", search_type="fragment")
    assert len(segments) == 13
