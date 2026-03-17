"""Luxonis U2IF package.

This package provides simple access to Luxonis u2if based devices and simple library for u2if protocol itself
"""

from .controller_box import ControllerBox
from .rp2040_u2if import RP2040_u2if

__all__ = ["ControllerBox", "RP2040_u2if"]
__version__ = "0.0.1"
