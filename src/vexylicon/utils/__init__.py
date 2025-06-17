#!/usr/bin/env -S uv run -s
# this_file: src/vexylicon/utils/__init__.py
"""Utility modules for Vexylicon."""

from vexylicon.utils.path_tools import (
    align_path_start,
    generate_ring_paths,
    interpolate_segment,
    parse_dual_contour_path,
    path_bbox,
    round_svg_coordinates,
    to_cubic_list,
)
from vexylicon.utils.svg_processor import SVGProcessor
from vexylicon.utils.theme_loader import Theme, ThemeLoader

__all__ = [
    # svg_processor
    "SVGProcessor",
    # theme_loader
    "Theme",
    "ThemeLoader",
    # path_tools
    "align_path_start",
    "generate_ring_paths",
    "interpolate_segment",
    "parse_dual_contour_path",
    "path_bbox",
    "round_svg_coordinates",
    "to_cubic_list",
]
