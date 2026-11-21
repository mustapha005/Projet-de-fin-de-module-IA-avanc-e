"""Gradient and representation checks on a small real DINOv2 architecture."""
import copy
import unittest

import torch
from transformers import Dinov2Config, Dinov2Model

from src.models import DinoClassifier, pooled


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)

    def backbone(self):
        config = Dinov2Config(hidden_size=24, num_hidden_layers=12,
                              num_attention_heads=3, mlp_ratio=2, image_size=28,
                              patch_size=14, drop_path_rate=0.)
        config._attn_implementation = 'eager'
        return Dinov2Model(config)

    def test_partial_forward_matches_full_backbone_and_freezes_prefix(self):
        base = self.backbone().eval()
        model = DinoClassifier('PFT', backbone=copy.deepcopy(base)).eval()
        pixels = torch.randn(2, 3, 28, 28)
        expected = pooled(base(pixels).last_hidden_state)
        torch.testing.assert_close(model.features(pixels), expected)
        model.train()
        model(pixels).square().mean().backward()
        self.assertTrue(all(p.grad is None for p in model.backbone.embeddings.parameters()))
        self.assertTrue(all(p.grad is None for layer in model.backbone.encoder.layer[:-2] for p in layer.parameters()))
        self.assertTrue(all(p.grad is not None for layer in model.backbone.encoder.layer[-2:] for p in layer.parameters()))
        self.assertTrue(all(p.grad is not None for p in model.head.parameters()))

    def test_lora_matches_initial_features_and_adapts_only_requested_projections(self):
        base = self.backbone().eval()
        model = DinoClassifier('LoRA', lora_depth=2, backbone=copy.deepcopy(base)).eval()
        pixels = torch.randn(2, 3, 28, 28)
        torch.testing.assert_close(model.features(pixels), pooled(base(pixels).last_hidden_state))
        names = [name for name, p in model.named_parameters() if p.requires_grad]
        self.assertEqual(len([n for n in names if 'lora_' in n]), 12)
        self.assertTrue(all('lora_' in n or n.startswith('head.') for n in names))
        self.assertTrue(all('.10.' in n or '.11.' in n for n in names if 'lora_' in n))
        model.train()
        model(pixels).square().mean().backward()
        grads = [(n, p.grad) for n, p in model.named_parameters()]
        self.assertTrue(all(g is None for n, g in grads if n not in names))
        self.assertTrue(any(g is not None and g.abs().sum() > 0 for n, g in grads if 'lora_B' in n))

    def test_linear_probe_has_no_autograd_graph(self):
        model = DinoClassifier('LP', backbone=self.backbone())
        features = model(torch.randn(2, 3, 28, 28, requires_grad=True))
        self.assertEqual(features.shape, (2, 48))
        self.assertFalse(features.requires_grad)
        self.assertFalse(any(p.requires_grad for p in model.parameters()))


if __name__ == '__main__':
    unittest.main()
