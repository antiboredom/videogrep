import os

from subprocess import call

from videogrep import videogrep

filename = 'TEST_OUTPUT.mp4'

def test_videogrep():
    files = os.listdir('.')
    if filename in files:
        call(['rm',filename])
    videogrep('test_videos/test.mp4', 'video', 'pos')
    assert filename in files
    call(['rm', filename])

def test_cli():
    command = 'videogrep.py -i test_videos/test.mp4 -s video -st pos'
    call(command.split())
    files = os.listdir('.')
    assert 'supercut.mp4' in files

