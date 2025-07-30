# pyexops/src/pyexops/__init__.py

# This file makes 'pyexops' a Python package and exposes its main components
# for easier import (e.g., 'from pyexops import Star').

from .star import Star, Spot
from .planet import Planet
from .scene import Scene
from .photometer import Photometer
from .simulator import TransitSimulator
from .exovisualizer import ExoVisualizer
from .orbital_solver import OrbitalSolver 

# Optionally, define what gets imported when someone does `from pyexops import *`
# This is generally discouraged, but if used, explicitly list the public API.
__all__ = [
    "Star",
    "Spot",
    "Planet",
    "Scene",
    "Photometer",
    "TransitSimulator",
    "ExoVisualizer",
    "OrbitalSolver", # Add OrbitalSolver to __all__
]

__version__ = "0.1.13"
