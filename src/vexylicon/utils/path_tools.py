#!/usr/bin/env -S uv run -s
# this_file: src/vexylicon/utils/path_tools.py
"""SVG path manipulation and interpolation utilities.

This module provides tools for working with SVG paths, including:
- Path parsing and analysis
- Contour splitting and alignment
- Path interpolation for bevel generation
- Coordinate rounding and precision control
"""

from __future__ import annotations

import re
from typing import List, Tuple

from svgpathtools import CubicBezier, Line, Path, parse_path


def path_bbox(d: str) -> Tuple[float, float]:
    """Return (width, height) of the path bounding box.
    
    Args:
        d: SVG path data string
        
    Returns:
        Tuple of (width, height) of the bounding box
    """
    p = parse_path(d)
    xmin, xmax, ymin, ymax = p.bbox()
    return xmax - xmin, ymax - ymin


def interpolate_segment(a, b, t: float):
    """Interpolate between two path segments (CubicBezier or Line).
    
    Args:
        a: First segment (source)
        b: Second segment (target)
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated segment of the same type
        
    Raises:
        TypeError: If segment type is not supported
    """
    if isinstance(a, CubicBezier):
        return CubicBezier(
            a.start * (1 - t) + b.start * t,
            a.control1 * (1 - t) + b.control1 * t,
            a.control2 * (1 - t) + b.control2 * t,
            a.end * (1 - t) + b.end * t,
        )
    if isinstance(a, Line):
        return Line(
            a.start * (1 - t) + b.start * t,
            a.end * (1 - t) + b.end * t
        )
    raise TypeError(f"Unsupported segment type {type(a).__name__}")


def to_cubic_list(path: Path) -> List[CubicBezier]:
    """Convert all segments to CubicBezier representation.
    
    Lines are converted to degenerate cubic beziers with control points on the line.
    
    Args:
        path: SVG path object
        
    Returns:
        List of CubicBezier segments
        
    Raises:
        TypeError: If path contains unsupported segment types
    """
    segs = []
    for seg in path:
        if isinstance(seg, Line):
            # Represent line as a degenerate cubic (ctrl points on line)
            segs.append(CubicBezier(seg.start, seg.start, seg.end, seg.end))
        elif isinstance(seg, CubicBezier):
            segs.append(seg)
        else:
            raise TypeError(
                "Unsupported segment type in path; please flatten arcs first"
            )
    return segs


def parse_dual_contour_path(d: str) -> Tuple[str, str]:
    """Split a path with two contours (separated by Z M or M commands).
    
    This function handles SVG paths that contain exactly two contours,
    typically representing outer and inner boundaries of a shape.
    
    Args:
        d: SVG path data string with two contours
        
    Returns:
        Tuple of (outer_contour, inner_contour) path strings
        
    Raises:
        ValueError: If path doesn't contain exactly two contours
    """
    # Handle both " Z M " and " M " separations
    if " Z M " in d:
        parts = d.split(" Z M ")
        if len(parts) == 2:
            inner_contour = parts[0].strip() + " Z"
            outer_contour = "M " + parts[1].strip()
            return outer_contour, inner_contour

    # Fallback to original " M " splitting
    parts = d.split(" M ")
    
    if len(parts) != 2:
        raise ValueError(
            f"Expected exactly 2 contours (M commands), got {len(parts)}"
        )
    
    # parts[0] is actually the inner contour, parts[1] is the outer contour
    inner_contour = parts[0].strip()
    outer_contour = "M " + parts[1].strip()
    
    return outer_contour, inner_contour


def round_svg_coordinates(d_string: str, precision: int = 2) -> str:
    """Round all numeric coordinates in SVG path string to specified precision.
    
    This helps avoid precision artifacts in generated paths.
    
    Args:
        d_string: SVG path data string
        precision: Number of decimal places (default: 2)
        
    Returns:
        Path string with rounded coordinates
    """
    def round_match(match):
        return str(round(float(match.group()), precision))
    
    # Match floating point numbers (including scientific notation)
    return re.sub(r"-?\d+\.?\d*(?:[eE][+-]?\d+)?", round_match, d_string)


def align_path_start(p_outer: Path, p_inner: Path) -> Path:
    """Rotate p_outer so that its first point is closest to p_inner[0].start.
    
    This alignment prevents twisted interpolation between paths.
    
    Args:
        p_outer: Outer path to align
        p_inner: Inner path to align to
        
    Returns:
        Rotated outer path with optimal alignment
    """
    target = p_inner[0].start
    # Find segment whose start-point is nearest to target
    idx = min(range(len(p_outer)), key=lambda i: abs(p_outer[i].start - target))
    # Rotate segments to start from that index
    segs = list(p_outer[idx:]) + list(p_outer[:idx])
    return Path(*segs)


def generate_ring_paths(
    outer_contour: str, 
    inner_contour: str, 
    steps: int
) -> List[str]:
    """Generate intermediate ring paths by interpolating between contours.
    
    Creates a series of progressively thinner rings by pushing the inner
    contour outward toward the outer contour.
    
    Args:
        outer_contour: SVG path string for outer boundary
        inner_contour: SVG path string for inner boundary
        steps: Number of intermediate rings to generate
        
    Returns:
        List of SVG path strings for the interpolated rings
        
    Raises:
        ValueError: If contours have incompatible segment counts
    """
    # Parse both contours into Paths
    outer_path = parse_path(outer_contour)
    inner_path = parse_path(inner_contour)
    
    # Reverse outer contour for correspondence
    outer_path_rev = outer_path.reversed()
    
    # Align start points to prevent twisted interpolation
    outer_path_rev = align_path_start(outer_path_rev, inner_path)
    
    p_outer = to_cubic_list(outer_path_rev)
    p_inner = to_cubic_list(inner_path)
    
    if len(p_outer) != len(p_inner):
        raise ValueError(
            "Outer and inner contours have incompatible segment counts"
        )
    
    t_vals = [(i + 1) / (steps + 1) for i in range(steps)]
    d_list: List[str] = []
    
    for t in t_vals:
        # Interpolate inner contour ’ aligned reversed outer contour
        # This makes inner contour move outward toward fixed outer contour
        inter_segs = [
            interpolate_segment(s_in, s_out, t) 
            for s_in, s_out in zip(p_inner, p_outer)
        ]
        
        ring_inner = Path(*inter_segs)
        # Round coordinates to 2 decimal places to avoid precision artifacts
        ring_inner_d = round_svg_coordinates(ring_inner.d())
        outer_d = round_svg_coordinates(outer_path.d())
        combined_d = f"{outer_d} M {ring_inner_d[2:]}"
        d_list.append(combined_d)
    
    return d_list