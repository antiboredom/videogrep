from distutils.core import Command

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


try:
    with open('README.md') as readme:
        long_description = readme.read()
except IOError:
    long_description =''

class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys, subprocess
        errno = subprocess.call([sys.executable, 'runtest.py'])
        raise SystemExit(errno)


setup(name='videogrep',
      version = '0.5.10',
      description = 'Python utility for creating video out of their subtitle files',
      long_description = long_description,
      download_url = 'https://github.com/antiboredom/videogrep/archive/master.zip',
      url='http://github.com/antiboredom/videogrep',
      author = 'Sam Lavigne',
      author_email = 'splavigne@gmail.com',
      test_suite = 'videogrep.tests',
      packages = ['videogrep','videogrep.tools','videogrep.tests'],
      install_requires= ['audiogrep', 'moviepy', 'beautifulsoup4'],
      scripts = ['bin/videogrep'],
      classifiers = [],
      license='MIT',
      cmdclass = {'test': PyTest})
