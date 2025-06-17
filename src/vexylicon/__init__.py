#!/usr/bin/env -S uv run -s
# this_file: src/vexylicon/__init__.py
"""Vexylicon - Create sophisticated liquid-glass SVG icon effects.

This package provides tools to transform simple SVG icons into stunning
glass-morphism designs with beveled edges and dynamic light/dark theme support.
"""

from vexylicon.__version__ import __version__
from vexylicon.core import VexyliconGenerator, VexyliconParams

__all__ = ["VexyliconGenerator", "VexyliconParams", "__version__"]
