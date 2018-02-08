# encoding=utf8
from __future__ import print_function
from __future__ import unicode_literals

import re
from bs4 import BeautifulSoup

def timestamp_to_secs(ts):
    hours, minutes, seconds = ts.split(':')
    return float(hours)*60*60 + float(minutes)*60 + float(seconds)


def secs_to_timestamp(secs):
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02f" % (h, m, s)


def parse_auto_sub(data):
    '''
    Parses webvtt and returns timestamps for words and lines
    Tested on automatically generated subtitles from YouTube
    '''

    out = []
    pat = r'<(\d\d:\d\d:\d\d(\.\d+)?)>'

    data = data.split('\n\n')
    data = [d.split('\n') for d in data]
    data = [d for d in data if len(d) == 2]

    for lines in data:
        meta, content = lines
        start, end = meta.split(' --> ')
        end = end.split(' ')[0]
        start = timestamp_to_secs(start)
        end = timestamp_to_secs(end)
        text = BeautifulSoup(content, 'html.parser').text
        words = text.split(' ')
        sentence = {'text': '', 'words': []}

        for word in words:
            item = {}
            item['start'] = start
            item['end'] = end
            word_parts = re.split(pat, word)
            item['word'] = word_parts[0]

            if len(word_parts) > 1:
                item['end'] = timestamp_to_secs(word_parts[1])

            sentence['words'].append(item)
            start = item['end']

        sentence['text'] = ' '.join([w['word'] for w in sentence['words']])
        out.append(sentence)

    for index, sentence in enumerate(out):
        if index == 0:
            continue

        first_word = sentence['words'][0]
        last_word = out[index-1]['words'][-1]

        if last_word['end'] > first_word['start']:
            last_word['end'] = first_word['start']

        sentence['start'] = sentence['words'][0]['start']
        sentence['end'] = sentence['words'][-1]['end']

    return out


def convert_to_srt(sentence):
    out = []
    for i, sentence in enumerate(sentence):
        out.append(str(i))
        start = sentence['words'][0]['start']
        end = sentence['words'][-1]['end']
        start = secs_to_timestamp(start)
        end = secs_to_timestamp(end)
        out.append('{} --> {}'.format(start, end))
        out.append(sentence['text'])
        out.append('')
    return '\n'.join(out)


def convert_to_sphinx(sentences):
    out = []
    for sentence in sentences:
        start = sentence['words'][0]['start']
        end = sentence['words'][-1]['end']
        out.append(sentence['text'])
        out.append('<s> {} {} .9'.format(start, start))
        for word in sentence['words']:
            out.append('{} {} {} {}'.format(word['word'], word['start'], word['end'], '.999'))
        out.append('</s> {} {} .9'.format(end, end))
    return '\n'.join(out)


if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as infile:
        text = infile.read()
    sentences = parse_auto_sub(text)
    print(convert_to_srt(sentences))

