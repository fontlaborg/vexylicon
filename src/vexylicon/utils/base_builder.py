#!/usr/bin/env -S uv run -s
# this_file: src/vexylicon/utils/base_builder.py
# ruff: noqa: E501
"""Convert a *single-contour* SVG into a `best_base` dual-contour template.

The emitted SVG keeps the structure of ``assets/best_base.svg``:

* ``borderShape`` – the **outer** contour only.
* ``mainShape``  – **outer + inner** contours.

`VexyliconGenerator` can consume the result without any further changes.

This implementation is dependency-free.  It uses **uniform scaling** to
approximate an inner offset.  A 3 % inset is usually enough for a pleasant
look.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from svgpathtools import CubicBezier, Line, Path as SvgPath, parse_path

from vexylicon.utils import SVGProcessor, round_svg_coordinates

__all__ = ["BaseSVGBuilder"]


class BaseSVGBuilder:  # pylint: disable=too-few-public-methods
    """Create a dual-contour *best_base* SVG from a flat SVG shape.

    Parameters
    ----------
    inset_ratio:
        Ratio of the **shortest** side of the shape's bounding box that should
        be used as the inner offset.  *Default is 3 %* which matches the hand-
        crafted template shipped with Vexylicon.
    """

    def __init__(self, inset_ratio: float = 0.03) -> None:  # noqa: D401
        self.inset_ratio = inset_ratio

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def build(self, source_svg: str | Path | SVGProcessor) -> str:
        """Return the completed *best_base* SVG as a **string**."""
        proc = source_svg if isinstance(source_svg, SVGProcessor) else SVGProcessor(source_svg)

        outer_path = self._extract_first_path(proc)
        inner_path = self._inset_path_uniform_scale(outer_path, self.inset_ratio)

        # Build dual-contour data strings
        outer_d = round_svg_coordinates(outer_path.d())
        inner_d = round_svg_coordinates(inner_path.d())
        # Combine outer and inner contours into one path string
        dual_d = f"{outer_d} M {inner_d[2:]}"

        # Compose final SVG, patching in the new paths
        width, height = self._bbox(outer_path)
        return self._compose_svg(dual_d, outer_d, width, height)

    # ------------------------------------------------------------------
    # Helpers – geometry & path handling
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_first_path(proc: SVGProcessor) -> SvgPath:
        """Return the **first** path element encountered in the SVG.

        Raises
        ------
        ValueError
            If the SVG does not contain any ``<path>`` element.
        """
        for elem in proc.find_all("path"):
            d = proc.get_path_data(elem)
            if d:
                return parse_path(d)
        raise ValueError("No <path> element found in source SVG.")

    @staticmethod
    def _bbox(path: SvgPath) -> Tuple[float, float]:
        xmin, xmax, ymin, ymax = path.bbox()
        return xmax - xmin, ymax - ymin

    # ..................................................................
    #  Very simple inset approximation: uniform scaling
    # ..................................................................
    def _inset_path_uniform_scale(self, path: SvgPath, ratio: float) -> SvgPath:
        """Approximate an inner offset by uniformly scaling the path.

        This is *not* mathematically equivalent to a polygon offset – but it is
        deterministic, dependency-free, and visually adequate for most icons
        with moderate curvature.
        """
        width, height = self._bbox(path)
        if min(width, height) == 0:  # pragma: no cover – degenerate case
            return path.copy()

        inset_dist = ratio * min(width, height)
        # Calculate uniform scale so that both width & height shrink by 2*inset
        scale_x = (width - 2 * inset_dist) / width
        scale_y = (height - 2 * inset_dist) / height
        scale = min(scale_x, scale_y)

        # Centre of the bounding box
        xmin, xmax, ymin, ymax = path.bbox()
        cx = (xmin + xmax) / 2
        cy = (ymin + ymax) / 2
        centre = complex(cx, cy)

        def _scale_point(pt: complex) -> complex:
            return (pt - centre) * scale + centre

        new_segs = []
        for seg in path:
            if isinstance(seg, CubicBezier):
                new_segs.append(
                    CubicBezier(
                        _scale_point(seg.start),
                        _scale_point(seg.control1),
                        _scale_point(seg.control2),
                        _scale_point(seg.end),
                    )
                )
            elif isinstance(seg, Line):
                new_segs.append(Line(_scale_point(seg.start), _scale_point(seg.end)))
            else:  # pragma: no cover – safeguard
                # Fallback: convert segment to line via point sampling
                new_segs.append(Line(_scale_point(seg.start), _scale_point(seg.end)))
        return SvgPath(*new_segs)

    # ------------------------------------------------------------------
    # Output generation – patching template SVG
    # ------------------------------------------------------------------
    def _compose_svg(
        self,
        main_d: str,
        border_d: str,
        width: float,
        height: float,
    ) -> str:
        """Return final SVG text with paths patched into the template."""
        # Locate template relative to project (no importlib.resources needed)
        asset_path = Path(__file__).resolve().parent.parent / "assets" / "best_base.svg"
        template_text = asset_path.read_text(encoding="utf-8")

        proc = SVGProcessor(template_text)

        # Replace path data – fail loudly if template is malformed
        border_elem = proc.find_by_id("borderShape")
        main_elem = proc.find_by_id("mainShape")
        if border_elem is None or main_elem is None:
            msg = "Template SVG is missing expected path IDs"
            raise ValueError(msg)

        border_elem.set("d", border_d)
        main_elem.set("d", main_d)
        # Adjust viewBox / width / height so the canvas fits the new shape
        root = proc.root
        root.set("width", f"{int(width)}")
        root.set("height", f"{int(height)}")
        # Preserve viewBox if present – otherwise create one
        if root.get("viewBox") is None:
            root.set("viewBox", f"0 0 {int(width)} {int(height)}")

        return proc.to_string(pretty_print=True)
