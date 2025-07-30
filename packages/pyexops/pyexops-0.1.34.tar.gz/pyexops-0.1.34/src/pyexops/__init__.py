# pyexops/src/pyexops/__init__.py

# This file makes 'pyexops' a Python package and exposes its main components
# for easier import (e.g., 'from pyexops import Star').

#For type hinting specific collections
from typing import List, Tuple, Optional, Union, Dict 

from .star import Star, Spot # Spot is also a class in star.py
from .planet import Planet
from .atmosphere import Atmosphere 
from .scene import Scene
from .photometer import Photometer
from .simulator import TransitSimulator
from .exovisualizer import ExoVisualizer
from .orbital_solver import OrbitalSolver 
from .astrometry import Astrometry # NEW: Import Astrometry module

# Optionally, define what gets imported when someone does `from pyexops import *`
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
    "Astrometry", # NEW: Add Astrometry to __all__
]

__version__ = "0.1.34" # Updated version
