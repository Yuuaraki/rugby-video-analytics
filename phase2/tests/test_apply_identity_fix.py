import numpy as np
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from phase2.scripts.apply_identity_fix import _apply_verdicts, _fill_unlisted_frames, _read_verdicts, main


class ApplyIdentityFixTests(unittest.TestCase):
    def test_apply_verdicts_uses_frame_numbers_and_changes_only_identity_arrays(self):
        tackler = {
            "frame_index": np.array([10, 11, 12, 13]),
            "coords": np.full((4, 2, 2), 1.0),
            "confs": np.full((4, 2), 0.1),
            "bbox": np.full((4, 4), 3.0),
            "n_det": np.array([2, 2, 1, 0]),
        }
        carrier = {
            "frame_index": np.array([13, 12, 11, 10]),
            "coords": np.array([[13.0] * 4, [12.0] * 4, [11.0] * 4, [10.0] * 4]).reshape(4, 2, 2),
            "confs": np.array([[13.0] * 2, [12.0] * 2, [11.0] * 2, [10.0] * 2]),
            "bbox": np.array([[13.0] * 4, [12.0] * 4, [11.0] * 4, [10.0] * 4]),
        }
        decisions = {
            11: ("swap", "tracks cross"),
            12: ("fused", "single merged detection"),
            13: ("no_valid", "neither detection is usable"),
        }

        verdicts, bases = _apply_verdicts(tackler, carrier, decisions)

        np.testing.assert_array_equal(verdicts, ["ok", "swap", "fused", "no_valid"])
        np.testing.assert_array_equal(bases, ["", "tracks cross", "single merged detection", "neither detection is usable"])
        np.testing.assert_array_equal(tackler["coords"][1], carrier["coords"][2])
        np.testing.assert_array_equal(tackler["confs"][1], carrier["confs"][2])
        np.testing.assert_array_equal(tackler["bbox"][1], carrier["bbox"][2])
        for name in ("coords", "confs", "bbox"):
            np.testing.assert_array_equal(tackler[name][2:], 0)
            initial_value = 3.0 if name == "bbox" else (0.1 if name == "confs" else 1.0)
            np.testing.assert_array_equal(tackler[name][0], np.full_like(tackler[name][0], initial_value))
        np.testing.assert_array_equal(tackler["n_det"], [2, 2, 1, 0])

    def test_apply_verdicts_rejects_swap_without_matching_carrier_frame(self):
        tackler = {
            "frame_index": np.array([10]),
            "coords": np.ones((1, 2, 2)),
            "confs": np.ones((1, 2)),
            "bbox": np.ones((1, 4)),
        }
        carrier = {
            "frame_index": np.array([11]),
            "coords": np.ones((1, 2, 2)),
            "confs": np.ones((1, 2)),
            "bbox": np.ones((1, 4)),
        }

        with self.assertRaisesRegex(ValueError, "missing from the carrier sheet"):
            _apply_verdicts(tackler, carrier, {10: ("swap", "")})

    def test_read_verdicts_rejects_duplicate_frame(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "verdicts.csv"
            csv_path.write_text("frame,verdict,basis\n10,ok,clear\n10,swap,crossing\n")

            with self.assertRaisesRegex(ValueError, "duplicate verdict for frame 10"):
                _read_verdicts(csv_path)

    def test_fill_unlisted_frames_only_uses_matching_listed_neighbours(self):
        decisions = {
            10: ("swap", "left verdict"),
            12: ("swap", "right verdict"),
            14: ("fused", "different verdict"),
            16: ("no_valid", "different verdict"),
        }

        filled = _fill_unlisted_frames(np.arange(10, 17), decisions)

        self.assertEqual(filled[11], ("swap", "filled from neighbours"))
        self.assertNotIn(13, filled)
        self.assertNotIn(15, filled)
        self.assertNotIn(11, decisions)

    def test_main_writes_loadable_verified_sheet_and_audit_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            sheet_dir = Path(directory)
            frames = np.array([10, 11, 12])
            common = {
                "coords": np.ones((3, 2, 2), dtype=np.float32),
                "confs": np.ones((3, 2), dtype=np.float32),
                "bbox": np.ones((3, 4), dtype=np.float32),
                "frame_index": frames,
            }
            np.savez(sheet_dir / "yolo_raw_P9201256_tackler_assign.npz", **common)
            carrier = {**common, "coords": np.full((3, 2, 2), 2, dtype=np.float32)}
            np.savez(sheet_dir / "yolo_raw_P9201256_carrier_assign.npz", **carrier)
            csv_path = sheet_dir / "verdicts.csv"
            csv_path.write_text("frame,verdict,basis\n10,swap,identity crossing\n12,swap,identity crossing\n")

            with patch("sys.argv", ["apply_identity_fix", str(sheet_dir), str(csv_path)]):
                main()

            with np.load(sheet_dir / "yolo_raw_P9201256_tackler_verified.npz", allow_pickle=False) as result:
                np.testing.assert_array_equal(result["coords"][1], 1)
                np.testing.assert_array_equal(result["identity_verdict"], ["swap", "ok", "swap"])

            with patch("sys.argv", ["apply_identity_fix", str(sheet_dir), str(csv_path), "--fill-odd"]):
                main()

            with np.load(sheet_dir / "yolo_raw_P9201256_tackler_verified.npz", allow_pickle=False) as result:
                np.testing.assert_array_equal(result["coords"], 2)
                np.testing.assert_array_equal(result["identity_verdict"], ["swap", "swap", "swap"])
                np.testing.assert_array_equal(
                    result["identity_fix_basis"],
                    ["identity crossing", "filled from neighbours", "identity crossing"],
                )
                self.assertEqual(result["identity_fix_counts"].dtype.names, ("verdict", "count"))


if __name__ == "__main__":
    unittest.main()
