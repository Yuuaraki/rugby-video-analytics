import csv
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import numpy as np

from phase2.scripts.labels_to_sheets import COCO17
from phase2.scripts.solo_sheet import BODY12, main, read_frame, true_runs
from phase2.temporal import observed_mask


class SoloSheetTests(unittest.TestCase):
    def row(self, box_conf=0.9, coord=0.4):
        kpts = np.tile([coord, 0.6, 0.8], (17, 1))
        return np.concatenate(([0, 0.5, 0.5, 0.2, 0.3], kpts.ravel(), [box_conf]))

    def run_main(self, labels, n_frames, out_dir, *options):
        argv = [
            "solo_sheet", str(labels), "clip", str(n_frames),
            "--out-dir", str(out_dir), "--runs-dir", str(out_dir), *options,
        ]
        with patch("sys.argv", argv), redirect_stdout(io.StringIO()) as output:
            main()
        return output.getvalue()

    def test_read_frame_selects_highest_box_confidence_and_exact_slices(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frame.txt"
            for rows in ([self.row()], [self.row(0.2, 0.1), self.row(0.9, 0.4)]):
                np.savetxt(path, rows)
                coords, confs, bbox, count, candidates = read_frame(path, 400, 0.005, 3840, 2160)
                self.assertEqual(count, len(rows))
                self.assertEqual(candidates, len(rows))
                np.testing.assert_allclose(coords, np.tile([0.4, 0.6], (17, 1)))
                np.testing.assert_allclose(confs, 0.8)
                np.testing.assert_allclose(bbox, [0.5, 0.5, 0.2, 0.3])

    def test_empty_file_means_no_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.txt"
            path.write_text(" \n")
            coords, confs, bbox, count, candidates = read_frame(path, 400, 0.005, 3840, 2160)
            self.assertEqual(coords.shape, (17, 2))
            self.assertEqual(confs.shape, (17,))
            self.assertEqual(bbox.shape, (4,))
            self.assertEqual(count, 0)
            self.assertEqual(candidates, 0)
            for values in (coords, confs, bbox):
                self.assertFalse(values.any())

    def test_gates_are_inclusive_and_use_pixel_area_and_both_edges(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frame.txt"
            row = self.row()
            row[1:5] = [0.5, 0.5, 0.5, 0.5]
            cases = (
                (row.copy(), 500, 0.25, 1000, 1000, 1),
                (row.copy(), 501, 0.25, 1000, 1000, 0),
                (row.copy(), 500, 0.25, 500, 1000, 0),
                (row.copy(), 0, 0, 1000, 1000, 1),
            )
            left, right = row.copy(), row.copy()
            left[1] = 0.49
            right[1] = 0.51
            cases += (
                (left, 500, 0.25, 1000, 1000, 0),
                (right, 500, 0.25, 1000, 1000, 0),
            )
            for values, min_size, eps, width, height, expected in cases:
                with self.subTest(min_size=min_size, eps=eps, width=width, cx=values[1]):
                    np.savetxt(path, [values])
                    coords, confs, bbox, count, candidates = read_frame(
                        path, min_size, eps, width, height,
                    )
                    self.assertEqual((count, candidates), (1, expected))
                    if not expected:
                        for result in (coords, confs, bbox):
                            self.assertFalse(result.any())

    def test_long_side_is_an_inclusive_alternative_to_min_size(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frame.txt"
            row = self.row()
            row[3:5] = [0.3, 0.1]
            np.savetxt(path, [row])

            self.assertEqual(read_frame(path, 200, 0.005, 1000, 1000)[4], 0)
            self.assertEqual(read_frame(path, 200, 0.005, 1000, 1000, 300)[4], 1)
            self.assertEqual(read_frame(path, 200, 0.005, 1000, 1000, 301)[4], 0)

            row[3:5] = [0.1, 0.3]
            np.savetxt(path, [row])
            self.assertEqual(read_frame(path, 300, 0.005, 1000, 2000, 400)[4], 1)

    def test_rejected_high_confidence_rows_do_not_win_candidate_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frame.txt"
            small = self.row(0.99, 0.1)
            small[3:5] = 0.01
            edge = self.row(0.98, 0.2)
            edge[1] = 0.05
            np.savetxt(path, [small, edge, self.row(0.7, 0.3), self.row(0.8, 0.4)])
            coords, _, _, count, candidates = read_frame(path, 400, 0.005, 3840, 2160)
            self.assertEqual((count, candidates), (4, 2))
            np.testing.assert_allclose(coords[:, 0], 0.4)

    def test_multiple_and_zero_candidates_break_runs_but_preserve_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            labels = root / "labels"
            labels.mkdir()
            small = self.row()
            small[3:5] = 0.01
            np.savetxt(labels / "clip_1.txt", [self.row()])
            np.savetxt(labels / "clip_2.txt", [self.row(0.7, 0.3), self.row()])
            np.savetxt(labels / "clip_3.txt", [self.row()])
            np.savetxt(labels / "clip_4.txt", [small])
            output = self.run_main(labels, 5, root / "out", "--tail", "0", "--win", "1")
            self.assertIn("n_cand histogram (0/1/2+): [2, 2, 1]", output)
            self.assertIn("runs >= 1: 2  frames: 2  windows: 2", output)
            with np.load(root / "out/yolo_raw_clip_solo.npz") as sheet:
                np.testing.assert_array_equal(sheet["n_det"], [1, 2, 1, 1, 0])
                np.testing.assert_array_equal(sheet["n_cand"], [1, 2, 1, 0, 0])
                self.assertTrue(sheet["coords"][1].any())
                self.assertFalse(sheet["coords"][3:].any())
            with (root / "out/solo_runs_clip.csv").open(newline="") as f:
                self.assertEqual(list(csv.reader(f))[1:], [
                    ["clip", "1", "1", "1", "0"], ["clip", "3", "3", "1", "0"],
                ])

    def test_malformed_labels_raise_with_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.txt"
            invalid = [
                "not a label\n",
                " ".join(["0"] * 56),
                " ".join(["0"] * 58),
                " ".join(["0"] * 57) + "\n0 1\n",
            ]
            for value in (np.nan, np.inf, -0.1, 1.1):
                row = self.row()
                row[10] = value
                invalid.append(" ".join(map(str, row)))
            for text in invalid:
                with self.subTest(text=text):
                    path.write_text(text)
                    with self.assertRaisesRegex(ValueError, str(path)):
                        read_frame(path, 400, 0.005, 3840, 2160)

    def test_true_runs_boundaries_empty_and_signed_conversion(self):
        cases = (
            ([], []),
            ([False, False], []),
            ([True], [(0, 0)]),
            ([True, True], [(0, 1)]),
            ([False, True, True, False, True, True, True], [(1, 2), (4, 6)]),
            ([True, False, True], [(0, 0), (2, 2)]),
        )
        for mask, expected in cases:
            for dtype in (bool, np.int64, np.uint8):
                with self.subTest(mask=mask, dtype=dtype):
                    self.assertEqual(true_runs(np.array(mask, dtype=dtype)), expected)
        for mask in (np.ones((2, 2), dtype=bool), np.array([0, 2])):
            with self.assertRaises(ValueError):
                true_runs(mask)

    def test_end_to_end_schema_runs_flags_and_windows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            labels = root / "labels"
            labels.mkdir()
            for n in range(1, 10):
                np.savetxt(labels / f"clip_{n}.txt", [self.row()])
            small = self.row(0.99, 0.1)
            small[3:5] = 0.01
            np.savetxt(labels / "clip_2.txt", [small, self.row()])
            (labels / "clip_4.txt").write_text("")
            (labels / "clip_7.txt").unlink()
            output = self.run_main(
                labels, 9, root / "out", "--tail", "1", "--win", "2",
                "--fps", "30", "--width", "1920", "--height", "1080",
                "--min-long", "300",
            )
            with np.load(root / "out/yolo_raw_clip_solo.npz", allow_pickle=False) as sheet:
                self.assertEqual(sheet["coords"].shape, (9, 17, 2))
                self.assertEqual(sheet["confs"].shape, (9, 17))
                self.assertEqual(sheet["bbox"].shape, (9, 4))
                for name in ("coords", "confs", "bbox"):
                    self.assertEqual(sheet[name].dtype, np.float32)
                    self.assertFalse(sheet[name][3].any())
                    self.assertFalse(sheet[name][6].any())
                    self.assertTrue(sheet[name][8].any())
                np.testing.assert_array_equal(sheet["frame_index"], np.arange(1, 10))
                np.testing.assert_array_equal(sheet["n_det"], [1, 2, 1, 0, 1, 1, 0, 1, 1])
                np.testing.assert_array_equal(sheet["n_cand"], [1, 1, 1, 0, 1, 1, 0, 1, 1])
                np.testing.assert_array_equal(sheet["joint_names"], COCO17)
                for name, value in (
                    ("fps", 30), ("W", 1920), ("H", 1080), ("tail", 1),
                    ("tau", 0.5), ("win", 2), ("source", "yolo_raw"), ("person", "solo"),
                    ("min_size", 400), ("edge_eps", 0.005), ("min_long", 300),
                ):
                    self.assertEqual(sheet[name].item(), value)
                self.assertEqual(observed_mask(sheet["coords"], sheet["confs"]).shape, (9, 17))
            with (root / "out/solo_runs_clip.csv").open(newline="") as f:
                self.assertEqual(list(csv.reader(f)), [
                    ["stem", "start", "end", "length", "n_flag"],
                    ["clip", "1", "3", "3", "1"],
                    ["clip", "5", "6", "2", "0"],
                    ["clip", "8", "8", "1", "0"],
                ])
            self.assertIn("fully visible frames (body-12, tau=0.5, n_cand==1): 6", output)
            self.assertIn("runs >= 2: 2  frames: 5  windows: 3", output)

    def test_standing_prone_and_small_pedestrian_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            labels = root / "labels"
            labels.mkdir()

            standing = self.row()
            standing[3:5] = [0.2, 0.7]
            prone = self.row()
            prone[3:5] = [0.4, 0.25]
            passerby = self.row(0.99, 0.2)
            passerby[3:5] = [0.03, 0.08]

            for frame in range(1, 121):
                player = prone if frame <= 80 and frame > 40 else standing
                detections = [player, passerby] if frame > 80 else [player]
                np.savetxt(labels / f"clip_{frame}.txt", detections)

            output = self.run_main(
                labels, 120, root / "out", "--tail", "0",
                "--width", "3840", "--height", "2160",
            )
            self.assertIn("n_det histogram (0/1/2/3+): [0, 80, 40, 0]", output)
            self.assertIn("n_cand histogram (0/1/2+): [0, 120, 0]", output)
            with np.load(root / "out/yolo_raw_clip_solo.npz") as sheet:
                np.testing.assert_array_equal(sheet["n_cand"], np.ones(120, dtype=np.int64))
                self.assertEqual(sheet["min_long"].item(), 700.0)

    def test_min_long_cli_value_controls_filter_and_is_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            labels = root / "labels"
            labels.mkdir()
            row = self.row()
            row[3:5] = [0.3, 0.1]
            np.savetxt(labels / "clip_1.txt", [row])

            output = self.run_main(
                labels, 1, root / "out", "--tail", "0", "--min-size", "200",
                "--min-long", "250", "--width", "1000", "--height", "1000",
            )
            self.assertIn("n_cand histogram (0/1/2+): [0, 1, 0]", output)
            with np.load(root / "out/yolo_raw_clip_solo.npz") as sheet:
                self.assertEqual(sheet["n_cand"][0], 1)
                self.assertEqual(sheet["min_long"].item(), 250.0)

    def test_visibility_uses_shared_mask_and_body12_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            labels = root / "labels"
            labels.mkdir()
            row = self.row()
            kpts = row[5:56].reshape(17, 3)
            kpts[:5, 2] = 0
            kpts[BODY12, 2] = 0.5
            np.savetxt(labels / "clip_1.txt", [row])
            kpts[5, 2] = 0.49
            np.savetxt(labels / "clip_2.txt", [row])
            kpts[:, 2] = 0.8
            kpts[:, :2] = 0
            np.savetxt(labels / "clip_3.txt", [row])
            output = self.run_main(labels, 4, root / "out", "--tail", "0", "--tau", "0.5")
            self.assertIn("fully visible frames (body-12, tau=0.5, n_cand==1): 1", output)
            with (root / "out/solo_runs_clip.csv").open(newline="") as f:
                self.assertEqual(list(csv.reader(f))[1:], [["clip", "1", "1", "1", "0"]])
            output = self.run_main(labels, 4, root / "out", "--tail", "0", "--tau", "0")
            self.assertIn("fully visible frames (body-12, tau=0.0, n_cand==1): 2", output)

    def test_tail_zero_equal_or_larger_than_frame_count(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for n in range(1, 4):
                np.savetxt(root / f"clip_{n}.txt", [self.row()])
            for tail, expected in ((0, 3), (1, 2), (3, 0), (30, 0)):
                with self.subTest(tail=tail):
                    output = self.run_main(root, 3, root / "out", "--tail", str(tail), "--win", "3")
                    self.assertIn(f"fully visible frames (body-12, tau=0.5, n_cand==1): {expected}", output)
                    self.assertIn(f"windows: {1 if tail == 0 else 0}", output)

    def test_all_missing_labels_writes_header_only_csv_and_zero_sheet(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = self.run_main(root, 4, root / "out", "--tail", "0")
            self.assertIn("runs: 0  longest: 0", output)
            self.assertIn("windows: 0", output)
            with (root / "out/solo_runs_clip.csv").open(newline="") as f:
                self.assertEqual(len(list(csv.reader(f))), 1)
            with np.load(root / "out/yolo_raw_clip_solo.npz") as sheet:
                self.assertFalse(sheet["coords"].any())
                self.assertFalse(sheet["n_det"].any())
                self.assertFalse(sheet["n_cand"].any())

    def test_invalid_cli_arguments_and_missing_directory_fail_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for options in (
                ("--tail", "-1"), ("--win", "0"), ("--tau", "nan"), ("--tau", "1.1"),
                ("--fps", "0"), ("--width", "0"), ("--height", "-1"),
                ("--min-size", "-1"), ("--min-size", "nan"), ("--min-size", "inf"),
                ("--min-long", "-1"), ("--min-long", "nan"), ("--min-long", "inf"),
                ("--edge-eps", "-0.01"), ("--edge-eps", "0.5"), ("--edge-eps", "nan"),
            ):
                with self.subTest(options=options), redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as exc:
                        self.run_main(root, 4, root / "out", *options)
                    self.assertEqual(exc.exception.code, 2)
            for labels, n in ((root / "missing", 4), (root, 0)):
                with self.subTest(labels=labels, n=n), redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as exc:
                        self.run_main(labels, n, root / "out")
                    self.assertEqual(exc.exception.code, 2)
            self.assertFalse((root / "out").exists())

    def test_bad_label_fails_explicitly_without_writing_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "clip_1.txt").write_text("0 1\n")
            with redirect_stderr(io.StringIO()) as error:
                with self.assertRaises(SystemExit) as exc:
                    self.run_main(root, 1, root / "out")
            self.assertEqual(exc.exception.code, 1)
            self.assertIn("clip_1.txt", error.getvalue())
            self.assertIn("expected 57 values", error.getvalue())
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()
