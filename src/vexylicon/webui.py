#!/usr/bin/env -S uv run -s
# this_file: src/vexylicon/webui.py
"""Tiny adapter so web UIs don't import CLI modules."""

from __future__ import annotations

from io import BytesIO

from vexylicon import VexyliconGenerator, VexyliconParams


def generate_svg(
    payload: bytes | None,
    steps: int = 24,
    quality: str | None = None,
    theme: str = "default",
) -> str:
    """Return a liquid-glass SVG.

    Args:
        payload: Raw bytes of an uploaded SVG or ``None``
        steps: Bevel steps
        quality: Preset name or ``None``
        theme: Theme to apply

    Returns:
        SVG as text
    """
    p = VexyliconParams(steps=steps, quality=quality)
    gen = VexyliconGenerator(theme=theme, params=p)

    in_svg: str | None = None
    if payload:
        in_svg = BytesIO(payload).getvalue().decode()

    return gen.generate(payload_svg=in_svg)
