# DailyDL CLI

**A focused Dailymotion downloader for the terminal.** Interactive quality selection, batch downloads, real deadlines, subtitles, and clean JSON output — without a browser or a web server.

Built with Python, [yt-dlp](https://github.com/yt-dlp/yt-dlp), [Rich](https://github.com/Textualize/rich), and [FFmpeg](https://ffmpeg.org/). DailyDL provides the application workflow and process supervision; media extraction is powered by yt-dlp.

## Features

- Interactive mode and multiple URLs in one command.
- Best, worst, or a preferred resolution; portrait videos use their shorter dimension.
- Manual and available automatic subtitle tracks, with explicit language selection.
- Metadata JSON without expiring media URLs or credentials.
- A real wall-clock timeout that stops the worker and its FFmpeg children.
- Isolated temporary downloads and unique final directories; existing videos are never overwritten.
- Machine-readable JSON Lines output and meaningful exit codes.

## Requirements

- CPython 3.10 or newer. Verified locally on Windows with Python 3.13.
- FFmpeg **and ffprobe** available on `PATH` for downloading. Extraction works without them.
- Internet access to Dailymotion and its media CDN.

Install FFmpeg using your platform's package manager or the [official download page](https://ffmpeg.org/download.html). Check `ffmpeg -version` and `ffprobe -version` before downloading.

## Install

Run these commands inside this repository:

```sh
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS / Linux:

```sh
source .venv/bin/activate
```

Then install and check your environment:

```sh
python -m pip install -e .
dailydl --doctor
```

You can also run `python -m dailydl_cli` instead of `dailydl`. This repository is completely standalone; DailyDL Web is not required.

For the dependency versions used during release verification:

```sh
python -m pip install -r requirements.lock
python -m pip install -e .
```

## Usage

```sh
# Interactive prompt
dailydl

# Download the best available quality
dailydl https://www.dailymotion.com/video/xalfjry

# Choose a quality, output folder, and total deadline
dailydl xalfjry -q 720 -o downloads --timeout 600

# Inspect the available resolutions and subtitle languages
dailydl xalfjry --list

# Download Arabic subtitles when that exact track is available
dailydl xalfjry --subtitles ar-auto

# Include all available subtitle tracks
dailydl xalfjry --subtitles

# Process multiple videos; one failure does not stop the remaining inputs
dailydl URL1 URL2 -q worst --no-metadata

# JSON Lines to stdout; human messages go to stderr
dailydl xalfjry --json-only > video.json
```

When an exact resolution is unavailable, DailyDL chooses the highest resolution at or below the request. If every available resolution is larger, it chooses the smallest. The saved path reports the actual selected quality.

Each successful download gets a unique directory:

```text
downloads/
  Video title [video-id] 720p-a1b2c3d4/
    video.mp4
    metadata.json
    video.en.vtt       # only when requested and available
```

Metadata is saved by default; use `--no-metadata` to disable it. Subtitles are off by default. Live streams, playlists, private/password-protected videos and DRM bypass are outside this application's scope. Videos may be unavailable because of region restrictions or provider changes.

Exit codes: `0` success, `1` one or more operations failed, `2` invalid arguments, `130` user cancellation. Press Ctrl+C to cancel and remove the partial download. `--timeout` applies to each extraction/download operation; interactive selection runs extraction and download as separate operations.

## Development

```sh
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m ruff check src tests
python -m build
```

The deterministic tests use fixtures and controlled subprocesses; they do not require live Dailymotion access. GitHub Actions runs these checks on Windows and Ubuntu with Python 3.10 and 3.13. A CI workflow is included; a successful local test run is not a claim that remote CI has already run.

```text
src/dailydl_cli/
  cli.py       # arguments, prompts, progress, output publication
  model.py     # URL, quality and subtitle validation
  engine.py    # Dailymotion-only yt-dlp adapter
  runner.py    # deadline, cancellation and process-tree cleanup
  worker.py    # private JSON-lines worker protocol
tests/         # regression and process-supervision tests
```

If Dailymotion changes its extraction requirements, update the maintained engine first, then rerun tests and a live download:

```sh
python -m pip install --upgrade "yt-dlp[curl-cffi]"
```

`requirements.lock` records the tested environment. Refresh it deliberately after validating updates. Do not commit `.venv`, downloaded media, credentials or generated package files; `.gitignore` already excludes them.

## License and attribution

Application code is MIT licensed. Dependencies retain their own licenses; see [THIRD_PARTY.md](THIRD_PARTY.md). This project is not affiliated with Dailymotion. Download only content you are authorized to save.
