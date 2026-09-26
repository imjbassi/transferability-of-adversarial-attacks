"""Lazily restore torch.autograd.gradcheck.zero_gradients (removed from torch) for advertorch 0.2.x.

Installed into the isolated SGM venv's site-packages together with
`zz_zero_gradients_shim.pth` (one line: `import zero_gradients_shim`), so that every
interpreter using that venv, including Windows-spawned DataLoader workers that re-import
attack_sgm.py, gets it. The .pth runs before torch is importable (torch lives in the user
site), so the patch is applied by an import hook when torch.autograd.gradcheck loads.
advertorch imports the helper at package import; LinfPGDAttack never calls it.
"""
import importlib.abc
import sys

TARGET = "torch.autograd.gradcheck"


def _zero_gradients(x):
    import torch
    if isinstance(x, torch.Tensor):
        if x.grad is not None:
            x.grad.detach_()
            x.grad.zero_()
    else:
        for elem in x:
            _zero_gradients(elem)


class _Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname != TARGET:
            return None
        for finder in sys.meta_path:
            if finder is self:
                continue
            spec = finder.find_spec(fullname, path, target) if hasattr(finder, "find_spec") else None
            if spec is not None:
                original = spec.loader.exec_module

                def exec_module(module, _original=original):
                    _original(module)
                    if not hasattr(module, "zero_gradients"):
                        module.zero_gradients = _zero_gradients
                spec.loader.exec_module = exec_module
                return spec
        return None


if not any(isinstance(f, _Finder) for f in sys.meta_path):
    sys.meta_path.insert(0, _Finder())
