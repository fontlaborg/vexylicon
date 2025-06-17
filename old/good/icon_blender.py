#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["svgpathtools", "rich"]
# ///
# this_file: icon_blender.py
"""CLI that creates progressively thinner ring shapes from a dual-contour path.

The script works with SVGs containing a path with two contours (separated by M):
- First contour: outer edge (stays fixed)
- Second contour: inner edge (interpolates outward toward outer edge)

Steps performed
---------------
1. Parse the input SVG and locate the outer path with dual contours.
2. Split the path into outer and inner contours.
3. Generate *N* ring paths by interpolating the inner contour toward the outer.
4. Insert rings as <g id="bevelSteps"> creating progressively thinner bevels.
5. Write the modified SVG to the requested output file.

Usage::

    python icon_blender.py \
        --input_svg icon-work1.svg \
        --output_svg icon-o3X.svg \
        --steps 23

You can then rasterise and compare as usual.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path as FsPath
from typing import List, Tuple

from rich import print
from svgpathtools import (  # type: ignore
    CubicBezier,
    Line,
    Path,
    parse_path,
)

# --------------------------------------------------------------------------------------
# Utility functions --------------------------------------------------------------------
# --------------------------------------------------------------------------------------


def path_bbox(d: str) -> Tuple[float, float]:
    """Return (width, height) of the path bounding box.

"""
    p = parse_path(d)
    xmin, xmax, ymin, ymax = p.bbox()
    return xmax - xmin, ymax - ymin


def interpolate_segment(a, b, t):
    """Interpolate between two path segments (CubicBezier or Line).

"""
    if isinstance(a, CubicBezier):
        # CubicBezier is not iterable by default (for type checker), interpolate manually
        return CubicBezier(  # type: ignore[arg-type]
            a.start * (1 - t) + b.start * t,
            a.control1 * (1 - t) + b.control1 * t,
            a.control2 * (1 - t) + b.control2 * t,
            a.end * (1 - t) + b.end * t,
        )
    if isinstance(a, Line):
        return Line(a.start * (1 - t) + b.start * t, a.end * (1 - t) + b.end * t)
    raise TypeError(f"Unsupported segment type {type(a).__name__}")


def to_cubic_list(path: Path) -> List[CubicBezier]:
    """Return segments where Lines stay lines, CubicBezier unchanged.

"""
    segs = []
    for seg in path:
        if isinstance(seg, Line):
            # Represent line as a degenerate cubic (ctrl points on line)
            segs.append(CubicBezier(seg.start, seg.start, seg.end, seg.end))
        elif isinstance(seg, CubicBezier):
            segs.append(seg)
        else:
            raise TypeError("Unsupported segment type in path; please flatten arcs first")
    return segs


def parse_dual_contour_path(d: str) -> Tuple[str, str]:
    """Split a path with two contours (separated by Z M or M commands).

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
        sys.exit(f"[red]Error:[/] Expected exactly 2 contours (M commands), got {len(parts)}")

    # parts[0] is actually the inner contour, parts[1] is the outer contour
    inner_contour = parts[0].strip()
    outer_contour = "M " + parts[1].strip()

    return outer_contour, inner_contour


def get_path_data_from_element(elem: ET.Element, tree: ET.ElementTree) -> str:
    """Extract path data from either a <path> element or a <use> element that references a path.

"""
    if elem.tag.endswith("path"):
        return elem.get("d", "")
    elif elem.tag.endswith("use"):
        # Get the href attribute (with or without namespace)
        href = elem.get("href") or elem.get("{http://www.w3.org/1999/xlink}href", "")
        if href.startswith("#"):
            # Find the referenced element in defs
            ref_id = href[1:]  # Remove the #
            ns_path = ".//{http://www.w3.org/2000/svg}path"
            ref_elem = tree.find(f"{ns_path}[@id='{ref_id}']")
            if ref_elem is not None:
                return ref_elem.get("d", "")
    return ""


def round_svg_coordinates(d_string: str, precision: int = 2) -> str:
    """Round all numeric coordinates in SVG path string to specified precision.

"""
    import re

    def round_match(match):
        """"""
        return str(round(float(match.group()), precision))

    # Match floating point numbers (including scientific notation)
    return re.sub(r"-?\d+\.?\d*(?:[eE][+-]?\d+)?", round_match, d_string)


def align_path_start(p_outer: Path, p_inner: Path) -> Path:
    """Rotate p_outer so that its first point is closest to p_inner[0].start.

"""
    target = p_inner[0].start
    # Find segment whose start-point is nearest to target
    idx = min(range(len(p_outer)), key=lambda i: abs(p_outer[i].start - target))
    # Rotate segments to start from that index
    segs = list(p_outer[idx:]) + list(p_outer[:idx])
    return Path(*segs)


def generate_ring_paths(outer_contour: str, inner_contour: str, steps: int) -> List[str]:
    """Generate *steps* rings by pushing the inner contour outward.

    The outer contour is first reversed to align its vertex ordering with the
    inner contour so that point-wise interpolation makes sense.

    """
    # Parse both contours into Paths
    outer_path = parse_path(outer_contour)
    inner_path = parse_path(inner_contour)

    # Reverse *a copy* of the outer contour for correspondence
    outer_path_rev = outer_path.reversed()

    # Align start points to prevent twisted interpolation
    outer_path_rev = align_path_start(outer_path_rev, inner_path)

    p_outer = to_cubic_list(outer_path_rev)
    p_inner = to_cubic_list(inner_path)

    if len(p_outer) != len(p_inner):
        sys.exit("[red]Error:[/] outer and inner contours have incompatible segment counts")

    t_vals = [(i + 1) / (steps + 1) for i in range(steps)]
    d_list: List[str] = []

    for t in t_vals:
        # Interpolate inner contour → aligned reversed outer contour
        # This makes inner contour move outward toward fixed outer contour
        inter_segs = [interpolate_segment(s_in, s_out, t) for s_in, s_out in zip(p_inner, p_outer)]

        ring_inner = Path(*inter_segs)
        # Round coordinates to 2 decimal places to avoid precision artifacts
        ring_inner_d = round_svg_coordinates(ring_inner.d())
        outer_d = round_svg_coordinates(outer_path.d())
        combined_d = f"{outer_d} M {ring_inner_d[2:]}"
        d_list.append(combined_d)

    return d_list


# --------------------------------------------------------------------------------------
# Main logic ---------------------------------------------------------------------------
# --------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """"""
    p = argparse.ArgumentParser(
        description="Insert blended bevel steps into the SVG icon",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input_svg", required=True, help="Source SVG file")
    p.add_argument("--output_svg", required=True, help="Destination SVG file")
    p.add_argument("--steps", type=int, default=23, help="Number of steps")
    p.add_argument(
        "--gradient_id",
        default="baseFill",
        help="Gradient id for the generated fill attribute (ignored in glass mode)",
    )
    p.add_argument(
        "--canvas_fill",
        default="none",
        help="Canvas background fill (color or 'none' to disable)",
    )
    p.add_argument(
        "--back_fill",
        default="url(#baseFill)",
        help="Back layer fill (gradient/color or 'none' to disable)",
    )
    p.add_argument(
        "--border_fill",
        default="none",
        help="Border fill (color or 'none' to disable)",
    )
    p.add_argument(
        "--opacity_start",
        type=float,
        default=0.9,
        help="Fill opacity for step nearest the inner rectangle (normal mode) or outer (glass mode)",
    )
    p.add_argument(
        "--opacity_end",
        type=float,
        default=0.05,
        help="Fill opacity for step nearest the outer rectangle (normal mode) or inner (glass mode)",
    )
    p.add_argument(
        "--outer_id",
        default="outer",
        help="id attribute of the outer path element (if present)",
    )
    p.add_argument(
        "--inner_id",
        default="inner",
        help="id attribute of the inner path element (if present)",
    )
    p.add_argument(
        "--glass_mode",
        action="store_true",
        help="Enable glass effect mode: use white fills, reverse opacity (bright edges), add blend modes",
    )
    p.add_argument(
        "--opacity_progression",
        type=int,
        choices=[1, 2, 3, 4],
        default=4,
        help="Opacity progression: 1=decreasing, 2=linear, 3=exponential, 4=more exponential",
    )
    return p


def locate_paths(
    tree: ET.ElementTree,
    outer_id: str = "outer",
    inner_id: str = "inner",
    small_id: str = "small",
) -> Tuple[ET.Element, ET.Element, ET.Element | None]:
    """Return (outer, inner) path elements.

    Strategy:
    1. Try to find paths with given id attributes.
    2. Fallback to area-based detection (largest two paths).

    """
    ns_path = ".//{http://www.w3.org/2000/svg}path"
    # Try ID-based lookup first - check both path and use elements
    ns_use = ".//{http://www.w3.org/2000/svg}use"
    outer_elem = tree.find(f"{ns_path}[@id='{outer_id}']") or tree.find(f"{ns_use}[@id='{outer_id}']")
    inner_elem = tree.find(f"{ns_path}[@id='{inner_id}']") or tree.find(f"{ns_use}[@id='{inner_id}']")
    small_elem = tree.find(f"{ns_path}[@id='{small_id}']") or tree.find(f"{ns_use}[@id='{small_id}']")

    if outer_elem is not None:
        # If outer found but no separate inner, use outer for both (dual contour case)
        if inner_elem is None:
            return outer_elem, outer_elem, small_elem
        else:
            return outer_elem, inner_elem, small_elem

    # Fallback to area heuristic
    paths = tree.findall(ns_path)
    if len(paths) < 2:
        sys.exit("[red]Error:[/] SVG must contain at least two <path> elements")

    sizes = []
    for elem in paths:
        d = elem.get("d", "")
        if not d:
            continue
        w, h = path_bbox(d)
        sizes.append((w * h, elem))

    if len(sizes) < 2:
        sys.exit("[red]Error:[/] Could not determine outer/inner paths")

    sizes.sort(key=lambda t: t[0], reverse=True)
    return sizes[0][1], sizes[1][1], None


def main() -> None:
    """Used in:
    - old/older/icon_masker.py

    Used in:
    - old/older/icon_masker.py
    """
    args = build_parser().parse_args()

    tree = ET.parse(args.input_svg)
    root = tree.getroot()

    outer_path, inner_path, small_path = locate_paths(tree, args.outer_id, args.inner_id)

    print("[green]Identified outer path with dual contours")

    # Parse the dual-contour outer path (handles both <path> and <use> elements)
    outer_d = get_path_data_from_element(outer_path, tree)
    if not outer_d:
        sys.exit("[red]Error:[/] Outer path has no 'd' attribute or referenced path")

    outer_contour, inner_contour = parse_dual_contour_path(outer_d)
    print(f"[blue]Split into outer and inner contours")

    # Control canvas, back, and border fills
    canvas_elem = root.find(".//{http://www.w3.org/2000/svg}rect[@id='canvas']")
    if canvas_elem is None:
        canvas_elem = root.find(".//{http://www.w3.org/2000/svg}path[@id='canvas']")

    back_elem = root.find(".//{http://www.w3.org/2000/svg}use[@id='back']")
    if back_elem is None:
        back_elem = root.find(".//{http://www.w3.org/2000/svg}path[@id='back']")

    border_elem = root.find(".//{http://www.w3.org/2000/svg}use[@id='border']")
    if border_elem is None:
        border_elem = root.find(".//{http://www.w3.org/2000/svg}path[@id='border']")

    if canvas_elem is not None:
        if args.canvas_fill.lower() == "none":
            # Find parent and remove canvas
            for parent in root.iter():
                if canvas_elem in parent:
                    parent.remove(canvas_elem)
                    break
            print("[yellow]Removed canvas background")
        else:
            canvas_elem.set("fill", args.canvas_fill)
            print(f"[blue]Set canvas fill to {args.canvas_fill}")

    if back_elem is not None:
        if args.back_fill.lower() == "none":
            # Find parent and remove back
            for parent in root.iter():
                if back_elem in parent:
                    parent.remove(back_elem)
                    break
            print("[yellow]Removed back layer")
        else:
            back_elem.set("fill", args.back_fill)
            print(f"[blue]Set back fill to {args.back_fill}")

    if border_elem is not None:
        if args.border_fill.lower() == "none":
            # Find parent and remove border
            for parent in root.iter():
                if border_elem in parent:
                    parent.remove(border_elem)
                    break
            print("[yellow]Removed border layer")
        else:
            border_elem.set("fill", args.border_fill)
            print(f"[blue]Set border fill to {args.border_fill}")

    d_steps = generate_ring_paths(outer_contour, inner_contour, args.steps)

    # Build group element
    ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", ns)
    g = ET.Element("{%s}g" % ns, attrib={"id": "bevelSteps"})

    # New opacity logic: split full range (0→1) into steps+1 divisions
    # Thinner rings (more interpolated) get higher opacity
    # Original ring (thickest) gets lowest opacity: 1/(steps+1)
    # Thinnest ring gets highest opacity: steps+1/(steps+1) = 1.0

    # Apply minimal opacity to the original outer path
    min_opacity = 1 / (args.steps + 1)
    outer_path.set("fill-opacity", f"{min_opacity:.3f}")
    print(f"[blue]Applied opacity {min_opacity:.3f} to outer path")

    # Calculate opacity progression based on selected mode
    op_vals = []
    progression_names = {
        1: "decreasing",
        2: "linear",
        3: "exponential",
        4: "more exponential",
    }

    for i in range(args.steps):
        t = (i + 1) / args.steps  # Linear parameter from 1/steps to 1

        if args.opacity_progression == 1:
            # Decreasing: start high, end low (reverse of exponential)
            opacity = min_opacity + (1.0 - min_opacity) * (1 - t**2)
        elif args.opacity_progression == 2:
            # Linear: uniform progression
            opacity = min_opacity + (1.0 - min_opacity) * t
        elif args.opacity_progression == 3:
            # Exponential: quadratic acceleration
            opacity = min_opacity + (1.0 - min_opacity) * (t**2)
        elif args.opacity_progression == 4:
            # More exponential: quartic acceleration
            opacity = min_opacity + (1.0 - min_opacity) * (t**4)
        else:
            # Default to more exponential if invalid value
            opacity = min_opacity + (1.0 - min_opacity) * (t**4)

        op_vals.append(opacity)

    prog_name = progression_names[args.opacity_progression]
    print(f"[blue]{prog_name.title()} bevel opacity: {op_vals[0]:.3f} → {op_vals[-1]:.3f}")

    if args.glass_mode:
        print("[blue]Glass mode: using blend modes for transparency effect")

    # Get the fill from the outer path to use for all bevel steps
    outer_fill = outer_path.get("fill", f"url(#{args.gradient_id})")

    for i, (d_str, op) in enumerate(zip(d_steps, op_vals), 1):
        sub = ET.SubElement(g, "{%s}path" % ns)
        sub.set("d", d_str)
        sub.set("id", f"bevelStep-{i}")

        # Use the same fill as the outer path
        sub.set("fill", outer_fill)

        if args.glass_mode:
            # Glass mode: add blend mode for glass effect
            sub.set("mix-blend-mode", "screen")

        sub.set("fill-opacity", f"{op:.3f}")
        sub.set("pointer-events", "none")

    # Insert g before inner_path element in its parent
    parent = None
    for p_elem in root.iter():
        if inner_path in list(p_elem):
            parent = p_elem
            break
    if parent is None:
        sys.exit("[red]Error:[/] Could not locate parent of inner path")

    idx = list(parent).index(inner_path)
    parent.insert(idx, g)

    # Process small path if it exists and has dual contours
    if small_path is not None:
        small_d = get_path_data_from_element(small_path, tree)
        if small_d and " M " in small_d:
            print("[green]Processing small path with dual contours")

            # Apply minimal opacity to small path
            small_path.set("fill-opacity", f"{min_opacity:.3f}")
            print(f"[blue]Applied opacity {min_opacity:.3f} to small path")

            # Parse dual contours for small path
            small_outer_contour, small_inner_contour = parse_dual_contour_path(small_d)
            small_d_steps = generate_ring_paths(small_outer_contour, small_inner_contour, args.steps)

            # Create bevel group for small path
            small_g = ET.Element("{%s}g" % ns, attrib={"id": "smallBevelSteps"})

            # Get the fill from the small path
            small_fill = small_path.get("fill", f"url(#{args.gradient_id})")

            for i, (d_str, op) in enumerate(zip(small_d_steps, op_vals), 1):
                sub = ET.SubElement(small_g, "{%s}path" % ns)
                sub.set("d", d_str)
                sub.set("id", f"smallBevelStep-{i}")
                sub.set("fill", small_fill)

                if args.glass_mode:
                    sub.set("mix-blend-mode", "screen")

                sub.set("fill-opacity", f"{op:.3f}")
                sub.set("pointer-events", "none")

            # Insert small bevel group before small path
            small_parent = None
            for p_elem in root.iter():
                if small_path in list(p_elem):
                    small_parent = p_elem
                    break
            if small_parent is not None:
                small_idx = list(small_parent).index(small_path)
                small_parent.insert(small_idx, small_g)
                print(f"[blue]Added {args.steps} bevel steps for small path")
        else:
            print("[yellow]Small path found but no dual contours - skipping")

    FsPath(args.output_svg).write_text(ET.tostring(root, encoding="unicode"), encoding="utf-8")
    mode_desc = "glass-effect" if args.glass_mode else "normal"
    print(f"[bold green]Wrote {mode_desc} blended SVG → {args.output_svg}")


if __name__ == "__main__":
    main()
