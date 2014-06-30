import os

from uuid import uuid4

from videogrep import videogrep

filename = 'test.mp4'

def test_videogrep():
    videogrep.videogrep('google_vids/Automatic Captions in YouTube Demo.mp4',filename, 'video', 'pos')
    files = os.listdir('.')
    assert filename in files
