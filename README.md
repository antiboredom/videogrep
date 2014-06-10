Videogrep
=========

Videogrep searches through dialog in video files (using .srt subtitle tracks) and makes supercuts based on what it finds.

##Requirements
Clone this repository, and then install [pattern](http://www.clips.ua.ac.be/pages/pattern-search) and [moviepy](https://github.com/Zulko/moviepy).
```
pip install pattern
pip install moviepy
```

If you're on a mac with homebrew you can install ffmpeg with:
```
brew install ffmpeg
```


##How to use it
The most basic use:
```
python videogrep.py --input path/to/video_or_folder --search 'search phrase'
```

###Options

videogrep can take a number of options:

####--input / -i
Video or subtitle file, or folder containing multiple files

####--search / -s
Search term

####--search-type / -st
Type of search you want to perform. There are three options:
* re: regular expression (which is the default)
* pos: part of speech search (uses pattern.search). For example: "JJ NN"
* hyper: hypernym search. For example: 'body parts'

####--max-clips / -m 
Maximum number of clips to use for the supercut

####--output / -o
Name of the file to generate. By default this is "supercut.mp4"

####--test / -t
Show the search results without making the supercut

####--randomize / -r
Randomize the order of the clips

####--padding / -p
Padding in milliseconds to add to the start and end of each clip

##Samples
* [All the instances of the phrase "time" in the movie "In Time"](https://www.youtube.com/watch?v=PQMzOUeprlk)
* [All the one to two second silences in "Total Recall"](https://www.youtube.com/watch?v=qEtEbXVbYJQ)
* [The President's former press secretary tellings us what he can tell us](https://www.youtube.com/watch?v=D7pymdCU5NQ)
