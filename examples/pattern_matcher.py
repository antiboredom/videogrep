import sys
import videogrep
import spacy
from spacy.matcher import Matcher


"""
Uses rule-based matching from spacy to make supercuts:
https://spacy.io/usage/rule-based-matching

Requires spacy
"""

# the videos we are working with
videos = sys.argv[1:]

# load spacy and the pattern matcher
nlp = spacy.load("en_core_web_sm")

# grabs all instances of adjectives followed by nouns
patterns = [
    [{"POS": "ADJ"}, {"POS": "NOUN"}]
]

matcher = Matcher(nlp.vocab)
matcher.add("HelloWorld", patterns)


searches = []

for video in videos:
    transcript = videogrep.parse_transcript(video)
    for sentence in transcript:
        doc = nlp(sentence["content"])
        matches = matcher(doc)
        for match_id, start, end in matches:
            string_id = nlp.vocab.strings[match_id]  # Get string representation
            span = doc[start:end]  # The matched span
            searches.append(span.text)

videogrep.videogrep(
    videos, searches, search_type="fragment", output="pattern_matcher.mp4"
)
