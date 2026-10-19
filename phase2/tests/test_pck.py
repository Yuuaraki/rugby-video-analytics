import tempfile
import unittest
from pathlib import Path

import numpy as np

from phase2.pck import (
    BODY12,
    align,
    bias_correct,
    load_gt,
    load_sheet,
    offsets,
    pck_matrix,
    subsets,
    torso_length,
)


def make_gt(frames=(3226, 3227, 3228)):
    coords = np.zeros((len(frames), 12, 2), dtype=float)
    coords[:, 0] = (10, 20)
    coords[:, 1] = (30, 20)
    coords[:, 6] = (10, 80)
    coords[:, 7] = (30, 80)
    for k in range(12):
        if k not in (0, 1, 6, 7):
            coords[:, k] = (100 + k, 100 + k)
    return {
        "coords": coords,
        "vis": np.zeros((len(frames), 12), dtype=int),
        "frames": np.asarray(frames),
    }


class PckTests(unittest.TestCase):
    def test_load_gt_converts_to_pixels_and_excludes_nonfinite_visible_gt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gt.npz"
            coords = np.full((1, 12, 2), 0.5)
            coords[0, 2] = np.nan
            np.savez(path, coords=coords, vis=np.zeros((1, 12)), frame_index=[10], W=100, H=80)

            with self.assertWarnsRegex(UserWarning, "1 NaN joints"):
                gt = load_gt(path)

        np.testing.assert_array_equal(gt["coords"][0, 0], [50, 40])
        self.assertEqual(gt["vis"][0, 2], 2)

    def test_load_sheet_reorders_named_joints_and_converts_normalized_coordinates(self):
        with tempfile.TemporaryDirectory() as tmp:
            names = BODY12[::-1]
            values = np.arange(24, dtype=float).reshape(1, 12, 2) / 100
            path = Path(tmp) / "sheet.npz"
            np.savez(path, coords=values, frame_index=[10], joint_names=names, W=100, H=200)

            sheet = load_sheet(path)

        expected = values[:, [names.index(name) for name in BODY12], :] * [100, 200]
        np.testing.assert_allclose(sheet["coords"], expected)

    def test_load_sheet_extracts_coco_body_joints(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "coco.npz"
            coords = np.arange(34, dtype=float).reshape(1, 17, 2)
            np.savez(path, coords=coords, frame_index=[10], W=100, H=200)

            sheet = load_sheet(path)

        np.testing.assert_array_equal(sheet["coords"], coords[:, 5:17, :])

    def test_align_uses_frame_index_and_counts_zero_prediction_as_present(self):
        gt = make_gt((100, 102))
        sheet = {
            "frames": np.array([101, 102, 100]),
            "coords": np.full((3, 12, 2), 25.0),
        }
        sheet["coords"][1, 0] = 0

        pred = align(gt, sheet)

        np.testing.assert_array_equal(pred[:, 1], [[25, 25], [25, 25]])
        np.testing.assert_array_equal(pred[0, 0], [25, 25])
        np.testing.assert_array_equal(pred[1, 0], [0, 0])
        correct, scored, _ = pck_matrix(pred, gt, 0.1)
        self.assertTrue(scored[1, 0])
        self.assertFalse(correct[1, 0])

    def test_align_rejects_ambiguous_duplicate_sheet_frames(self):
        gt = make_gt((100,))
        sheet = {"frames": np.array([100, 100]), "coords": np.zeros((2, 12, 2))}

        with self.assertRaisesRegex(ValueError, "duplicates"):
            align(gt, sheet)

    def test_torso_length_uses_median_for_frames_with_outside_joint(self):
        gt = make_gt((1, 2, 3))
        gt["vis"][1, 0] = 2
        gt["coords"][1, 0] = np.nan

        lengths = torso_length(gt, per_frame=True)

        np.testing.assert_allclose(lengths, [60, 60, 60])

    def test_phase_subsets_broadcast_frame_ranges_over_joints(self):
        gt = make_gt((3226, 3227, 3228, 3280, 3281, 3282))

        masks = subsets(gt, "P9201256")

        self.assertEqual(masks["pre"].shape, (6, 12))
        np.testing.assert_array_equal(masks["pre"][:, 0], [True, False, False, False, False, False])
        np.testing.assert_array_equal(masks["contact"][:, 0], [False, False, True, True, False, False])
        np.testing.assert_array_equal(masks["fusion"][:, 0], [False, False, False, False, False, True])

    def test_offsets_returns_nan_statistics_without_visible_observations(self):
        gt = make_gt((1,))
        gt["vis"][:] = 1
        pred = np.full_like(gt["coords"], np.nan)

        rows = offsets(pred, gt)

        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[0]["n"], 0)
        self.assertTrue(np.isnan(rows[0]["mean_dx"]))

    def test_nan_prediction_is_excluded_from_numerator_and_denominator(self):
        gt = make_gt((100, 102))
        pred = gt["coords"].copy()                      # perfect sheet: n = 24, all correct
        pred[0, 3] = np.nan                             # one joint-frame unknown -> not scored
        correct, scored, _ = pck_matrix(pred, gt, 0.10)
        self.assertEqual(int(scored.sum()), 24 - 1)
        self.assertEqual(int(correct.sum()), 24 - 1)
        pred[1, 3] = (0, 0)                             # a (0,0) miss stays scored and counts as wrong
        correct, scored, _ = pck_matrix(pred, gt, 0.10)
        self.assertEqual(int(scored.sum()), 24 - 1)
        self.assertEqual(int(correct.sum()), 24 - 2)

    def test_bias_correct_restores_a_uniformly_shifted_sheet(self):
        gt = make_gt((100, 102, 104))                   # torso 60 px -> 0.10*60 = 6 px, offsets() keeps dist <= 30 px
        shift = np.array([8.0, -12.0])                  # 14.4 px: wrong at alpha 0.10, but inside the outlier rule
        pred = gt["coords"] + shift
        pred_bc, bias = bias_correct(pred, gt, np.ones(3, bool))
        np.testing.assert_allclose(bias, np.tile(shift, (12, 1)))
        self.assertEqual(pck_matrix(pred, gt, 0.10)[0].mean(), 0.0)
        self.assertEqual(pck_matrix(pred_bc, gt, 0.10)[0].mean(), 1.0)
        
    def test_torso_length_default_is_per_clip_reference(self):
        gt = make_gt((1, 2, 3))                       # torso 60 on every frame
        gt["coords"][1, [6, 7], 1] = 100              # frame 2: torso 80
        gt["coords"][2, [6, 7], 1] = 120              # frame 3: torso 100
        gt["vis"][1, 0] = 2                           # frame 2 excluded from the reference -> median of {60, 100}
        np.testing.assert_allclose(torso_length(gt), [80, 80, 80])

if __name__ == "__main__":
    unittest.main()
