from moviepy.editor import VideoFileClip
from functools import lru_cache
import os


@lru_cache(maxsize=None)
def get_clip(filename):
    return VideoFileClip(filename)


def frames(seconds, fps):
    return int(seconds * fps)


class Clip:
    def __init__(self, filename, clip_id, start, end, clip_in, clip_out):
        self.clip = get_clip(filename)
        self.full_path = os.path.abspath(filename)
        self.base_path = os.path.basename(filename)
        self.shot_name = os.path.basename(filename)
        self.clip_id = f"{self.shot_name}-{clip_id}"
        self.audio_clip_id = f"{self.clip_id}-audio"
        self.fps = self.clip.fps
        self.duration = self.clip.duration
        self.width = self.clip.w
        self.height = self.clip.h
        self.start = self.frames(start)
        self.end = self.frames(end)
        self.clip_in = self.frames(clip_in)
        self.clip_out = self.frames(clip_out)
        self.file_id = self.shot_name
        self.audio_channels = 2

    def frames(self, secs):
        return int(secs * self.fps)

    def render(self, include_file=False):
        file_meta = f'<file id="{self.file_id}" />'

        if include_file:
            file_meta = self.render_file()

        return f"""
          <clipitem id="{self.clip_id}">
            <name>{self.shot_name}</name>
            <duration>{self.duration}</duration>
            <rate>
              <timebase>{self.fps}</timebase>
              <ntsc>FALSE</ntsc>
            </rate>
            <start>{self.start}</start>
            <end>{self.end}</end>
            <enabled>TRUE</enabled>
            <in>{self.clip_in}</in>
            <out>{self.clip_out}</out>
            {file_meta}
            <compositemode>normal</compositemode>
            <link>
              <linkclipref>{self.clip_id}</linkclipref>
            </link>
            <link>
              <linkclipref>{self.audio_clip_id}</linkclipref>
            </link>
            <comments />
          </clipitem>"""

    def render_audio(self):
        return f"""
          <clipitem id="{self.audio_clip_id}">
            <name>{self.shot_name}</name>
            <duration>{self.duration}</duration>
            <rate>
              <timebase>{self.fps}</timebase>
              <ntsc>FALSE</ntsc>
            </rate>
            <start>{self.start}</start>
            <end>{self.end}</end>
            <enabled>TRUE</enabled>
            <in>{self.clip_in}</in>
            <out>{self.clip_out}</out>
            <file id="{self.file_id}" />
            <sourcetrack>
              <mediatype>audio</mediatype>
              <trackindex>1</trackindex>
            </sourcetrack>
            <link>
              <linkclipref>{self.clip_id}</linkclipref>
            </link>
            <link>
              <linkclipref>{self.audio_clip_id}</linkclipref>
            </link>
            <comments />
          </clipitem>"""

    def render_file(self):
        return f"""
            <file id="{self.file_id}">
              <pathurl>file://{self.full_path}</pathurl>
              <name>{self.base_path}</name>
              <rate>
                <timebase>{self.fps}</timebase>
                <ntsc>FALSE</ntsc>
              </rate>
              <duration>{self.duration}</duration>
              <timecode>
                <rate>
                  <timebase>{self.fps}</timebase>
                  <ntsc>FALSE</ntsc>
                </rate>
                <string>00:00:00:00</string>
                <displayformat>NDF</displayformat>
              </timecode>
              <media>
                <video>
                  <duration>{self.duration}</duration>
                  <samplecharacteristics>
                    <width>{self.width}</width>
                    <height>{self.height}</height>
                  </samplecharacteristics>
                </video>
                <audio>
                  <channelcount>{self.audio_channels}</channelcount>
                </audio>
              </media>
            </file>"""


class Sequence:
    def __init__(self, segments, project_name):
        clips = []

        start = 0
        track_duration = 0
        for index, s in enumerate(segments):
            clip_duration = s["end"] - s["start"]
            end = start + clip_duration
            track_duration += clip_duration

            clip = Clip(
                filename=s["file"],
                clip_id=index,
                clip_in=s["start"],
                clip_out=s["end"],
                start=start,
                end=end,
            )
            clips.append(clip)
            start = end

        self.clips = clips
        self.track_duration = clips[0].frames(track_duration)
        self.project_name = project_name
        self.fps = clips[0].fps
        self.width = clips[0].width
        self.height = clips[0].height

    def render_video(self):
        files = []
        rendered = []
        for c in self.clips:
            if c.full_path in files:
                need_file = False
            else:
                files.append(c.full_path)
                need_file = True

            rendered.append(c.render(include_file=need_file))

        return "\n".join(rendered)

    def render_audio(self):
        return "\n".join([c.render_audio() for c in self.clips])

    def render(self):
        return f"""<?xml version="1.0" encoding="utf-8"?>
            <!DOCTYPE xmeml>
            <xmeml version="5">
              <sequence>
                <name>{self.project_name}</name>
                <duration>{self.track_duration}</duration>
                <rate>
                  <timebase>{self.fps}</timebase>
                  <ntsc>FALSE</ntsc>
                </rate>
                <in>-1</in>
                <out>-1</out>
                <timecode>
                  <string>01:00:00:00</string>
                  <frame>108000</frame>
                  <displayformat>NDF</displayformat>
                  <rate>
                    <timebase>{self.fps}</timebase>
                    <ntsc>TRUE</ntsc>
                  </rate>
                </timecode>
                <media>
                  <video>
                    <track>
                        {self.render_video()}
                    </track>
                    <format>
                      <samplecharacteristics>
                        <width>{self.width}</width>
                        <height>{self.height}</height>
                        <pixelaspectratio>square</pixelaspectratio>
                        <rate>
                          <timebase>{self.fps}</timebase>
                          <ntsc>FALSE</ntsc>
                        </rate>
                      </samplecharacteristics>
                    </format>
                  </video>
                  <audio>
                    <track>
                        {self.render_audio()}
                    </track>
                  </audio>
                </media>
              </sequence>
            </xmeml>"""


def compose(segments, outname):
    s = Sequence(segments, outname)

    # output = minidom.parseString(output)
    with open(outname, "w") as outfile:
        outfile.write(s.render())
