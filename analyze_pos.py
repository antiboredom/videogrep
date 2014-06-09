from pattern.en import tag, tokenize
import sys

text = sys.stdin.read()
tags = tag(text)
pos = [t[1] for t in tags]
ngrams = {}
n = int(sys.argv[1])

for i in range(len(pos) - n + 1):
    gram = tuple(pos[i:i+n])
    if gram in ngrams:
        ngrams[gram] += 1
    else:
        ngrams[gram] = 1

for ngram in sorted(ngrams, key=ngrams.get, reverse=True):
    count = ngrams[ngram]
    if count > 4:
        print ' '.join(ngram) + ": " + str(count)

