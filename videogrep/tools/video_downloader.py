import urllib
import time
import sys

from pytube import YouTube
import getyoutubecc
from bs4 import BeautifulSoup

def get_urls(url):
    data = urllib.urlopen(url).read()
    soup = BeautifulSoup(data)
    soupy_links = soup.select('a.yt-uix-sessionlink')
    urls = ['http://youtube.com' + link.get('href') for link in soupy_links\
                                                if 'watch' in link.get('href')]
    return set(urls)

def get_single_url(url, youtube_object=YouTube()):
#    try:
    youtube_object.url = url
    video = youtube_object.get('mp4', '720p')
    filename = youtube_object.filename
    video.download()
    cc = getyoutubecc.getyoutubecc(youtube_object.video_id,'en')
    cc.writeSrtFile(filename + '.srt')
#    except:
#        return 'Broke!' 


def search_all_files(search_url, youtube_object=YouTube()):
    search_url = search_url 
    urls = get_urls(search_url)
    yt = youtube_object
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
