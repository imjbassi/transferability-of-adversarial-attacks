"""Seed python/numpy/torch RNGs, then run the unchanged SIT main.py as __main__ (cwd = SIT checkout).

The release seeds nothing; SIA draws block splits, operations, shifts, scales, noise and
dropout masks from numpy and torch RNGs.
"""
import random
import runpy
import sys

if __name__ == "__main__":
    import numpy as np
    import torch

    seed = int(sys.argv[1])
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    sys.path.insert(0, ".")
    sys.argv = ["main.py", *sys.argv[2:]]
    runpy.run_path("main.py", run_name="__main__")
