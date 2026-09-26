"""Restore torch.autograd.gradcheck.zero_gradients (removed from torch) and run the unchanged attack_sgm.py.

advertorch 0.2.x imports the helper at package import; LinfPGDAttack does not call it.
The class_to_idx.npy it loads with allow_pickle was inspected beforehand with a restricted
unpickler (safe_npy.py) and holds only a synset -> index dict.
"""
import runpy
import sys

if __name__ == "__main__":
    import torch
    import torch.autograd.gradcheck  # noqa: F401  (ensure the module is loaded)
    gradcheck = sys.modules["torch.autograd.gradcheck"]  # attribute access yields the function

    def zero_gradients(x):
        if isinstance(x, torch.Tensor):
            if x.grad is not None:
                x.grad.detach_()
                x.grad.zero_()
        else:
            for elem in x:
                zero_gradients(elem)

    if not hasattr(gradcheck, "zero_gradients"):
        gradcheck.zero_gradients = zero_gradients
    sys.path.insert(0, ".")
    sys.argv = ["attack_sgm.py", *sys.argv[1:]]
    runpy.run_path("attack_sgm.py", run_name="__main__")
