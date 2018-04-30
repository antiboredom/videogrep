try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


try:
    with open('README.md') as readme:
        long_description = readme.read()
except IOError:
    long_description =''

setup(name='videogrep',
      version = '2.0.0',
      description = 'Python utility for creating video out of their subtitle files',
      long_description = long_description,
      download_url = 'https://github.com/antiboredom/videogrep/archive/master.zip',
      url='http://github.com/antiboredom/videogrep',
      author = 'Sam Lavigne',
      author_email = 'splavigne@gmail.com',
      test_suite = 'tests',
      packages = ['videogrep','videogrep.tools'],
      install_requires= ['audiogrep', 'moviepy', 'beautifulsoup4'],
      scripts = ['bin/videogrep'],
      classifiers = [],
      license='MIT')
