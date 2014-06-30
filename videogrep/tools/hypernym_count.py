import sys
from pattern.en import wordnet, parse, tag


def hypernym_search(text, search_word):
    output = []
    synset = wordnet.synsets(search_word)[0]
    pos = synset.pos
    possible_words = re_search(text, pos)
    for match in possible_words:
        word = match[0].string
        synsets = wordnet.synsets(word)
        if len(synsets) > 0:
            hypernyms = synsets[0].hypernyms(recursive=True)
            if any(search_word == h.senses[0] for h in hypernyms):
                output.append(word)
    return set(output)

text = sys.stdin.read()

hypernyms = {}
for word, pos in tag(text):
    synsets = wordnet.synsets(word)
    if len(synsets) > 0:
        try:
            hypernym = synsets[0].hypernyms()[0].senses[0]
            if hypernym in hypernyms:
                hypernyms[hypernym] += 1
            else:
                hypernyms[hypernym] = 1
        except:
            next

for hypernym in sorted(hypernyms, key=hypernyms.get, reverse=True):
    count = hypernyms[hypernym]
    print hypernym + ": " + str(count)
