import os

from subprocess import call

from videogrep import videogrep

filename = 'TEST_OUTPUT.mp4'

def test_videogrep():
    videogrep.videogrep('test_videos/test.mp4', filename, 'video', 'pos')
    files = os.listdir('.')
    assert filename in files

def test_cli():
    command = 'videogrep_cli.py -i test_videos/test.mp4 -s video -st pos'
    call(command.split())
    files = os.listdir('.')
    assert 'supercut.mp4' in files

def test_cleanup():
    call(['rm', filename])
    call(['rm', 'supercut.mp4'])
