from __future__ import print_function

import sys
import random
# from pattern.search import Pattern, STRICT, search
# from pattern.en import parsetree, wordnet, ngrams


def re_search(text, search_string, strict=False):
    try:
        from pattern.search import STRICT, search
        from pattern.en import parsetree
    except:
        print('Please install pattern: pip install https://github.com/clips/pattern/archive/development.zip')
        sys.exit()

    tree = parsetree(text, lemmata=True)
    if strict:
        results = search(search_string, tree, STRICT)
    else:
        results = search(search_string, tree)
    return results


def search_out(text, search_string, strict=False):
    results = re_search(text, search_string, strict)
    output = []
    for match in results:
        sent = []
        for word in match:
            sent.append(word.string)
        output.append(" ".join(sent))
    return output


def contains(text, search_string):
    results = re_search(text, search_string)
    return len(results) > 0


def hypernym_search(text, search_word):
    try:
        from pattern.en import wordnet
    except:
        print('Please install pattern: pip install https://github.com/clips/pattern/archive/development.zip')
        sys.exit()

    output = []
    try:
        for search_word in search_word.split('|'):
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
    except IndexError:
        pass

    return set(output)


def hypernym_combo(text, category, search_pattern):
    possibilities = search_out(text, search_pattern)
    output = []
    for p in possibilities:
        if len(hypernym_search(p, category)) > 0:
            output.append(p)
    return output


def list_hypernyms(search_word):
    try:
        from pattern.en import wordnet
    except:
        print('Please install pattern: pip install https://github.com/clips/pattern/archive/development.zip')
        sys.exit()

    output = []
    for synset in wordnet.synsets(search_word):
        hypernyms = synset.hypernyms(recursive=True)
        output.append([h.senses[0] for h in hypernyms])
    return output


def random_hyponym(word):
    to_return = ''
    hyponyms = list_hyponyms(word)
    if len(hyponyms) > 0:
        to_return = random.choice(hyponyms)
    return to_return


def list_hyponyms(word):
    try:
        from pattern.en import wordnet
    except:
        print('Please install pattern: pip install https://github.com/clips/pattern/archive/development.zip')
        sys.exit()

    output = []
    synsets = wordnet.synsets(word)
    if len(synsets) > 0:
        hyponyms = synsets[0].hyponyms(recursive=True)
        output = [h.senses[0] for h in hyponyms]
    return output


if __name__ == '__main__':

    import sys

    results = list_hypernyms(sys.argv[1])
    for result in results:
        print(result)
