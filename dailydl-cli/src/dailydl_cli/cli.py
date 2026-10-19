"""Human-friendly interactive downloads and script-friendly batch commands."""

import argparse
import json
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table

from . import __version__
from .model import canonical_url, quality_value, safe_name, subtitle_languages
from .runner import OperationError, run_operation

console = Console(stderr=True)


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def retries_value(value):
    number = int(value)
    if not 0 <= number <= 10:
        raise argparse.ArgumentTypeError("must be between 0 and 10")
    return number


def parser():
    result = argparse.ArgumentParser(
        description="DailyDL — reliable, Dailymotion-only video downloads."
    )
    result.add_argument("urls", nargs="*", help="Dailymotion URLs or video IDs")
    result.add_argument(
        "-q", "--quality", default="best", help="best, worst, interactive, or e.g. 720"
    )
    result.add_argument("-o", "--output", type=Path, default=Path("downloads"))
    mode = result.add_mutually_exclusive_group()
    mode.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="list available qualities without downloading",
    )
    mode.add_argument(
        "-j",
        "--json-only",
        action="store_true",
        help="print metadata as JSON (one object per URL)",
    )
    result.add_argument(
        "-s",
        "--subtitles",
        nargs="?",
        const="all",
        default="",
        help="subtitle languages separated by commas; omit value for all available tracks",
    )
    result.add_argument(
        "--no-metadata",
        action="store_true",
        help="do not save metadata.json with the video",
    )
    result.add_argument(
        "--timeout",
        type=positive,
        default=600,
        help="total deadline per operation, in seconds",
    )
    result.add_argument("--retries", type=retries_value, default=2)
    result.add_argument(
        "--doctor", action="store_true", help="check Python, yt-dlp, FFmpeg and ffprobe"
    )
    result.add_argument("--version", action="version", version=f"DailyDL {__version__}")
    return result


def show_video(video):
    console.print(f"\n{video['title']}", style="bold", markup=False)
    console.print(
        f"ID: {video['id']} · {video['duration']:g}s · {video['channel']}", markup=False
    )
    table = Table("Quality", "Available subtitles", header_style="cyan")
    table.add_row(
        ", ".join(f"{q}p" for q in video["qualities"]),
        ", ".join(s["language"] for s in video["subtitles"]) or "None",
    )
    console.print(table)


def process(url, args):
    url = canonical_url(url)
    quality = args.quality
    base = {"url": url, "retries": args.retries}
    if args.list or args.json_only or quality == "interactive":
        result = run_operation({**base, "action": "extract"}, timeout=args.timeout)
        video = result["video"]
        if args.json_only:
            print(json.dumps(video, ensure_ascii=False))
            return
        show_video(video)
        if args.list:
            return
        choices = [str(q) for q in video["qualities"]] + ["best", "worst"]
        quality = Prompt.ask(
            "Quality", choices=choices, default="best", console=console
        )
    quality = quality_value(quality)
    languages = subtitle_languages(args.subtitles.split(",") if args.subtitles else [])
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise OperationError(
            "FFmpeg and ffprobe are required. Run dailydl --doctor for details."
        )
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".dailydl-", dir=output) as temporary:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TextColumn("{task.percentage:>3.0f}%"),
            console=console,
            disable=not console.is_terminal,
        ) as progress:
            task = progress.add_task("Extracting", total=100)

            def update(event):
                progress.update(
                    task,
                    description=event.get("stage", "Working").capitalize(),
                    completed=event.get("percent") or 0,
                )

            result = run_operation(
                {
                    **base,
                    "action": "download",
                    "quality": quality,
                    "subtitles": languages,
                    "metadata": not args.no_metadata,
                    "output": temporary,
                },
                timeout=args.timeout,
                on_progress=update,
            )
            progress.update(task, completed=100, description="Complete")
        video = result["video"]
        name = f"{safe_name(video['title'])} [{video['id']}] {video['selected_quality']}p-{uuid.uuid4().hex[:8]}"
        destination = output / name
        # Atomic rename within the same filesystem; never publish partial output.
        Path(temporary).rename(destination)
    console.print(
        f"Saved {video['selected_quality']}p: {destination}",
        style="green",
        markup=False,
    )
    for warning in result.get("warnings", []):
        console.print(warning, style="yellow", markup=False)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    command = parser()
    args = command.parse_args(argv)
    if args.doctor:
        from yt_dlp.version import __version__ as engine_version

        console.print(
            f"DailyDL {__version__} · Python {sys.version.split()[0]} · yt-dlp {engine_version}"
        )
        for binary in ("ffmpeg", "ffprobe"):
            console.print(
                f"{binary}: {shutil.which(binary) or 'MISSING'}", markup=False
            )
        return 0 if all(shutil.which(binary) for binary in ("ffmpeg", "ffprobe")) else 1
    try:
        if args.quality != "interactive":
            quality_value(args.quality)
        subtitle_languages(args.subtitles.split(",") if args.subtitles else [])
    except ValueError as error:
        command.error(str(error))
    if args.quality == "interactive" and not sys.stdin.isatty():
        command.error("interactive quality selection requires a terminal")
    if not args.urls:
        if not sys.stdin.isatty():
            command.error(
                "provide at least one URL when using a non-interactive terminal"
            )
        console.print(
            "DailyDL · paste a Dailymotion URL, or q to quit", style="bold cyan"
        )
        while True:
            try:
                url = Prompt.ask("Video URL", console=console).strip()
                if url.lower() in {"q", "quit", "exit"}:
                    return 0
                if url:
                    args.quality = "interactive"
                    process(url, args)
            except (KeyboardInterrupt, EOFError):
                console.print("\nCancelled.")
                return 130
            except (ValueError, OSError, OperationError) as error:
                console.print(str(error), style="red", markup=False)
    failed = False
    for url in args.urls:
        try:
            process(url, args)
        except KeyboardInterrupt:
            console.print("\nCancelled. Partial files removed.")
            return 130
        except (ValueError, OSError, OperationError) as error:
            failed = True
            if args.json_only:
                print(
                    json.dumps({"input": url, "error": str(error)}, ensure_ascii=False)
                )
            else:
                console.print(str(error), style="red", markup=False)
    return 1 if failed else 0
