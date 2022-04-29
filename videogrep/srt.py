import re
import io


def convert_timespan(timespan):
    """Convert an srt timespan into a start and end timestamp."""
    start, end = timespan.split("-->")
    start = convert_timestamp(start)
    end = convert_timestamp(end)
    return (start, end)


def convert_timestamp(timestamp):
    """Convert an srt timestamp into seconds."""
    timestamp = timestamp.strip()
    chunk, millis = timestamp.split(",")
    hours, minutes, seconds = chunk.split(":")
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    seconds = seconds + hours * 60 * 60 + minutes * 60 + float(millis) / 1000
    return seconds


def parse(srt):
    """
    Converts an srt file into a dictionary
    """

    if isinstance(srt, io.IOBase):
        srt = srt.read()

    out = []

    srt = re.sub(r"^\d+[\n\r]", "", srt, flags=re.MULTILINE)
    lines = srt.splitlines()


    for line in lines:
        line = line.strip()
        if line == "":
            continue
        print(line)
        if "-->" in line:
            if len(out) > 0:
                out[-1]["content"] = out[-1]["content"].strip()
            start, end = convert_timespan(line)
            item = {"start": start, "end": end, "content": ""}
            out.append(item)
        else:
            out[-1]["content"] += line + " "

    return out
