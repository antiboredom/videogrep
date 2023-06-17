Videogrep
=========

Videogrep is a command line tool that searches through dialog in video files and makes supercuts based on what it finds. It will recognize `.srt` or `.vtt` subtitle tracks, or transcriptions that can be generated with vosk, pocketsphinx, and other tools.

#### Examples

* [The Meta Experience](https://www.youtube.com/watch?v=nGHbOckpifw)
* [All the instances of the phrase "time" in the movie "In Time"](https://www.youtube.com/watch?v=PQMzOUeprlk)
* [All the one to two second silences in "Total Recall"](https://www.youtube.com/watch?v=qEtEbXVbYJQ)
* [A former press secretary telling us what he can tell us](https://www.youtube.com/watch?v=D7pymdCU5NQ)

#### Tutorial

See my blog for a short [tutorial on videogrep and yt-dlp](https://lav.io/notes/videogrep-tutorial/), and part 2, on [videogrep and natural language processing](https://lav.io/notes/videogrep-and-spacy/).

----

## Installation

Videogrep is compatible with Python versions 3.6 to 3.10.

To install:

```
pip install videogrep
```

If you want to transcribe videos, you also need to install [vosk](https://alphacephei.com/vosk/):

```
pip install vosk
```

Note: the previous version of videogrep supported pocketsphinx for speech-to-text. Vosk seems *much* better so I've added support for it and will likely be phasing out support for pocketsphinx.

## Usage

The most basic use:

```
videogrep --input path/to/video --search 'search phrase'
```

You can put any regular expression in the search phrase.

**NOTE: videogrep requires a matching subtitle track with each video you want to use. The video file and subtitle file need to have the exact same name, up to the extension.** For example, `my_movie.mp4` and `my_movie.srt` will work, and `my_movie.mp4` and `my_movie_subtitle.srt` will *not* work.

Videogrep will search for matching `srt` and `vtt` subtitles, as well as `json` transcript files that can be generated with the `--transcribe` argument.

### Options

#### `--input [filename(s)] / -i [filename(s)]`

Video or videos to use as input. Most video formats should work.


#### `--output [filename] / -o [filename]`

Name of the file to generate. By default this is `supercut.mp4`. Any standard video extension will also work.

Videogrep will also recognize the following extensions for saving files:
  * `.mpv.edl`: generates an edl file playable by [mpv](https://mpv.io/) (useful for previews)
  * `.m3u`: media playlist
  * `.xml`: Final Cut Pro timeline, compatible with Adobe Premiere and Davinci Resolve

```
videogrep --input path/to/video --search 'search phrase' --output coolvid.mp4
```


#### `--search [query] / -s [query]`

Search term, as a regular expression. You can add as many of these as you want. For example:

```
videogrep --input path/to/video --search 'search phrase' --search 'another search' --search 'a third search' --output coolvid.mp4
```


#### `--search-type [type] / -st [type]`

Type of search you want to perform. There are two options:

* `sentence`: (default): Generates clips containing the full sentences of your search query.
* `fragment`: Generates clips containing the exact word or phrase of your search query.

Both options take regular expressions. You may only use the `fragment` search if your transcript has word-level timestamps, which will be the case for youtube `.vtt` files, or if you generated a transcript using Videogrep itself.

```
videogrep --input path/to/video --search 'experience' --search-type fragment
```

#### `--max-clips [num] / -m [num]`

Maximum number of clips to use for the supercut.


#### `--demo / -d`

Show the search results without making the supercut.


#### `--randomize / -r`

Randomize the order of the clips.


#### `--padding [seconds] / -p [seconds]`

Padding in seconds to add to the start and end of each clip.

#### `--resyncsubs [seconds] / -rs [seconds]`

Time in seconds to shift the shift the subtitles forwards or backwards.

#### `--transcribe / -tr`

Transcribe the video using [vosk](https://alphacephei.com/vosk/). This will generate a `.json` file in the same folder as the video. By default this uses vosk's small english model.

**NOTE:** Because of some compatibility issues, vosk must be installed separately with `pip install vosk`.

```
videogrep -i vid.mp4 --transcribe
```

#### `--model [modelpath] / -mo [modelpath]`

In combination with the `--transcribe` option, allows you to specify the path to a vosk model folder to use. Vosk models are [available here](https://alphacephei.com/vosk/models) in a variety of languages.

```
videogrep -i vid.mp4 --transcribe --model path/to/model/
```

#### `--export-clips / -ec`

Exports clips as individual files rather than as a supercut.

```
videogrep -i vid.mp4 --search 'whatever' --export-clips
```

#### `--export-vtt / -ev`

Exports the transcript of the supercut as a WebVTT file next to the video.

```
videogrep -i vid.mp4 --search 'whatever' --export-vtt
```

#### `--ngrams [num] / -n [num]`

Shows common words and phrases from the video.

```
videogrep -i vid.mp4 --ngrams 1
```


----


## Use it as a module

```
from videogrep import videogrep

videogrep('path/to/your/files','output_file_name.mp4', 'search_term', 'search_type')
```
The videogrep module accepts the same parameters as the command line script. To see the usage check out the source.

### Example Scripts

Also see the examples folder for:
* [silence extraction](https://github.com/antiboredom/videogrep/blob/master/examples/only_silence.py)
* [automatically creating supercuts](https://github.com/antiboredom/videogrep/blob/master/examples/auto_supercut.py)
* [creating supercuts based on youtube searches](https://github.com/antiboredom/videogrep/blob/master/examples/auto_youtube.py)
* [creating supercuts from specific parts of speech](https://github.com/antiboredom/videogrep/blob/master/examples/parts_of_speech.py)
* [creating supercuts from spacy pattern matching](https://github.com/antiboredom/videogrep/blob/master/examples/pattern_matcher.py)
