from pytube import YouTube
import getyoutubecc
from bs4 import BeautifulSoup
import urllib
import time
import sys

def get_urls(url):
    data = urllib.urlopen(url).read()
    soup = BeautifulSoup(data)
    soupy_links = soup.select('a.yt-uix-sessionlink')
    urls = ['http://youtube.com' + link.get('href') for link in soupy_links if 'watch' in link.get('href')]
    return set(urls)


search_url = sys.argv[1]
urls = get_urls(search_url)
yt = YouTube()
for url in urls:
    try:
        print "downloading " + url
        yt.url = url
        video = yt.get('mp4', '720p')
        filename = yt.filename
        video.download()
        time.sleep(.1)
        cc = getyoutubecc.getyoutubecc(yt.video_id,'en')
        cc.writeSrtFile(filename + '.srt')
        time.sleep(.1)
    except:
        print "couldn't download " + url

