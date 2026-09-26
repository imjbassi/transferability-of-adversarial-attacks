"""Seed RNGs, then execute the unchanged released attack.py as __main__ (cwd = SSA checkout)."""
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
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    sys.path.insert(0, ".")
    sys.argv = ["attack.py", *sys.argv[2:]]
    runpy.run_path("attack.py", run_name="__main__")
