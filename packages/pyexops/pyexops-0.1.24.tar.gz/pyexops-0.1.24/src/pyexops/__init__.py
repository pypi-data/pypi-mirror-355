# pyexops/src/pyexops/__init__.py

# This file makes 'pyexops' a Python package and exposes its main components
# for easier import (e.g., 'from pyexops import Star').

# For type hinting specific collections
from typing import List, Tuple, Optional, Union, Dict

from .star import Star, Spot
from .planet import Planet
from .atmosphere import Atmosphere
from .scene import Scene
from .photometer import Photometer
from .simulator import TransitSimulator
from .visualizer import ExoVisualizer
from .orbital_solver import OrbitalSolver 

# Optionally, define what gets imported when someone does `from pyexops import *`
# This is generally discouraged, but if used, explicitly list the public API.
__all__ = [
    "Star",
    "Spot",
    "Planet",
    "Atmosphere",
    "Scene",
    "Photometer",
    "TransitSimulator",
    "ExoVisualizer",
    "OrbitalSolver", 
]

__version__ = "0.1.24"
