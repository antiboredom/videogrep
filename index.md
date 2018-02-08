Videogrep
=========

(By [Sam Lavigne](http://lav.io))

Videogrep is a command line tool that searches through dialog in video files (using .srt or .vtt subtitle tracks, or pocketsphinx transcriptions) and makes supercuts based on what it finds.

Videogrep also has an experimental graphic interface (Mac only). Download it here: [http://saaaam.s3.amazonaws.com/VideoGrep.app.zip](http://saaaam.s3.amazonaws.com/VideoGrep.app.zip)

## Requirements

Install with pip
```
pip install videogrep
```
Install [ffmpeg](http://ffmpeg.org/) with Ogg/Vorbis support. If you're on a mac with homebrew you can install ffmpeg with:
```
brew install ffmpeg --with-libvpx --with-libvorbis
```

(OPTIONAL) Install pocketsphinx for word-level transcriptions. On a mac:
```
brew tap watsonbox/cmu-sphinx
brew install --HEAD watsonbox/cmu-sphinx/cmu-sphinxbase
brew install --HEAD watsonbox/cmu-sphinx/cmu-sphinxtrain # optional
brew install --HEAD watsonbox/cmu-sphinx/cmu-pocketsphinx
```

## How to use it
The most basic use:
```
videogrep --input path/to/video_or_folder --search 'search phrase'
```
You can put any regular expression in the search phrase.

If you install Pattern.en (`pip install pattern`), you can also search for part-of-speech tags. See the [Pattern-Search documentation](http://www.clips.ua.ac.be/pages/pattern-search) for some details about how this works, and the [Penn Tree bank tag set](http://www.clips.ua.ac.be/pages/mbsp-tags) for a list of usuable part-of-speech tags. For example the following will search for every line of dialog that contains an adjective (JJ) followed by a singular noun (NN):
```
videogrep --input path/to/video_or_folder --search 'JJ NN' --search-type pos
```
With Pattern you can also do a [hypernym](https://en.wikipedia.org/wiki/Hypernym) search - which essentially searches for words that fit into a specific category. The following, for example, will search for any line of dialog that references a liquid (like water, coffee, beer, etc.):
```
videogrep --input path/to/video_or_folder --search 'liquid' --search-type hyper
```

**NOTE: videogrep requires the subtitle track and the video file to have the exact same name, up to the extension.** For example, my_movie.mp4 and my_movie.srt will work, my_movie.mp4 and my_movie_subtitle.srt will not work.

### Options

videogrep can take a number of options:

#### --input / -i
Video or subtitle file, or folder containing multiple files

#### --output / -o
Name of the file to generate. By default this is "supercut.mp4"

#### --search / -s
Search term

#### --search-type / -st
Type of search you want to perform. There are three options:
* re: [regular expression](http://www.pyregex.com/) (this is the default).
* pos: part of speech search (uses [pattern.search](http://www.clips.ua.ac.be/pages/pattern-search)). For example 'JJ NN' would return all lines of dialog that contain an adjective followed by a noun.
* hyper: hypernym search. For example 'body parts' grabs all lines of dialog that reference a body part
* word: extract individual words - for multiple words use the '|' symbol (requires pocketsphinx).
* franken: create a "frankenstein" sentence (requires pocketsphinx)
* fragment: multiple words with allowed wildcards like 'blue \*' (requires pocketsphinx)

#### --max-clips / -m
Maximum number of clips to use for the supercut

#### --demo / -d
Show the search results without making the supercut

#### --randomize / -r
Randomize the order of the clips

#### --padding / -p
Padding in milliseconds to add to the start and end of each clip

#### --use-vtt / -vtt
Use .vtt files rather than .srt subtitle files. If this is enabled, and you grabbed the .vtt from YouTube's auto-captioning service you can do word-level searches.

#### --transcribe / -tr
Transcribe the video using audiogrep/pocketsphinx. You must install pocketsphinx first!

#### --use-transcript / -t
Use the pocketsphinx transcript rather than a subtitle file for searching. If this is enabled you can do
word-level searches.

## Samples
* [All the instances of the phrase "time" in the movie "In Time"](https://www.youtube.com/watch?v=PQMzOUeprlk)
* [All the one to two second silences in "Total Recall"](https://www.youtube.com/watch?v=qEtEbXVbYJQ)
* [The President's former press secretary telling us what he can tell us](https://www.youtube.com/watch?v=D7pymdCU5NQ)

### Use it as a module

```
from videogrep import videogrep

videogrep('path/to/your/files','output_file_name.mp4', 'search_term', 'search_type')
```
The videogrep module accepts the same parameters as the command line script. To see the usage check out the source.
