try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    with open('README.md') as readme:
        long_description = readme.read()
except IOError, ImportError:
    long_description =''

with open('requirements.txt', 'r') as requirements:
    install_requires = requirements.read().split()

setup(name='videogrep',
      version = '0.4',
      description = 'Python utility for creating video out of their subtitle files',
      long_description = long_description,
      author = 'Sam Lavigne',
      author_email = 'splavigne@gmail.com',
      install_requires = install_requires)
