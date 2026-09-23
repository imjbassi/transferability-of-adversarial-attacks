"""PyTorch ports of selected SI-NI-FGSM and VMI-FGSM update loops.

The original releases require TensorFlow 1.x. Numerical equivalence has not
been validated. These runs use images and converted weights from an SSA checkout;
matching numeric random seeds does not establish cross-framework equivalence.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import transforms as T
from tqdm import tqdm

HERE = Path(__file__).resolve().parent
_bootstrap = argparse.ArgumentParser(add_help=False)
_bootstrap.add_argument('--ssa-root', type=Path, required=True,
                        help='Populated SSA checkout; see PROVENANCE.md')
_paths, _ = _bootstrap.parse_known_args()
SSA = _paths.ssa_root.resolve()
if not (SSA / 'loader.py').is_file():
    raise SystemExit('SSA checkout must contain loader.py and documented dependencies')
sys.path.insert(0, str(SSA))
from loader import ImageNet  # noqa: E402
from torch_nets import tf_inception_v3  # noqa: E402


def logits(model, images):
    output = model(images)
    return output[0] if isinstance(output, (tuple, list)) else output


def si_ni_fgsm(model, clean, epsilon, steps, momentum):
    z0 = clean * 2 - 1
    eps = 2 * epsilon
    alpha = eps / steps
    z = z0.clone().detach()
    grad_state = torch.zeros_like(z)
    with torch.no_grad():
        labels = logits(model, z).argmax(1)
    for _ in range(steps):
        z = z.detach().requires_grad_(True)
        total = torch.zeros_like(z)
        for scale in (1, 2, 4, 8, 16):
            z_nes = z + momentum * alpha * grad_state
            loss = F.cross_entropy(logits(model, z_nes / scale), labels)
            total = total + torch.autograd.grad(loss, z, retain_graph=False)[0]
        normalized = total / total.abs().mean((1, 2, 3), keepdim=True).clamp_min(1e-12)
        grad_state = momentum * grad_state + normalized
        z = z.detach() + alpha * grad_state.sign()
        z = torch.maximum(torch.minimum(z, z0 + eps), z0 - eps).clamp(-1, 1)
    return (z + 1) / 2


def vmi_fgsm(model, clean, epsilon, steps, momentum, samples, beta):
    z0 = clean * 2 - 1
    eps = 2 * epsilon
    alpha = eps / steps
    z = z0.clone().detach()
    grad_state = torch.zeros_like(z)
    variance = torch.zeros_like(z)
    with torch.no_grad():
        labels = logits(model, z).argmax(1)
    for _ in range(steps):
        probe = z.detach().requires_grad_(True)
        loss = F.cross_entropy(logits(model, probe), labels)
        new_grad = torch.autograd.grad(loss, probe)[0]
        global_grad = torch.zeros_like(z)
        for _ in range(samples):
            neighbor = (z + torch.empty_like(z).uniform_(-eps * beta, eps * beta)).detach()
            neighbor.requires_grad_(True)
            loss_neighbor = F.cross_entropy(logits(model, neighbor), labels)
            global_grad += torch.autograd.grad(loss_neighbor, neighbor)[0]
        current = new_grad + variance
        normalized = current / current.abs().mean((1, 2, 3), keepdim=True).clamp_min(1e-12)
        grad_state = momentum * grad_state + normalized
        variance = global_grad / samples - new_grad
        z = z + alpha * grad_state.sign()
        z = torch.maximum(torch.minimum(z, z0 + eps), z0 - eps).clamp(-1, 1).detach()
    return (z + 1) / 2


def main():
    parser = argparse.ArgumentParser(parents=[_bootstrap])
    parser.add_argument("mode", choices=("si-ni", "vmi"))
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--steps", type=int, required=True,
                        help="Explicit iteration count: historical port/code default 10; SI-NI paper setup states 16")
    args = parser.parse_args()
    if args.steps <= 0 or args.batch_size <= 0:
        parser.error('steps and batch-size must be positive')
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        parser.error('Use a new or empty output directory; archived runs must not be overwritten')

    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    device = torch.device("cuda")
    data = ImageNet(
        str(SSA / "dataset" / "images"),
        str(SSA / "dataset" / "images.csv"),
        T.ToTensor(),
    )
    loader = DataLoader(data, batch_size=args.batch_size, shuffle=False, num_workers=0)
    model = tf_inception_v3.KitModel(str(SSA / "models" / "tf_inception_v3.npy"))
    model = model.to(device).eval()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for images, names, _ in tqdm(loader):
        images = images.to(device)
        if args.mode == "si-ni":
            adversarial = si_ni_fgsm(model, images, 16 / 255, args.steps, 1.0)
        else:
            adversarial = vmi_fgsm(model, images, 16 / 255, args.steps, 1.0, 20, 1.5)
        arrays = (adversarial.detach().cpu().permute(0, 2, 3, 1).numpy() * 255).astype(np.uint8)
        for array, name in zip(arrays, names):
            Image.fromarray(array).save(args.output_dir / name)
    metadata = {
        "mode": args.mode,
        "seed": 0,
        "epsilon": "16/255",
        "steps": args.steps,
        "attack_label_policy": "clean_source_prediction",
        "evaluation_label_policy": "ground_truth_with_documented_index_conversion",
        "original_runtime_equivalence": "not_validated",
        "pixel_step_size": 16 / args.steps,
        "momentum": 1.0,
        "variance_samples": 20 if args.mode == "vmi" else None,
        "variance_beta": 1.5 if args.mode == "vmi" else None,
        "adapter": str(Path(__file__).resolve()),
    }
    (args.output_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
