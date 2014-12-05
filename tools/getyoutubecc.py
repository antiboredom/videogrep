#!/usr/bin/python

import urllib
import HTMLParser
import re
import codecs


class getyoutubecc():
    """ This class allows you to download the caption from a video from youtube
        Example:
            >>> import getyoutubecc
            #import the library
            >>> cc = getyoutubecc.getyoutubecc('2XraaWefBd8','en')
            # Now in cc.caption_obj are the parsed captions, its syntax is like
            # [{'texlines': [u"caption first line", 'caption second line'],
            #    'time': {'hours':'1', 'min':'2','sec':44,'msec':232} }]
            # Modify the caption as you want if desired
            >>> cc.writeSrtFile('captionsfile.srt')
            #write the contents to a srt file
         Note:
            MULTITRACK VIDEO
            if video is a multitrack video (or the track has a name) you need
            to specify the name of the track:
            >>> cc = getyoutubecc.getyoutubecc('pNiFoYt69-w','fr','french')
            TRANSLATE VIDEO
            if you prefer the automatic translation to another language use
            the lang code
            >>> cc = getyoutubecc.getyoutubecc('pNiFoYt69-w', 'fr', 'french', \
                tlang:'es')
    """

    caption_obj = {}

    """ This object contains the fetched captions. Use this to treat the
    captions or whatever"""

    def __init__(self, video_id, lang="en", track="", tlang=""):
        """ """
        # Obtain the file from internet
        cc_url = "http://www.youtube.com/api/timedtext?v=" + video_id + \
                 "&lang=" + lang + "&name=" + track + "&tlang=" + tlang
        print "video id: " + video_id
        print "video language: " + lang
        print "video track: " + track
        print "translate video to: " + tlang
        try:
            cc = urllib.urlopen(cc_url).read()
        except:
            print "Problem with connection"
        # parse the file to make a easy to modify object with the captions
        # and its time
        if self.caption_obj == []:
            print "url " + cc_url + " was an empty response. Multitrack video?"
        self.caption_obj = self._parseXml(cc)

    def writeSrtFile(self, filename="caption"):
        srt_lines = self._generateSrt(self.caption_obj)  # generate a srt file
        srtfile = open(filename, 'w')
        for line in srt_lines:
            srtfile.write(line.encode('utf8') + "\n")

    def _parseXml(self, cc):
        """ INPUT: XML file with captions
            OUTPUT: parsed object like:
                [{'texlines': [u"So, I'm going to rewrite this", 'in a more
                concise form as'],
                'time': {'hours':'1', 'min':'2','sec':44,'msec':232} }]
        """
        htmlpar = HTMLParser.HTMLParser()
        # ['<text start="2997.929">So, it will\nhas time',
        # '<text start="3000.929">blah', ..]
        cc = cc.split("</text>")
        captions = []
        for line in cc:
            if re.search('text', line):
                time = re.search(r'start="(\d+)(?:\.(\d+)){0,1}',
                                 line).groups()  # ('2997','929')
                time = (int(time[0]), int(0 if not time[1] else time[1]))
                # convert seconds and millisec to int
                # extract text i.e. 'So, it will\nhas time'
                text = re.search(r'">(.*)', line, re.DOTALL).group(1)
                textlines = [htmlpar.unescape(htmlpar.unescape(unicode(
                    lineunparsed, "utf-8"))) for lineunparsed in
                    text.split('\n')]  # unescape chars like &amp; or &#39;
                ntime = {'hours': time[0] / 3600, "min": time[0] % 3600 / 60,
                         "sec": time[0] % 3600 % 60, "msec": time[1]}
                captions.append({'time': ntime, 'textlines': textlines})
        return captions

    def _generateSrt(self, captions):
        """ INPUT: array with captions, i.e.
                [{'texlines': [u"So, I'm going to rewrite this", 'in a more
                concise form as'], 'time': {'hours':'1', 'min':'2','sec':44,
                'msec':232} }]
            OUTPUT: srtformated string
        """
        caption_number = 0
        srt_output = []
        for caption in captions:
            caption_number += 1
            # CAPTION NUMBER
            srt_output.append(str(caption_number))
            # TIME
            time_from = (caption['time']['hours'], caption['time']['min'],
                         caption['time']['sec'], caption['time']['msec'])
            if len(captions) > caption_number:
                # display caption until next one
                next_caption_time = captions[caption_number]['time']
                time_to = (next_caption_time['hours'],
                           next_caption_time['min'], next_caption_time['sec'],
                           next_caption_time['msec'])
            else:
                # display caption for 2 seconds
                time_to = (time_from[0], time_from[1] + 2, time_from[2],
                           time_from[3])
            srt_output.append((":").join([str(i) for i in time_from[0:-1]])
                              + "," + str(time_from[-1]) + " --> " +
                              (":").join([str(i) for i in time_to[0:-1]])
                              + "," + str(time_to[-1]))
            # CAPTIONS
            for caption_line in caption['textlines']:
                srt_output.append(caption_line)
            # Add two empty lines to serarate every caption showed
            srt_output.append("")
            srt_output.append("")
        return srt_output


if __name__ == "__main__":
    import sys
    import getopt

    sys.argv

    videoid = ''
    lang = ''
    track = ''
    tlang = ''

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv:l:t:T:",
                                   ["videoid=", "language=", "track=",
                                    "translate="])
    except getopt.GetoptError:
        print 'getyoutubecc -v <video_id> -l <language_id> -t <track_name> ' \
              '-T <translate_to>'
        print 'Example: getyoutubecc -v pNiFoYt69-w -l fr -t french -T es'
        print 'Example: getyoutubecc -v 2XraaWefBd8 -l en '
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'getyoutubecc -v <video_id> -l <language_id> -t ' \
                  '<track_name> -T <translate_to>'
            print 'Example: getyoutubecc -v pNiFoYt69-w -l fr -t french -T es'
            print 'Example: getyoutubecc -v 2XraaWefBd8 -l en '
            print 'NOTE: if video has a track name, the -t argument is ' \
                  'mandatory '
            sys.exit()
        elif opt in ("-v", "--videoid"):
            videoid = arg
        elif opt in ("-l", "--language"):
            lang = arg
        elif opt in ("-t", "--track"):
            track = arg
        elif opt in ("-T", "--translate"):
            tlang = arg
    if videoid != '':
        print "downloading " + videoid + " captions"
        cc = getyoutubecc(videoid, lang, track, tlang)
        cc.writeSrtFile(videoid + '.srt')
    else:
        print 'getyoutubecc -v <video_id> -l <language_id> -t <track_name> ' \
              '-T <translate_to>'
        print 'Example: getyoutubecc -v pNiFoYt69-w -l fr -t french -T es'
        print 'Example: getyoutubecc -v 2XraaWefBd8 -l en '
        print 'NOTE: if video has a track name, the -t argument is mandatory '
