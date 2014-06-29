Videogrep
=========

Videogrep searches through dialog in video files (using .srt subtitle tracks) and makes supercuts based on what it finds.

##Requirements
Clone this repository, and then install [pattern](http://www.clips.ua.ac.be/pages/pattern-search) and [moviepy](https://github.com/Zulko/moviepy) along with the other requirements.
```
pip install -r requirements.txt
```

Install [ffmpeg](http://ffmpeg.org/) with Ogg/Vorbis support. If you're on a mac with homebrew you can install ffmpeg with:
```
brew install ffmpeg --with-libvpx --with-libvorbis
```

You may need to change the path to your installation of ffmpeg by modifying the first line of videogrep.py:
```python
FFMPEG_BINARY = '/usr/local/bin/ffmpeg'
```

##How to use it
The most basic use:
```
python videogrep.py --input path/to/video_or_folder --search 'search phrase'
```
You can put any regular expression in the search phrase.

You can also search for part-of-speech tags using Pattern. See the [Pattern-Search documentation](http://www.clips.ua.ac.be/pages/pattern-search) for some details about how this works, and the [Penn Treebank tag set](http://www.clips.ua.ac.be/pages/mbsp-tags) for a list of usuable part-of-speech tags. For example the following will search for every line of dialog that contains an adjective (JJ) followed by a singular noun (NN):
```
python videogrep.py --input path/to/video_or_folder --search 'JJ NN' --search-type pos
```
You can also do a [hypernym](https://en.wikipedia.org/wiki/Hypernym) search - which essentially searches for words that fit into a specific category. The following, for example, will search for any line of dialog that references a liquid (like water, coffee, beer, etc.):
```
python videogrep.py --input path/to/video_or_folder --search 'liquid' --search-type hyper
```

**NOTE: videogrep requires the subtitle track and the video file to have the exact same name, up to the extension.** For example, my_movie.mp4 and my_movie.srt will work, my_movie.mp4 and my_movie_subtitle.srt will not work.

###Options

videogrep can take a number of options:

####--input / -i
Video or subtitle file, or folder containing multiple files

####--output / -o
Name of the file to generate. By default this is "supercut.mp4"

####--search / -s
Search term

###--search-file / -sf
A file with multiple search terms

####--search-type / -st
Type of search you want to perform. There are three options:
* re: [regular expression](http://www.pyregex.com/) (this is the default).
* pos: part of speech search (uses [pattern.search](http://www.clips.ua.ac.be/pages/pattern-search)). For example 'JJ NN' would return all lines of dialog that contain an adjective followed by a noun.
* hyper: hypernym search. For example 'body parts' grabs all lines of dialog that reference a body part

####--max-clips / -m 
Maximum number of clips to use for the supercut

####--test / -t
Show the search results without making the supercut

####--randomize / -r
Randomize the order of the clips

####--padding / -p
Padding in milliseconds to add to the start and end of each clip

####--unique / -u
Take only the first result for search term

####--ordered / -or
In case of multiple search terms order the final videos in the same order as search terms list


##Samples
* [All the instances of the phrase "time" in the movie "In Time"](https://www.youtube.com/watch?v=PQMzOUeprlk)
* [All the one to two second silences in "Total Recall"](https://www.youtube.com/watch?v=qEtEbXVbYJQ)
* [The President's former press secretary telling us what he can tell us](https://www.youtube.com/watch?v=D7pymdCU5NQ)
