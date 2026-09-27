"""Restore numpy.int (removed in NumPy 1.24) and run the unchanged rap_attack.py as __main__.

rap_attack.py seeds torch and numpy itself from --seed; nothing else is changed.
"""
import runpy
import sys

if __name__ == "__main__":
    import numpy as np

    if not hasattr(np, "int"):
        np.int = int
    script = sys.argv[1]
    sys.argv = ["rap_attack.py", *sys.argv[2:]]
    runpy.run_path(script, run_name="__main__")
