import re
import io
from bs4 import BeautifulSoup
from typing import Union, List


def timestamp_to_secs(ts: str) -> float:
    """
    Convert a timestamp to seconds

    :param ts str: Timestamp
    :rtype float: Seconds
    """
    hours, minutes, seconds = ts.split(":")
    return float(hours) * 60 * 60 + float(minutes) * 60 + float(seconds)


def secs_to_timestamp(secs: float) -> str:
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02f" % (h, m, s)


def parse_cued(data: List[str]) -> List[dict]:
    out = []
    pat = r"<(\d\d:\d\d:\d\d(\.\d+)?)>"

    for lines in data:
        meta, content = lines
        start, end = meta.split(" --> ")
        end = end.split(" ")[0]
        start = timestamp_to_secs(start)
        end = timestamp_to_secs(end)
        text = BeautifulSoup(content, "html.parser").text
        words = text.split(" ")
        sentence = {"content": "", "words": []}

        for word in words:
            item = {}
            item["start"] = start
            item["end"] = end
            word_parts = re.split(pat, word)
            item["word"] = word_parts[0]

            if len(word_parts) > 1:
                item["end"] = timestamp_to_secs(word_parts[1])

            sentence["words"].append(item)
            start = item["end"]

        sentence["content"] = " ".join([w["word"] for w in sentence["words"]])
        out.append(sentence)

    for index, sentence in enumerate(out):
        if index == 0:
            sentence["start"] = sentence["words"][0]["start"]
            sentence["end"] = sentence["words"][-1]["end"]
            continue

        first_word = sentence["words"][0]
        last_word = out[index - 1]["words"][-1]

        if last_word["end"] > first_word["start"]:
            last_word["end"] = first_word["start"]

        sentence["start"] = sentence["words"][0]["start"]
        sentence["end"] = sentence["words"][-1]["end"]

    return out


def parse_uncued(data: str) -> List[dict]:
    out = []
    lines = [d.strip() for d in data.split("\n") if d.strip() != ""]
    out = [{"content": "", "start": None, "end": None}]
    for line in lines:
        if " --> " in line:
            start, end = line.split(" --> ")
            end = end.split(" ")[0]
            start = timestamp_to_secs(start)
            end = timestamp_to_secs(end)
            if out[-1]["start"] is None:
                out[-1]["start"] = start
                out[-1]["end"] = end
            else:
                out.append({"content": "", "start": start, "end": end})
        else:
            if out[-1]["start"] is not None:
                out[-1]["content"] += " " + line.strip()

    for o in out:
        o["content"] = o["content"].strip()

    return out


def parse(vtt: Union[io.IOBase, str]) -> List[dict]:
    """
    Parses webvtt and returns timestamps for words and lines
    Tested on automatically generated subtitles from YouTube
    """

    _vtt: str = ""
    if isinstance(vtt, io.IOBase):
        _vtt = vtt.read()
    else:
        _vtt = vtt

    pat = r"<(\d\d:\d\d:\d\d(\.\d+)?)>"
    out = []

    lines = []
    data = _vtt.split("\n")
    data = [d for d in data if re.search(r"\d\d:\d\d:\d\d", d) is not None]
    for i, d in enumerate(data):
        if re.search(pat, d):
            lines.append((data[i - 1], d))

    if len(lines) > 0:
        out = parse_cued(lines)
    else:
        out = parse_uncued(_vtt)

    return out


def convert_to_srt(sentence):
    out = []
    for i, sentence in enumerate(sentence):
        out.append(str(i))
        start = sentence["words"][0]["start"]
        end = sentence["words"][-1]["end"]
        start = secs_to_timestamp(start)
        end = secs_to_timestamp(end)
        out.append("{} --> {}".format(start, end))
        out.append(sentence["text"])
        out.append("")
    return "\n".join(out)

def render(segments: List[dict], outputfile: str):
    """
    Render a list of segments to a WebVTT file
    
    :param segments: List of segments as returned by videogrep.search
    :param outputfile: Filename for the WebVTT output
    """

    start = 0.0
    with open(outputfile, "w", encoding="utf-8") as outfile:
        outfile.write("WEBVTT\n")
        for index, s in enumerate(segments):
            clip_duration = s["end"] - s["start"]
            end = start + clip_duration
            start_t = secs_to_timestamp(start)
            end_t = secs_to_timestamp(end)
            outfile.write(f"\n{index}\n{start_t} --> {end_t}\n{s['content']}\n")
            start = end
