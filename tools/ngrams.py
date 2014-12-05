import sys
from pattern.en import ngrams


class NGram(object):

    def __init__(self, total, threshold=10):
        self.total = total
        self.threshold = threshold
        self.text = ''
        self.ngramcount = {}
        self.output = []

    def feed(self, text):
        self.text = self.text + text

    def ngram_count(self):
        grams = ngrams(self.text, n=self.total)
        for gram in grams:
            if gram in self.ngramcount:
                self.ngramcount[gram] += 1
            else:
                self.ngramcount[gram] = 1

    def frequent(self):
        for gram in sorted(self.ngramcount, key=self.ngramcount.get,
                           reverse=True):
            count = self.ngramcount[gram]
            if count > self.threshold and all(len(x) > 0 for x in gram):
                self.output.append(' '.join(gram))
        return self.output


if __name__ == '__main__':
    import sys
    import os
    inputfile = sys.argv[1]
    total = int(sys.argv[2])
    threshold = int(sys.argv[3])
    srts = []

    if os.path.isfile(inputfile):
        filename = inputfile.split('.')
        filename[-1] = 'srt'
        srts = ['.'.join(filename)]

    elif os.path.isdir(inputfile):
        if not inputfile.endswith('/'):
            inputfile += '/'
        srts = [inputfile + f for f in os.listdir(inputfile) if
                f.lower().endswith('srt')]

    ngrammer = NGram(total, threshold)
    for srt in srts:
        f = open(srt, 'r')
        text = f.read()
        f.close()
        ngrammer.feed(text)

    ngrammer.ngram_count()
    for gram in sorted(ngrammer.ngramcount, key=ngrammer.ngramcount.get,
                       reverse=True):
        count = ngrammer.ngramcount[gram]
        word = ' '.join(gram)
        if count > threshold and len(word) > 3:
            print count, word
