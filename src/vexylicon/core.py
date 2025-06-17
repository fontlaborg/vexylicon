#!/usr/bin/env -S uv run -s
# this_file: src/vexylicon/core.py
"""Core Vexylicon functionality.

This module provides the main VexyliconGenerator class that orchestrates
the creation of liquid-glass SVG effects with theme support.
"""

from __future__ import annotations

import importlib.resources
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

from lxml import etree

from vexylicon.utils import (
    SVGProcessor,
    Theme,
    ThemeLoader,
    generate_ring_paths,
    parse_dual_contour_path,
)


class OpacityProgression(IntEnum):
    """Opacity progression modes for bevel steps."""

    LINEAR = 1
    DECREASING = 2
    EXPONENTIAL = 3
    MORE_EXPONENTIAL = 4


@dataclass
class VexyliconParams:
    """Parameters for Vexylicon generation.

    Attributes:
        steps: Number of bevel steps to generate (default: 24)
        opacity_start: Starting opacity for bevel (default: 0.9)
        opacity_end: Ending opacity for bevel (default: 0.05)
        opacity_progression: How opacity changes across steps (default: MORE_EXPONENTIAL)
        quality: Preset quality level ('low', 'medium', 'high')
    """

    steps: int = 24
    opacity_start: float = 0.9
    opacity_end: float = 0.05
    opacity_progression: OpacityProgression = OpacityProgression.MORE_EXPONENTIAL
    quality: str | None = None

    def __post_init__(self):
        """Apply quality presets if specified."""
        if self.quality:
            quality_presets = {"low": 8, "medium": 16, "high": 24, "ultra": 32}
            if self.quality in quality_presets:
                self.steps = quality_presets[self.quality]


class VexyliconError(Exception):
    """Base exception for Vexylicon errors."""


class InvalidSVGError(VexyliconError):
    """Raised when input SVG is malformed or incompatible."""


class ThemeValidationError(VexyliconError):
    """Raised when theme JSON is invalid."""


class VexyliconGenerator:
    """Main class for generating liquid-glass SVG effects."""

    def __init__(self, theme: Theme | str = "default", params: VexyliconParams | None = None):
        """Initialize generator with theme and parameters.

        Args:
            theme: Theme object or name of built-in theme
            params: Generation parameters (uses defaults if None)
        """
        self.params = params or VexyliconParams()

        # Load theme if string provided
        if isinstance(theme, str):
            loader = ThemeLoader()
            self.theme = loader.load_theme(theme)
        else:
            self.theme = theme

        # Load base SVG from package assets
        base_svg_path = importlib.resources.files("vexylicon.assets") / "best_base.svg"
        self.base_svg_content = base_svg_path.read_text()

    def generate(self, payload_svg: Path | str | None = None) -> str:
        """Generate liquid-glass SVG with optional payload.

        Args:
            payload_svg: Path to payload SVG or SVG content string

        Returns:
            Generated SVG as string

        Raises:
            InvalidSVGError: If base or payload SVG is invalid
            VexyliconError: For other generation errors
        """
        # Parse base SVG
        try:
            processor = SVGProcessor(self.base_svg_content)
        except etree.XMLSyntaxError as e:
            msg = f"Base SVG is malformed: {e}"
            raise InvalidSVGError(msg) from e

        # Generate bevel steps
        self._generate_bevel_steps(processor)

        # Apply theme
        self._apply_theme(processor)

        # Create theme-aware groups
        self._create_theme_groups(processor)

        # Add payload if provided
        if payload_svg:
            self._inject_payload(processor, payload_svg)

        return processor.to_string()

    def _generate_bevel_steps(self, processor: SVGProcessor) -> None:
        """Generate the bevel step paths.

        Args:
            processor: SVG processor instance

        Raises:
            InvalidSVGError: If required paths not found
        """
        # Find the main shape with dual contours
        main_shape = processor.find_by_id("mainShape")
        if main_shape is None:
            # Fallback to finding by tag
            paths = processor.find_all("path")
            if not paths:
                msg = "No paths found in base SVG"
                raise InvalidSVGError(msg)
            main_shape = paths[0]  # Assume first path is main

        # Get path data
        path_data = processor.get_path_data(main_shape)
        if not path_data:
            msg = "Main shape has no path data"
            raise InvalidSVGError(msg)

        try:
            outer_contour, inner_contour = parse_dual_contour_path(path_data)
        except ValueError as e:
            msg = f"Failed to parse dual contours: {e}"
            raise InvalidSVGError(msg) from e

        # Generate ring paths
        ring_paths = generate_ring_paths(outer_contour, inner_contour, self.params.steps)

        # Ensure an <path id="inner"> exists for clipping masks
        if processor.find_by_id("inner") is None:
            inner_path_elem = processor.create_element(
                "path",
                id="inner",
                d=inner_contour,
                fill="none",
            )
            processor.get_defs().append(inner_path_elem)

        # Create bevel steps group
        bevel_group = processor.create_element("g", id="bevelSteps")

        # Calculate opacity values
        opacities = self._calculate_opacities()

        # Locate the rendered <use> element that references the main shape.
        outer_use = processor.find_by_id("outer")

        # Apply the minimal opacity to *both* the rendered <use id="outer">
        # element (if present) and the <path id="mainShape"> definition. This
        # guarantees the bevel rings are not completely covered by an opaque
        # base fill in any renderer.
        target_elem = outer_use or main_shape
        min_opacity = 1 / (self.params.steps + 1)
        target_elem.set("fill-opacity", f"{min_opacity:.3f}")

        if outer_use is not None and outer_use is not main_shape:
            main_shape.set("fill-opacity", f"{min_opacity:.3f}")

        # Create bevel step paths (single set, themeable via gradients)
        for i, (path_d, opacity) in enumerate(zip(ring_paths, opacities, strict=False), 1):
            step = processor.create_element(
                "path",
                d=path_d,
                id=f"bevelStep-{i}",
                fill="url(#edgeGlow)",
                pointer_events="none",
            )
            step.set("fill-opacity", f"{opacity:.3f}")
            step.set("mix-blend-mode", "screen")
            bevel_group.append(step)

        # Insert bevel group into document
        root = processor.root
        root.append(bevel_group)

    def _calculate_opacities(self) -> list[float]:
        """Calculate opacity values for each bevel step.

        Returns:
            List of opacity values
        """
        opacities = []
        min_opacity = 1 / (self.params.steps + 1)

        for i in range(self.params.steps):
            t = (i + 1) / self.params.steps  # Linear parameter

            if self.params.opacity_progression == OpacityProgression.LINEAR:
                opacity = min_opacity + (1.0 - min_opacity) * t
            elif self.params.opacity_progression == OpacityProgression.DECREASING:
                opacity = min_opacity + (1.0 - min_opacity) * (1 - t**2)
            elif self.params.opacity_progression == OpacityProgression.EXPONENTIAL:
                opacity = min_opacity + (1.0 - min_opacity) * (t**2)
            elif self.params.opacity_progression == OpacityProgression.MORE_EXPONENTIAL:
                opacity = min_opacity + (1.0 - min_opacity) * (t**4)
            else:
                # Default to more exponential
                opacity = min_opacity + (1.0 - min_opacity) * (t**4)

            opacities.append(opacity)

        return opacities

    def _apply_theme(self, processor: SVGProcessor) -> None:
        """Apply theme gradients and colors to the SVG.

        Args:
            processor: SVG processor instance
        """
        # Add gradients defined in the theme as-is (no light/dark duplication)
        for gradient_name, gradient_def in self.theme.gradients.items():
            if gradient_def["type"] == "linear":
                processor.add_gradient(
                    "linear",
                    gradient_name,
                    gradient_def["stops"],
                    x1=gradient_def["x1"],
                    y1=gradient_def["y1"],
                    x2=gradient_def["x2"],
                    y2=gradient_def["y2"],
                )
            elif gradient_def["type"] == "radial":
                processor.add_gradient(
                    "radial",
                    gradient_name,
                    gradient_def["stops"],
                    cx=gradient_def["cx"],
                    cy=gradient_def["cy"],
                    r=gradient_def["r"],
                )

        # Apply theme colors
        canvas = processor.find_by_id("canvas")
        if canvas is not None:
            canvas.set("fill", self.theme.colors.canvas)

        border = processor.find_by_id("border")
        if border is not None:
            border.set("fill", self.theme.colors.border)

    def _create_theme_groups(self, processor: SVGProcessor) -> None:
        """Create light and dark theme groups.

        Args:
            processor: SVG processor instance
        """
        # Create clip path for payload
        inner_path = processor.find_by_id("inner") or processor.find_by_id("mainShape")
        if inner_path is not None:
            defs = processor.get_defs()
            clip_path = processor.create_element("clipPath", id="innerClip")
            clip_use = processor.create_element("use", href="#inner")
            clip_path.append(clip_use)
            defs.append(clip_path)

    def _inject_payload(self, processor: SVGProcessor, payload_svg: Path | str) -> None:
        """Inject payload SVG into the mask.

        Args:
            processor: SVG processor instance
            payload_svg: Path to payload SVG or SVG content

        Raises:
            InvalidSVGError: If payload SVG is invalid
        """
        # Create payload group
        payload_group = processor.create_element("g", id="payload", clip_path="url(#innerClip)")

        # Parse payload SVG
        try:
            if isinstance(payload_svg, str | Path):
                payload_path = Path(payload_svg) if isinstance(payload_svg, str) else payload_svg
                payload_processor = SVGProcessor(payload_path) if payload_path.exists() else SVGProcessor(payload_svg)
            else:
                payload_processor = SVGProcessor(payload_svg)
        except etree.XMLSyntaxError as e:
            msg = f"Payload SVG is malformed: {e}"
            raise InvalidSVGError(msg) from e

        # Import payload content into main document
        payload_root = payload_processor.root
        for child in list(payload_root):
            # Skip certain elements like defs
            tag = child.tag if isinstance(child.tag, str) else str(child.tag)
            if not tag.endswith("defs"):
                payload_group.append(child)

        # Find back element and inject payload there
        back_elem = processor.find_by_id("back")
        if back_elem is not None:
            parent = back_elem.getparent()
            idx = list(parent).index(back_elem)
            parent.insert(idx + 1, payload_group)
        else:
            # Fallback: append to root
            processor.root.append(payload_group)
