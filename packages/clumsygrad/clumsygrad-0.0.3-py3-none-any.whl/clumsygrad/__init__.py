"""
ClumsyGrad: A simple automatic differentiation library built on top of NumPy.

This library provides a basic tensor class with support for gradient tracking, building computational graphs,
and performing backpropagation through various tensor operations.
"""

from . import tensor
from . import grad
from . import activation
from . import types
from . import optimizer
from . import loss
from . import random
from . import math

__version__ = "0.0.3"

__all__ = [
    "tensor",
    "grad",
    "activation",
    "types",
    "optimizer",
    "loss",
    "random",
    "math",
    "__version__"
]