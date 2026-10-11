import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import numpy as np

from phase2.scripts.labels_to_sheets import main, performer_sized


class LabelsToSheetsTests(unittest.TestCase):
    def row(self, cx, width, height, confidence=0.9):
        keypoints = np.zeros((17, 3))
        keypoints[:, 0] = cx
        keypoints[:, 1] = 0.5 + np.linspace(-0.1, 0.1, 17)
        keypoints[:, 2] = 0.9
        return np.concatenate(([0, cx, 0.5, width, height], keypoints.ravel(), [confidence]))

    def write_synthetic_labels(self, labels):
        for frame in range(1, 161):
            rows = [self.row(0.70, 0.02, 0.11), self.row(0.72, 0.02, 0.12)]
            if 41 <= frame <= 100:
                progress = (frame - 41) / 59
                rows.extend((
                    self.row(0.10 + 0.35 * progress, 0.07, 0.42),
                    self.row(0.90 - 0.35 * progress, 0.07, 0.42),
                ))
            elif 101 <= frame <= 120:
                rows.extend((self.row(0.47, 0.07, 0.42), self.row(0.52, 0.07, 0.42)))
            elif 121 <= frame <= 140:
                rows.append(self.row(0.49, 0.12, 0.42))
            elif frame >= 141:
                rows.extend((
                    self.row(0.47 - 0.002 * (frame - 140), 0.07, 0.42),
                    self.row(0.52 + 0.002 * (frame - 140), 0.07, 0.42),
                ))
            np.savetxt(labels / f"TK_{frame}.txt", np.asarray(rows), fmt="%.6f")

    def run_main(self, labels, out, *options):
        argv = [
            "labels_to_sheets", str(labels), "TK", "1", "160", str(out), *options,
        ]
        with patch("sys.argv", argv), redirect_stdout(io.StringIO()) as output:
            main()
        return output.getvalue()

    def load_sheet(self, out, person, fusion="assign"):
        return np.load(out / f"yolo_raw_TK_{person}_{fusion}.npz")

    def test_performer_size_gate_uses_pixel_area_or_long_side(self):
        small = [0.5, 0.5, 0.02, 0.11]
        player = [0.5, 0.5, 0.07, 0.42]
        self.assertFalse(performer_sized(small, 400, 700))
        self.assertTrue(performer_sized(player, 400, 700))
        self.assertTrue(performer_sized(small, 0, 0))
        self.assertTrue(performer_sized([0.5, 0.5, 0.02, 0.11], 0, 700))

    def test_default_gate_keeps_all_detections_and_preserves_raw_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            labels, out = root / "labels", root / "out"
            labels.mkdir()
            self.write_synthetic_labels(labels)

            output = self.run_main(labels, out)
            self.assertIn("n_det histogram (0/1/2/3+): [0, 0, 40, 120]  init frame: 1", output)
            self.assertIn(
                "tackler side: right  size gate: min_size=0.0, min_long=0.0  "
                "detections removed by the gate: 0",
                output,
            )
            for person in ("tackler", "carrier"):
                with self.load_sheet(out, person) as sheet:
                    np.testing.assert_array_equal(sheet["n_det"], sheet["n_det_raw"])
                    np.testing.assert_array_equal(sheet["n_det_raw"][:40], np.full(40, 2))
                    self.assertEqual(sheet["tackler_side"].item(), "right")
                    self.assertEqual(sheet["min_size"].item(), 0)
                    self.assertEqual(sheet["min_long"].item(), 0)

    def test_size_gate_filters_passers_and_init_side_assigns_player_tracks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            labels, out = root / "labels", root / "out"
            labels.mkdir()
            self.write_synthetic_labels(labels)

            right_output = self.run_main(
                labels, out, "--min-size", "400", "--min-long", "700",
            )
            self.assertIn("n_det histogram (0/1/2/3+): [40, 20, 100, 0]  init frame: 41", right_output)
            self.assertIn("detections removed by the gate: 320", right_output)
            self.assertIn("tackler: observed 100/160 frames", right_output)
            self.assertIn("carrier: observed 120/160 frames", right_output)
            with self.load_sheet(out, "tackler") as tackler, self.load_sheet(out, "carrier") as carrier:
                np.testing.assert_array_equal(tackler["n_det"], carrier["n_det"])
                np.testing.assert_array_equal(tackler["n_det_raw"], np.full(160, 2) + np.r_[np.zeros(40), np.full(80, 2), np.full(20, 1), np.full(20, 2)])
                self.assertEqual(tackler["n_det"][39], 0)
                self.assertAlmostEqual(tackler["bbox"][69, 0], 0.90 - 0.35 * (29 / 59), places=5)
                self.assertAlmostEqual(carrier["bbox"][69, 0], 0.10 + 0.35 * (29 / 59), places=5)

            left_output = self.run_main(
                labels, out, "--min-size", "400", "--min-long", "700",
                "--tackler-side", "left",
            )
            self.assertIn("init frame: 41", left_output)
            with self.load_sheet(out, "tackler") as tackler, self.load_sheet(out, "carrier") as carrier:
                self.assertEqual(tackler["tackler_side"].item(), "left")
                self.assertAlmostEqual(tackler["bbox"][69, 0], 0.10 + 0.35 * (29 / 59), places=5)
                self.assertAlmostEqual(carrier["bbox"][69, 0], 0.90 - 0.35 * (29 / 59), places=5)

    def test_invalid_size_thresholds_fail_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            labels = root / "labels"
            labels.mkdir()
            for option, value in (("--min-size", "-1"), ("--min-size", "nan"),
                                  ("--min-long", "-1"), ("--min-long", "inf")):
                with self.subTest(option=option, value=value), redirect_stderr(io.StringIO()):
                    with patch("sys.argv", [
                        "labels_to_sheets", str(labels), "TK", "1", "1",
                        str(root / "out"), option, value,
                    ]):
                        with self.assertRaises(SystemExit) as exc:
                            main()
                    self.assertEqual(exc.exception.code, 2)
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()
