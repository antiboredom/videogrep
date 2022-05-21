import videogrep
from glob import glob
from subprocess import run


def auto_youtube_supercut(query, max_videos=1):
    """
    Search youtube for a query, download videos with yt-dlp,
    and then makes a supercut with that query
    """

    args = [
        "yt-dlp",  # run yt-dlp
        "https://www.youtube.com/results?search_query=" + query,
        "--write-auto-sub",  # download youtube's auto-generated subtitles
        "-f",  # select the format of the video
        "22",  # 22 is 1280x720 mp4
        "--max-downloads",  # limit the downloads
        str(max_videos),
        "--playlist-end",
        str(max_videos),
        "-o",  # where to save the downloaded videos to
        query + "%(video_autonumber)s.mp4",  # save the video as the query + .mp4
    ]

    run(args)

    # grab the videos we just downloaded
    files = glob(query + "*.mp4")

    # run videogrep
    videogrep.videogrep(files, query, search_type="fragment")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create a supercut of youtube videos based on a search term"
    )

    parser.add_argument("--search", "-s", dest="search", help="search term")

    parser.add_argument(
        "--max",
        "-m",
        dest="max_videos",
        type=int,
        default=1,
        help="maximum number of videos to download",
    )

    args = parser.parse_args()

    auto_youtube_supercut(args.search, args.max_videos)
