from moviepy.editor import VideoFileClip
import os


template = """<?xml version="1.0" encoding="UTF-8"?>
<xmeml version="4">
  <project>
    <name>{project_name}</name>
    <children>
      <sequence id="sequence-1">
        <name>{project_name}</name>
        <duration>{track_duration}</duration>
        <rate>
          <timebase>{fps}</timebase>
          <ntsc>FALSE</ntsc>
        </rate>
        <media>
          <video>
            <track>
                {clips}
            </track>
            <format>
              <samplecharacteristics>
                <width>{width}</width>
                <height>{height}</height>
                <pixelaspectratio>square</pixelaspectratio>
              </samplecharacteristics>
            </format>
          </video>
          <audio>
            <track>
                {audio_clips}
            </track>
          </audio>
        </media>
      </sequence>
    </children>
  </project>
</xmeml>
"""

file_template = """
<file id="{file_id}">
  <pathurl>file://{full_path}</pathurl>
  <name>{base_path}</name>
  <rate>
    <timebase>{fps}</timebase>
    <ntsc>FALSE</ntsc>
  </rate>
  <duration>{total_duration}</duration>
  <timecode>
    <rate>
      <timebase>{fps}</timebase>
      <ntsc>FALSE</ntsc>
    </rate>
    <string>00:00:00:00</string>
    <frame>0</frame>
    <displayformat>NDF</displayformat>
  </timecode>
  <media>
    <video />
    <audio />
  </media>
</file>
"""

clip_item_template = """
<clipitem frameBlend="FALSE" id="{clip_item_id}">
{file_meta}
<name>{shot_name}</name>
<rate>
  <timebase>{fps}</timebase>
  <ntsc>FALSE</ntsc>
</rate>
<duration>{clip_duration}</duration>
<start>{start}</start>
<end>{end}</end>
<in>{clip_in}</in>
<out>{clip_out}</out>
</clipitem>
"""

audio_item_template = """
<clipitem id="{clip_item_id}">
{file_meta}
<name>{shot_name}</name>
<rate>
  <timebase>{fps}</timebase>
  <ntsc>FALSE</ntsc>
</rate>
<duration>{clip_duration}</duration>
<start>{start}</start>
<end>{end}</end>
<in>{clip_in}</in>
<out>{clip_out}</out>
</clipitem>

"""



def get_clip_meta(segments):
    v_id = 1

    meta = {}

    for s in segments:
        filename = s["file"]

        if filename not in meta:
            _v = VideoFileClip(filename)
            meta[filename] = {
                "duration": _v.duration,
                "fps": _v.fps,
                "v_id": f"file-{v_id}",
                "width": _v.w,
                "height": _v.h,
            }
            v_id += 1

    return meta


def secs_to_frames(seconds, fps):
    return int(seconds * fps)


def compose(segments, outname):
    meta = get_clip_meta(segments)

    start = 0
    track_duration = 0

    clip_items = []
    audio_clip_items = []
    files = {}

    clip_id = 1

    total_clips = len(segments)

    for s in segments:
        filename = s["file"]
        clip_in = s["start"]
        clip_out = s["end"]
        clip_duration = s["end"] - s["start"]
        end = start + clip_duration
        track_duration += clip_duration

        total_clip_duration = meta[filename]["duration"]
        width = meta[filename]['width']
        height = meta[filename]['height']
        fps = meta[filename]["fps"]
        file_id = meta[filename]["v_id"]

        if file_id not in files:
            files[file_id] = file_template.format(
                file_id=file_id,
                full_path=filename,
                base_path=os.path.basename(filename),
                fps=fps,
                total_duration=secs_to_frames(total_clip_duration, fps),
            )
            file_clip = files[file_id]
        else:
            file_clip = f'<file id="{file_id}" />'.format(file_id)

        clip = clip_item_template.format(
            clip_item_id=f"clipitem-{clip_id}",
            file_meta=file_clip,
            shot_name=os.path.basename(filename),
            fps=fps,
            clip_duration=secs_to_frames(clip_duration, fps),
            start=secs_to_frames(start, fps),
            end=secs_to_frames(end, fps),
            clip_in=secs_to_frames(clip_in, fps),
            clip_out=secs_to_frames(clip_out, fps),
        )


        audio_clip = audio_item_template.format(
            clip_item_id=f"clipitem-{clip_id+total_clips}",
            file_meta=files[file_id],
            shot_name=os.path.basename(filename),
            fps=fps,
            clip_duration=secs_to_frames(clip_duration, fps),
            start=secs_to_frames(start, fps),
            end=secs_to_frames(end, fps),
            clip_in=secs_to_frames(clip_in, fps),
            clip_out=secs_to_frames(clip_out, fps),
        )

        clip_items.append(clip)
        audio_clip_items.append(audio_clip)

        clip_id += 1

        start = end

    output = template.format(
        fps=fps,
        width=width,
        height=height,
        project_name=os.path.splitext(os.path.basename(outname))[0],
        clips="\n".join(clip_items),
        audio_clips="\n".join(audio_clip_items),
        track_duration=secs_to_frames(track_duration, fps),
    )

    # output = minidom.parseString(output)
    with open(outname, "w") as outfile:
        outfile.write(output)
