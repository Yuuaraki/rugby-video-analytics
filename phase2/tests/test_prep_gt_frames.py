import io
import json
import runpy
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import numpy as np


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prep_gt_frames.py"


class PrepGtFramesTests(unittest.TestCase):
    def write_labels(self, directory, clip, frames):
        directory.mkdir(parents=True)
        row = np.zeros(57)
        row[1:5] = [0.5, 0.5, 0.25, 0.5]
        for frame in frames:
            np.savetxt(directory / f"{clip}_{frame}.txt", [row])

    def run_script(self, home, options):
        frame = np.broadcast_to(np.zeros(3, dtype=np.uint8), (2160, 3840, 3))
        with patch("pathlib.Path.home", return_value=home), \
                patch.dict("os.environ", {"HOME": str(home)}), \
                patch("sys.argv", [str(SCRIPT), *options]), \
                patch("cv2.VideoCapture") as capture, \
                patch("cv2.imwrite", return_value=True) as write, \
                redirect_stdout(io.StringIO()):
            capture.return_value.read.return_value = (True, frame)
            settings = runpy.run_path(str(SCRIPT), run_name="__main__")
        return settings, capture, write

    def assert_export(self, settings, capture, write, clip, video, labels, out, frames, end):
        self.assertEqual(settings["CLIP"], clip)
        self.assertEqual(settings["VIDEO"], video)
        self.assertEqual(settings["LABEL_DIR"], labels)
        self.assertEqual(settings["OUT_DIR"], out)
        capture.assert_called_once_with(str(video))
        self.assertEqual(capture.return_value.read.call_count, end)
        capture.return_value.release.assert_called_once()
        self.assertEqual(write.call_count, len(frames))
        self.assertEqual(
            [call.args[0] for call in write.call_args_list],
            [str(out / f"{frame:06d}.jpg") for frame in frames],
        )
        for call in write.call_args_list:
            self.assertEqual(call.args[1].shape, (1380, 1260, 3))
        meta = json.loads((out / "crop_meta.json").read_text())
        self.assertEqual(meta["clip"], clip)
        self.assertEqual(meta["frames"], frames)
        self.assertEqual(meta["crop_origin"], [1290, 390])
        self.assertEqual(meta["crop_size"], [1260, 1380])

    def test_default_settings_preserve_p9201256_window(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            repo = home / "rugby-video-analytics"
            labels = repo / "runs/pose/runs/pose/20260920_full/labels"
            video = repo / "data/raw/20260920/P9201256.MOV"
            out = home / "data/phase2_gt/frames_P9201256"
            frames = list(range(3222, 3417, 2))
            self.write_labels(labels, "P9201256", frames)
            settings, capture, write = self.run_script(home, [])
            self.assertEqual(
                (settings["F_START"], settings["F_END"], settings["F_STEP"]),
                (3222, 3416, 2),
            )
            self.assert_export(
                settings, capture, write, "P9201256", video, labels, out, frames, 3416,
            )

    def test_all_cli_overrides_and_home_expansion(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            labels, video, out = home / "labels", home / "custom.MOV", home / "out"
            self.write_labels(labels, "CUSTOM", [2, 4])
            settings, capture, write = self.run_script(home, [
                "--clip", "CUSTOM", "--video", "~/custom.MOV",
                "--labels-dir", "~/labels", "--out-dir", "~/out",
                "--start", "2", "--end", "5", "--step", "2",
            ])
            self.assertEqual(
                (settings["F_START"], settings["F_END"], settings["F_STEP"]),
                (2, 5, 2),
            )
            self.assert_export(
                settings, capture, write, "CUSTOM", video, labels, out, [2, 4], 5,
            )

    def test_invalid_frame_arguments_fail_before_export(self):
        for options in (
            ["--start", "0"], ["--start", "5", "--end", "4"],
            ["--step", "0"], ["--step", "-1"],
        ):
            with self.subTest(options=options), \
                    tempfile.TemporaryDirectory() as directory, \
                    redirect_stderr(io.StringIO()):
                home = Path(directory)
                with self.assertRaises(SystemExit) as error:
                    self.run_script(home, options)
                self.assertEqual(error.exception.code, 2)
                self.assertFalse((home / "data/phase2_gt/frames_P9201256").exists())


if __name__ == "__main__":
    unittest.main()
