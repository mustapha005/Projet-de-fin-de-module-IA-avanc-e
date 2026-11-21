"""DINOv2 adaptation with explicit frozen prefixes, and the scratch CNN."""
import json

from peft import LoraConfig, get_peft_model
import torch
from torch import nn
from torchvision.models import resnet18
from transformers import Dinov2Model

from src.runtime import ROOT, sha256


def load_backbone() -> Dinov2Model:
    pin = json.loads((ROOT / 'configs/backbone.json').read_text())
    folder = ROOT / pin['local_path']
    for filename, record in pin['files'].items():
        if sha256(folder / filename) != record['sha256']:
            raise ValueError(f'Backbone checksum mismatch: {filename}')
    return Dinov2Model.from_pretrained(folder, local_files_only=True,
                                      attn_implementation='eager')


def pooled(tokens: torch.Tensor) -> torch.Tensor:
    return torch.cat([tokens[:, 0], tokens[:, 1:].mean(dim=1)], dim=1)


class DinoClassifier(nn.Module):
    def __init__(self, method: str, depth=2, rank=8, lora_depth=12, backbone=None):
        super().__init__()
        if method not in {'LP', 'PFT', 'LoRA'}:
            raise ValueError(method)
        self.method, self.depth = method, depth
        self.backbone = load_backbone() if backbone is None else backbone
        count = len(self.backbone.encoder.layer)
        if not 1 <= depth <= count or not 1 <= lora_depth <= count:
            raise ValueError('Invalid adaptation depth')
        self.backbone.requires_grad_(False)
        self.target_modules = []
        if method == 'PFT':
            for layer in self.backbone.encoder.layer[-depth:]:
                layer.requires_grad_(True)
            self.backbone.layernorm.requires_grad_(True)
        elif method == 'LoRA':
            self.target_modules = [f'encoder.layer.{i}.attention.attention.{projection}'
                                   for i in range(count - lora_depth, count)
                                   for projection in ('query', 'key', 'value')]
            config = LoraConfig(r=rank, lora_alpha=16, lora_dropout=.1,
                                bias='none', target_modules=self.target_modules)
            self.backbone = get_peft_model(self.backbone, config)
        dim = self.backbone.config.hidden_size * 2
        self.head = nn.Identity() if method == 'LP' else nn.Linear(dim, 2)
        self.train()

    def train(self, mode=True):
        super().train(mode)
        if self.method == 'LP':
            self.backbone.eval()
        elif self.method == 'PFT':
            self.backbone.embeddings.eval()
            for layer in self.backbone.encoder.layer[:-self.depth]:
                layer.eval()
        return self

    def features(self, pixels: torch.Tensor) -> torch.Tensor:
        if self.method == 'PFT':
            with torch.no_grad():
                hidden = self.backbone.embeddings(pixels)
                for layer in self.backbone.encoder.layer[:-self.depth]:
                    hidden = layer(hidden)[0]
            for layer in self.backbone.encoder.layer[-self.depth:]:
                hidden = layer(hidden)[0]
            return pooled(self.backbone.layernorm(hidden))
        if self.method == 'LP':
            with torch.no_grad():
                return pooled(self.backbone(pixel_values=pixels).last_hidden_state)
        return pooled(self.backbone(pixel_values=pixels).last_hidden_state)

    def forward(self, pixels):
        return self.head(self.features(pixels))


def build_model(method: str, **options) -> nn.Module:
    if method == 'CNN':
        model = resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, 2)
        return model
    return DinoClassifier(method, **options)


def parameter_counts(model: nn.Module) -> dict:
    return {'total': sum(p.numel() for p in model.parameters()),
            'trainable': sum(p.numel() for p in model.parameters() if p.requires_grad)}
