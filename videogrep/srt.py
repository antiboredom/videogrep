import re
import io
from typing import Tuple, Union, List


def convert_timespan(timespan:str) -> Tuple[float, float]:
    """
    Convert an srt timespan into a start and end timestamp.

    :param timespan str: Srt timespan
    :rtype Tuple[float, float]: start and end in seconds
    """

    start, end = timespan.split("-->")
    start = convert_timestamp(start)
    end = convert_timestamp(end)
    return (start, end)


def convert_timestamp(timestamp:str) -> float:
    """
    Convert an srt timestamp into seconds.

    :param timestamp str: An srt timestamp
    :rtype float: Seconds
    """

    timestamp = timestamp.strip()
    chunk, millis = timestamp.split(",")
    hours, minutes, seconds = chunk.split(":")
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    seconds = seconds + hours * 60 * 60 + minutes * 60 + float(millis) / 1000
    return seconds


def parse(srt:Union[io.IOBase, str]) -> List[dict]:
    """
    Converts an srt file into a list of dictionary timestamps

    :param srt Union[io.IOBase, str]: srt content or file reader
    :rtype List[dict]: List of timestamps and content
    """

    _srt:str = ""

    if isinstance(srt, io.IOBase):
        _srt = srt.read()
    else:
        _srt = srt

    out = []

    _srt = re.sub(r"^\d+[\n\r]", "", _srt, flags=re.MULTILINE)
    lines = _srt.splitlines()


    for line in lines:
        line = line.strip()
        if line == "":
            continue
        if "-->" in line:
            if len(out) > 0:
                out[-1]["content"] = out[-1]["content"].strip()
            start, end = convert_timespan(line)
            item = {"start": start, "end": end, "content": ""}
            out.append(item)
        else:
            out[-1]["content"] += line + " "

    return out
