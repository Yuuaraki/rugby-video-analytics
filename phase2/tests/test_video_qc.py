import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

import cv2
import numpy as np

from phase2.video_qc import frame_diffs, main, summarize


class VideoQCTests(unittest.TestCase):
    def capture(self, frames):
        cap = Mock()
        cap.isOpened.return_value = True
        cap.read.side_effect = [(True, frame) for frame in frames] + [(False, None)]
        return cap

    def test_signed_subtraction_and_spatial_sampling(self):
        first = np.full((8, 8, 3), 5, dtype=np.uint8)
        second = np.full((8, 8, 3), 255, dtype=np.uint8)
        second[::4, ::4] = 3
        cap = self.capture([first, second])
        with patch("phase2.video_qc.cv2.VideoCapture", return_value=cap):
            n, d = frame_diffs("test.mov")
        self.assertEqual(n, 2)
        np.testing.assert_array_equal(d, [2.0])
        cap.release.assert_called_once()

    def test_frame_limit_preserves_pair_count_without_extra_read(self):
        frames = [np.full((8, 8, 3), i, dtype=np.uint8) for i in range(5)]
        for limit, expected in ((0, 5), (1, 1), (2, 2), (5, 5), (10, 5)):
            with self.subTest(limit=limit):
                cap = self.capture(frames)
                with patch("phase2.video_qc.cv2.VideoCapture", return_value=cap):
                    n, d = frame_diffs("test.mov", max_frames=limit)
                self.assertEqual(n, expected)
                self.assertEqual(len(d), max(0, n - 1))
                if limit and limit <= len(frames):
                    self.assertEqual(cap.read.call_count, limit)
                cap.release.assert_called_once()

    def test_capture_released_on_failure(self):
        cap = self.capture([])
        cap.isOpened.return_value = False
        with patch("phase2.video_qc.cv2.VideoCapture", return_value=cap):
            with self.assertRaisesRegex(OSError, "Cannot open"):
                frame_diffs("missing.mov")
        cap.release.assert_called_once()
        cap = self.capture([np.zeros((8, 8, 3), dtype=np.uint8)])
        with patch("phase2.video_qc.cv2.VideoCapture", return_value=cap):
            with patch("phase2.video_qc.cv2.cvtColor", side_effect=ValueError("conversion failed")):
                with self.assertRaisesRegex(ValueError, "conversion failed"):
                    frame_diffs("test.mov")
        cap.release.assert_called_once()

    def test_known_duplicate_rates_and_frame_numbers(self):
        genuine = np.full(59, 1.0)
        self.assertEqual(summarize(genuine, 0.3, 0)[:5], (0, 0.0, 0, 1.0, 1.0))
        diffs = np.empty(119)
        diffs[::2] = 0.1
        diffs[1::2] = 1.0
        n_dup, rate, n_tail, p90, min_body, frames = summarize(diffs, 0.3, 0)
        self.assertEqual(n_dup, 60)
        self.assertAlmostEqual(rate, 100 * 60 / 119)
        self.assertEqual(p90, 1.0)
        self.assertEqual(n_tail, 0)
        self.assertEqual(min_body, 0.1)
        np.testing.assert_array_equal(frames, np.arange(2, 121, 2))
        self.assertIsInstance(n_dup, int)

    def test_known_answer_encoded_videos(self):
        rng = np.random.default_rng(11)
        gray_frames = rng.integers(80, 121, size=(60, 32, 48), dtype=np.uint8)
        frames = np.repeat(gray_frames[..., None], 3, axis=-1)
        with tempfile.TemporaryDirectory(prefix="video-qc-") as directory:
            for repeated in (False, True):
                with self.subTest(repeated=repeated):
                    path = Path(directory) / ("duplicated.avi" if repeated else "baseline.avi")
                    writer = cv2.VideoWriter(
                        str(path), cv2.VideoWriter_fourcc(*"FFV1"),
                        60000 / 1001 if repeated else 30000 / 1001, (48, 32),
                    )
                    try:
                        self.assertTrue(writer.isOpened(), "FFV1 writer could not be opened")
                        for frame in frames:
                            writer.write(frame)
                            if repeated:
                                writer.write(frame)
                    finally:
                        writer.release()
                    n, d = frame_diffs(path)
                    n_dup, rate, n_tail, _, _, candidates = summarize(d, 0.3, 0)
                    self.assertEqual(n, 120 if repeated else 60)
                    self.assertEqual(len(d), n - 1)
                    self.assertEqual(n_dup, 60 if repeated else 0)
                    self.assertEqual(n_tail, 0)
                    self.assertAlmostEqual(rate, 100 * 60 / 119 if repeated else 0)
                    np.testing.assert_array_equal(
                        candidates, np.arange(2, 121, 2) if repeated else np.array([], dtype=int),
                    )

    def test_threshold_is_strict_and_scale_invariant(self):
        d = np.array([0.1, 0.3] + [1.0] * 10)
        expected = summarize(d, 0.3, 0)
        self.assertEqual(expected[0], 1)
        for scale in (0.01, 100):
            result = summarize(d * scale, 0.3, 0)
            self.assertEqual(result[:2], expected[:2])
            np.testing.assert_array_equal(result[5], expected[5])

    def test_tail_uses_body_threshold_without_affecting_body_statistics(self):
        body = np.array([0.1] + [1.0] * 9)
        for tail_d, expected_tail in (
            (np.zeros(100), 100),
            (np.full(100, 100.0), 0),
            (np.array([0.0, 0.1, 0.3, 1.0]), 2),
        ):
            with self.subTest(tail_d=tail_d):
                result = summarize(np.concatenate((body, tail_d)), 0.3, len(tail_d))
                self.assertEqual(result[:5], (1, 10.0, expected_tail, 1.0, 0.1))
                np.testing.assert_array_equal(result[5], [2])

    def test_split_boundary_uses_later_frame_numbers(self):
        d = np.array([1.0, 1.0, 0.1, 0.1])
        result = summarize(d, 0.3, 1)
        self.assertEqual(result[0], 1)
        self.assertAlmostEqual(result[1], 100 / 3)
        self.assertEqual(result[2], 1)
        np.testing.assert_array_equal(result[5], [4])
        result = summarize(np.array([1.0, 0.1]), 0.3, 1)
        self.assertEqual(result[:5], (0, 0.0, 1, 1.0, 1.0))

    def test_invalid_tail_and_zero_body_p90_are_explicit_errors(self):
        for tail in (-1, 2, 3, 1.5):
            with self.subTest(tail=tail), self.assertRaises(ValueError):
                summarize(np.ones(2), 0.3, tail)
        with self.assertRaisesRegex(ValueError, "body P90 is zero"):
            summarize(np.array([0.0, 0.0, 100.0]), 0.3, 1)

    def test_undefined_or_invalid_inputs_are_explicit_errors(self):
        for d in (np.array([]), np.zeros(2), np.array([np.nan]), np.array([np.inf]),
                  np.array([-1.0]), np.ones((2, 2))):
            with self.subTest(d=d), self.assertRaises(ValueError):
                summarize(d, 0.3, 0)
        for ratio in (0, -1, np.nan, np.inf):
            with self.subTest(ratio=ratio), self.assertRaises(ValueError):
                summarize(np.ones(2), ratio, 0)
        for kwargs in ({"step": 0}, {"step": -1}, {"max_frames": -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                frame_diffs("test.mov", **kwargs)

    def test_cli_reports_candidates(self):
        with patch("sys.argv", ["video_qc", "test.mov", "--tail", "0"]):
            with patch("phase2.video_qc.frame_diffs", return_value=(4, np.array([0.1, 1.0, 1.0]))):
                with redirect_stdout(io.StringIO()) as output:
                    main()
        self.assertIn("33.33", output.getvalue())
        self.assertIn("tail_dup", output.getvalue())
        self.assertIn("first duplicate frames in body (1-based): [2]", output.getvalue())

    def test_cli_defaults_to_thirty_tail_pairs(self):
        d = np.concatenate(([0.1, 1.0, 1.0], np.zeros(30)))
        with patch("sys.argv", ["video_qc", "test.mov"]):
            with patch("phase2.video_qc.frame_diffs", return_value=(34, d)):
                with redirect_stdout(io.StringIO()) as output:
                    main()
        self.assertEqual(
            output.getvalue().splitlines()[1].split(),
            ["test", "34", "1", "33.33", "30", "0.100", "1.000", "0.100"],
        )

    def test_cli_rejects_negative_tail_before_reading(self):
        with patch("sys.argv", ["video_qc", "test.mov", "--tail", "-1"]):
            with patch("phase2.video_qc.frame_diffs") as read:
                with redirect_stderr(io.StringIO()) as error:
                    with self.assertRaises(SystemExit) as exit_info:
                        main()
        self.assertEqual(exit_info.exception.code, 2)
        self.assertIn("--tail must be nonnegative", error.getvalue())
        read.assert_not_called()

    def test_cli_rejects_unassessable_video(self):
        with patch("sys.argv", ["video_qc", "test.mov"]):
            with patch("phase2.video_qc.frame_diffs", return_value=(1, np.array([]))):
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as error:
                    with self.assertRaises(SystemExit) as exit_info:
                        main()
        self.assertEqual(exit_info.exception.code, 1)
        self.assertIn("test.mov: at least two decoded frames", error.getvalue())


if __name__ == "__main__":
    unittest.main()
