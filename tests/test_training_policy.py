"""Verify independent views, held-out guards, and optimizer scheduling."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from PIL import Image
import torch

from src.datasets import Images, development_rows
from src.runtime import sha256
from src.train import lr_multiplier


class TrainingPolicyTests(unittest.TestCase):
    def test_augmentation_views_match_between_lp_and_neural_without_changing_rng(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pixels = np.random.default_rng(8).integers(0, 256, (260, 310), dtype=np.uint8)
            Image.fromarray(pixels).save(root / 'image.png')
            rows = pd.DataFrame([{'path': 'image.png', 'image_id': 'example', 'label': 1}])
            with patch('src.datasets.ROOT', root):
                lp = Images(rows, training=True, seed=7, views=4)
                neural = Images(rows, training=True, seed=7)
                state = torch.random.get_rng_state().clone()
                for view in range(4):
                    neural.epoch = view
                    torch.testing.assert_close(lp[view][0], neural[0][0], rtol=0, atol=0)
                self.assertTrue(torch.equal(state, torch.random.get_rng_state()))
                self.assertFalse(torch.equal(lp[0][0], lp[1][0]))

    def test_development_loader_rejects_even_one_held_out_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data').mkdir()
            pd.DataFrame([{'image_id': 'x', 'split': 'test'}]).to_csv(root / 'view.csv', index=False)
            (root / 'data/development_view.json').write_text(json.dumps({
                'path': 'view.csv', 'development_sha256': sha256(root / 'view.csv')}))
            with patch('src.datasets.ROOT', root), self.assertRaisesRegex(ValueError, 'Held-out'):
                development_rows(.1, 0)

    def test_warmup_and_cosine_finish_at_prespecified_endpoints(self):
        self.assertEqual(lr_multiplier(0, 4, 50), .25)
        self.assertEqual(lr_multiplier(3, 4, 50), 1.)
        self.assertEqual(lr_multiplier(199, 4, 50), 0.)
        self.assertEqual(lr_multiplier(1, 1, 2), 0.)


if __name__ == '__main__':
    unittest.main()
