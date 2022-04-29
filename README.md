Videogrep
=========

Videogrep is a command line tool that searches through dialog in video files and makes supercuts based on what it finds. It will recognize .srt or .vtt subtitle tracks, or transcriptions that can be generated with vosk, pocketsphinx, and other tools.

## Installation

Videogrep is compatible with Python versions 3.6 to 3.9.

Install this BETA version with pip:

```
pip install git+https://github.com/antiboredom/videogrep@v2beta
```

You can optionally install [ffmpeg](http://ffmpeg.org/) if you'd like to transcribe videos. If you're on a mac with homebrew you install ffmpeg with:

```
brew install ffmpeg
```

## Usage

The most basic use:

```
videogrep --input path/to/video --search 'search phrase'
```

You can put any regular expression in the search phrase.

**NOTE: videogrep requires the subtitle track and the video file to have the exact same name, up to the extension.** For example, my_movie.mp4 and my_movie.srt will work, and my_movie.mp4 and my_movie_subtitle.srt will not work.

### Options

videogrep can take a number of options:


#### --input / -i

Video or subtitle file, or folder containing multiple files


#### --output / -o

Name of the file to generate. By default this is "supercut.mp4"


#### --search / -s

Search term


#### --search-type / -st

Type of search you want to perform. There are two options:

* `sentence` (default): Generates clips containing the full sentences of your search query.
* `fragment`: Generates clips containing the exact word or phrase of your search query.

Both options take regular expressions. You may only use the `fragment` search if your transcript has word-level timestamps, which will be the case for youtube .vtt files, or if you generated a transcript using videogrep itself.

#### --max-clips / -m

Maximum number of clips to use for the supercut


#### --demo / -d

Show the search results without making the supercut


#### --randomize / -r

Randomize the order of the clips


#### --padding / -p

Padding in milliseconds to add to the start and end of each clip

#### --resyncsubs / -rs

Shifts the subtitle timing forwards or backgrounds in milliseconds

#### --transcribe / -tr

Transcribe the video using [vosk](https://alphacephei.com/vosk/). This will generate a `.json` file in the same folder as the video. Only works for English at the moment!

```
videogrep -i vid.mp4 --transcribe
```

#### --export-clips / -ec

Exports clips as individual files rather than as a supercut

```
videogrep -i vid.mp4 --search 'whatever' --export-clips
```

#### --ngrams / -n

Shows common ngrams from the transcript

```
videogrep -i vid.mp4 --ngrams 1
```




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

