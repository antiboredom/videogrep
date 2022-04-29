import re
import io
import os
from subprocess import run


def convert_to_wav(videofile):
    """Converts files to a format that pocketsphinx can deal wtih (16khz mono 16bit wav)"""
    wav_file = videofile + ".temp.wav"
    if not os.path.exists(wav_file):
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                videofile,
                "-acodec",
                "pcm_s16le",
                "-ac",
                "1",
                "-ar",
                "16000",
                wav_file,
            ]
        )
    return wav_file


def transcribe(videofile):
    """Uses pocketsphinx to transcribe audio files"""

    transcript_file = os.path.splitext(videofile)[0] + ".transcript"

    if os.path.exists(transcript_file):
        with open(transcript_file, "r") as infile:
            return infile.read()

    print("Transcribing", videofile)
    wav_file = convert_to_wav(videofile)
    transcript = run(
        [
            "pocketsphinx_continuous",
            "-infile",
            wav_file,
            "-time",
            "yes",
            "-logfn",
            "/dev/null",
        ],
        capture_output=True,
    ).stdout.decode("utf-8")

    with open(transcript_file, "w") as outfile:
        outfile.write(transcript)

    os.remove(wav_file)

    return transcript


def parse(transcript):
    """
    Parses pocketsphinx transcript and returns timestamps for words and lines
    """

    if isinstance(transcript, io.IOBase):
        transcript = transcript.read()

    sentences = []

    lines = transcript.split("\n")

    lines = [re.sub(r"\(.*?\)", "", l).strip().split(" ") for l in lines]
    lines = [l for l in lines if len(l) == 4]

    seg_start = -1
    seg_end = -1

    for index, line in enumerate(lines):
        word, start, end, conf = line
        if word == "<s>" or word == "<sil>" or word == "</s>":
            if seg_start == -1:
                seg_start = index
                seg_end = -1
            else:
                seg_end = index

            if seg_start > -1 and seg_end > -1:
                words = lines[seg_start + 1 : seg_end]
                words = [
                    {"word": w[0], "start": float(w[1]), "end": float(w[2])}
                    for w in words
                ]
                content = " ".join([w["word"] for w in words])
                start = float(lines[seg_start][1])
                end = float(lines[seg_end][1])
                if words:
                    sentences.append(
                        {"start": start, "end": end, "content": content, "words": words}
                    )
                if word == "</s>":
                    seg_start = -1
                else:
                    seg_start = seg_end
                seg_end = -1

    return sentences


if __name__ == "__main__":
    import sys

    for f in sys.argv[1:]:
        transcript = transcribe(f)
        out = parse(transcript)
        print(out)
