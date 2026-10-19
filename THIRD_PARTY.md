# Third-party components

DailyDL CLI is an application built on existing open-source tools. The extractor is not an original DailyDL implementation.

| Component | Role | Upstream |
| --- | --- | --- |
| yt-dlp | Dailymotion extraction, stream selection, HLS and subtitles | https://github.com/yt-dlp/yt-dlp |
| curl-cffi | Browser-compatible HTTP requests used by yt-dlp | https://github.com/lexiforest/curl_cffi |
| Rich | Terminal formatting and progress | https://github.com/Textualize/rich |
| FFmpeg / ffprobe | Media processing and inspection; installed separately | https://ffmpeg.org/ |

Dependencies are installed from their packages and retain their upstream licenses and notices. The MIT license in this repository applies to DailyDL application code, not to every dependency. FFmpeg licensing depends on the particular build. No FFmpeg binary, dependency source tree, downloaded video or credential is included in this repository.
