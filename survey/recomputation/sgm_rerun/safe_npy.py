"""Load the release's imagenet_class_to_idx.npy without executing arbitrary pickle code."""
import pickle

from numpy.lib import format as npf

SAFE = {("numpy", "dtype"), ("numpy", "ndarray"), ("numpy.core.multiarray", "_reconstruct"),
        ("numpy._core.multiarray", "_reconstruct"), ("_codecs", "encode")}


class _Restricted(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) in SAFE:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"blocked {module}.{name}")


def load_class_to_idx(path):
    with open(path, "rb") as handle:
        version = npf.read_magic(handle)
        (npf.read_array_header_1_0 if version == (1, 0) else npf.read_array_header_2_0)(handle)
        mapping = _Restricted(handle, encoding="latin1").load().item()
    if not isinstance(mapping, dict) or sorted(mapping.values()) != list(range(1000)):
        raise ValueError("unexpected class_to_idx payload")
    return mapping
