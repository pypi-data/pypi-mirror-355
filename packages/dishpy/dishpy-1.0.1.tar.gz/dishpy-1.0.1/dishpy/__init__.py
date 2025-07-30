"""
DishPy - A Python development tool for VEX Competition robotics.

This package provides tools for developing VEX Competition robotics programs
in Python, including project initialization, code amalgamation, and upload
to VEX V5 brains.
"""

__version__ = "1.0.1"
__author__ = "Aadish V"
__email__ = "aadish@ohs.stanford.edu"

# Make main functions and classes available at package level
from .main import main, Cli, Project

__all__ = [
    "main",
    "Cli",
    "Project",
    "__version__",
]
