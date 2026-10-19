import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dailydl_cli import cli


VIDEO = {
    "id": "xalfjry",
    "title": "Title",
    "duration": 10,
    "channel": "Channel",
    "qualities": [360],
    "subtitles": [],
    "selected_quality": 360,
}


class CliTests(unittest.TestCase):
    def test_json_output_is_parseable(self):
        stream = io.StringIO()
        with (
            patch.object(cli, "run_operation", return_value={"video": VIDEO}),
            contextlib.redirect_stdout(stream),
        ):
            self.assertEqual(cli.main(["xalfjry", "--json-only"]), 0)
        self.assertEqual(json.loads(stream.getvalue())["id"], "xalfjry")

    def test_batch_returns_failure_and_continues(self):
        stream = io.StringIO()
        with (
            patch.object(cli, "run_operation", return_value={"video": VIDEO}),
            contextlib.redirect_stdout(stream),
        ):
            self.assertEqual(
                cli.main(["https://evil.example/x", "xalfjry", "--json-only"]), 1
            )
        lines = [json.loads(line) for line in stream.getvalue().splitlines()]
        self.assertIn("error", lines[0])
        self.assertEqual(lines[1]["id"], "xalfjry")

    def test_completed_downloads_get_unique_directories(self):
        def operation(request, **kwargs):
            Path(request["output"], "video.mp4").write_bytes(b"test-video")
            return {"video": VIDEO, "files": ["video.mp4"]}

        with (
            tempfile.TemporaryDirectory() as root,
            patch.object(cli, "run_operation", side_effect=operation),
            patch.object(cli.shutil, "which", return_value="ffmpeg"),
        ):
            args = cli.parser().parse_args(["xalfjry", "-o", root])
            cli.process("xalfjry", args)
            cli.process("xalfjry", args)
            directories = list(Path(root).iterdir())
            self.assertEqual(len(directories), 2)
            self.assertTrue(all((path / "video.mp4").is_file() for path in directories))
            self.assertFalse(
                any(path.name.startswith(".dailydl-") for path in directories)
            )

    def test_failed_download_removes_partial_files(self):
        def operation(request, **kwargs):
            Path(request["output"], "video.mp4.part").write_bytes(b"partial")
            raise cli.OperationError("failure")

        with (
            tempfile.TemporaryDirectory() as root,
            patch.object(cli, "run_operation", side_effect=operation),
            patch.object(cli.shutil, "which", return_value="ffmpeg"),
        ):
            args = cli.parser().parse_args(["xalfjry", "-o", root])
            with self.assertRaises(cli.OperationError):
                cli.process("xalfjry", args)
            self.assertEqual(list(Path(root).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
