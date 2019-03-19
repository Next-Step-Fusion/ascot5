"""
Methods to evaluate quantities from MHD data.

File: libmhd.py
"""
import numpy as np

from a5py.ascotpy.libascot import LibAscot


import importlib.util as util

plt = util.find_spec("matplotlib")
if plt:
    import matplotlib.pyplot as plt

class LibMhd(LibAscot):

    quantities = ["br", "bphi", "bz","er", "ephi", "ez"]

    def evaluate(self, R, phi, z, t, quantity):

        out = None
        if quantity in ["br", "bphi", "bz", "er", "ephi", "ez"]:
            out = self.eval_mhd(R, phi, z, t)[quantity]

        assert out is not None, "Unknown quantity"

        return out
