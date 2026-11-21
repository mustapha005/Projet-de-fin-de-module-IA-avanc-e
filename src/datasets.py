"""Development-only loading and reproducible, method-independent augmentation."""
import hashlib
import json

import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms as T
from torchvision.transforms import InterpolationMode

from src.runtime import ROOT, sha256

MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]


def image_transform(training: bool, size: int = 224):
    """Use PIL bilinear interpolation and tensor normalization from the protocol."""
    steps = [T.Grayscale(num_output_channels=3)]
    if training:
        steps += [T.RandomResizedCrop(size, scale=(.8, 1.), ratio=(.75, 4 / 3),
                                     interpolation=InterpolationMode.BILINEAR, antialias=True),
                  T.RandomHorizontalFlip(.5),
                  T.RandomRotation(10, interpolation=InterpolationMode.BILINEAR, fill=0),
                  T.ColorJitter(brightness=.1, contrast=.1)]
    else:
        steps += [T.Resize(size, interpolation=InterpolationMode.BILINEAR, antialias=True),
                  T.CenterCrop(size)]
    return T.Compose(steps + [T.ToTensor(), T.Normalize(MEAN, STD)])


def view_seed(seed: int, image_id: str, view: int) -> int:
    message = json.dumps([seed, image_id, view], separators=(',', ':')).encode()
    return int.from_bytes(hashlib.sha256(message).digest()[:8], 'little') % (2 ** 63)


class Images(Dataset):
    """Rows are supplied by the caller; views repeat images, not unique labels."""
    def __init__(self, rows: pd.DataFrame, training=False, seed=0, views=1, size=224):
        self.rows = rows.to_dict('records')
        self.transform = image_transform(training, size)
        self.training, self.seed, self.views, self.epoch = training, seed, views, 0
        if views < 1:
            raise ValueError('At least one view is required')

    def __len__(self):
        return len(self.rows) * self.views

    def __getitem__(self, index):
        row = self.rows[index // self.views]
        view = index % self.views if self.views > 1 else self.epoch
        with Image.open(ROOT / row['path']) as image:
            # torchvision transforms use torch's CPU RNG. Isolate it from model RNG.
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(view_seed(self.seed, row['image_id'], view))
                tensor = self.transform(image)
        return tensor, int(row['label']), row['image_id']


def development_rows(fraction: float, seed: int):
    """Fail closed on modified preparation evidence or any held-out record."""
    evidence = json.loads((ROOT / 'data/development_view.json').read_text())
    path = ROOT / evidence['path']
    if sha256(path) != evidence['development_sha256']:
        raise ValueError('Development manifest checksum mismatch; rerun data preparation')
    rows = pd.read_csv(path, dtype={'phash': str})
    if not set(rows.split) <= {'train', 'val'}:
        raise ValueError('Held-out rows are forbidden in the development interface')
    subsets = pd.read_csv(ROOT / 'data/manifests/label_subsets.csv')
    chosen = subsets[(subsets.seed == seed) & np.isclose(subsets.fraction, fraction)]
    if chosen.empty:
        raise ValueError('No frozen label subset for this seed/fraction')
    train = rows[rows.image_id.isin(chosen.image_id)].sort_values('image_id')
    if set(train.split) != {'train'} or len(train) != len(chosen):
        raise ValueError('Invalid selected development subset')
    if not train.set_index('image_id').label.sort_index().equals(chosen.set_index('image_id').label.sort_index()):
        raise ValueError('Subset labels changed')
    return train.reset_index(drop=True), rows[rows.split == 'val'].sort_values('image_id').reset_index(drop=True)


def loader(dataset: Images, shuffle=False, seed=0):
    return DataLoader(dataset, batch_size=min(32, len(dataset)), shuffle=shuffle,
                      generator=torch.Generator().manual_seed(seed), num_workers=0, drop_last=False)
