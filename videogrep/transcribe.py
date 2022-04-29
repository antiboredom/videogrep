from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import os
import subprocess
import json

MAX_CHARS = 36
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")

SetLogLevel(-1)


def transcribe(videofile):
    # if not os.path.exists(MODEL_PATH):
    #     print(
    #         "Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder."
    #     )
    #     exit(1)

    transcript_file = os.path.splitext(videofile)[0] + ".json"

    if os.path.exists(transcript_file):
        with open(transcript_file, "r") as infile:
            data = infile.read()
        return data

    print("Transcribing", videofile)

    sample_rate = 16000
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, sample_rate)
    rec.SetWords(True)

    process = subprocess.Popen(
        [
            "ffmpeg",
            "-loglevel",
            "quiet",
            "-i",
            videofile,
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "-f",
            "s16le",
            "-",
        ],
        stdout=subprocess.PIPE,
    )

    while True:
        data = process.stdout.read(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)

    out = []
    data = json.loads(rec.FinalResult())
    words = [w for w in data["result"]]
    item = {"content": "", "start": None, "end": None, "words": []}
    for w in words:
        item["content"] += w["word"] + " "
        item["words"].append(w)
        if len(item["content"]) > MAX_CHARS or w == words[-1]:
            item["content"] = item["content"].strip()
            item["start"] = item["words"][0]["start"]
            item["end"] = item["words"][-1]["end"]
            out.append(item)
            item = {"content": "", "start": None, "end": None, "words": []}

    with open(transcript_file, "w") as outfile:
        json.dump(out, outfile)

    return out
