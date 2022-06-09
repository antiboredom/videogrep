import sys
import videogrep
import spacy

"""
Make a supercut of different types of words, for example, all nouns.

To use:

1) Install spacy: pip3 install spacy
2) Download the small model: python -m spacy download en_core_web_sm
3) Update the "parts_of_speech" list below to change what you're searching for
4) Run: python3 parts_of_speech.py somevideo.mp4
"""

# load spacy
nlp = spacy.load("en_core_web_sm")

# the videos we are working with
videos = sys.argv[1:]

# create a list of types of words we are looking for
# can be anything from:
# https://universaldependencies.org/u/pos/
parts_of_speech = ["NOUN"]


search_words = []

for video in videos:
    transcript = videogrep.parse_transcript(video)
    for sentence in transcript:
        doc = nlp(sentence["content"])
        for token in doc:
            # token.pos_ has Coarse-grained part-of-speech
            # switch to token.tag_ if you want fine-grained pos
            if token.pos_ in parts_of_speech:
                # ensure we're only going to grab exact words
                search_words.append(f"^{token.text}$")

query = "|".join(search_words)
videogrep.videogrep(
    videos, query, search_type="fragment", output="part_of_speech_supercut.mp4"
)
