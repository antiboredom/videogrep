import os

from videogrep import videogrep

filename = 'test_output.mp4'

def test_videogrep():
    videogrep.videogrep('test_videos/test.mp4',filename, 'video', 'pos')
    files = os.listdir('.')
    assert filename in files
