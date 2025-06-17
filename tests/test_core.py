#!/usr/bin/env -S uv run -s
# this_file: tests/test_core.py
"""Tests for core Vexylicon functionality."""

import pytest

from vexylicon import VexyliconGenerator, VexyliconParams
from vexylicon.core import InvalidSVGError, OpacityProgression


def test_vexylicon_generator_creation():
    """Test basic generator creation."""
    generator = VexyliconGenerator()
    assert generator is not None
    assert generator.theme.name == "default"
    assert generator.params.steps == 24


def test_vexylicon_params():
    """Test parameter configuration."""
    params = VexyliconParams(
        steps=16, opacity_start=0.8, opacity_end=0.1, opacity_progression=OpacityProgression.LINEAR
    )
    assert params.steps == 16
    assert params.opacity_start == 0.8
    assert params.opacity_end == 0.1
    assert params.opacity_progression == OpacityProgression.LINEAR


def test_quality_presets():
    """Test quality preset application."""
    params_low = VexyliconParams(quality="low")
    assert params_low.steps == 8

    params_high = VexyliconParams(quality="high")
    assert params_high.steps == 24

    params_ultra = VexyliconParams(quality="ultra")
    assert params_ultra.steps == 32


def test_basic_generation():
    """Test basic SVG generation without payload."""
    generator = VexyliconGenerator()
    result = generator.generate()

    # Check it's valid SVG
    assert result.startswith("<?xml")
    assert "<svg" in result
    assert "</svg>" in result

    # Check for expected elements
    assert 'id="bevelSteps"' in result
    assert 'mix-blend-mode="screen"' in result


def test_invalid_svg_handling():
    """Test handling of invalid SVG input."""
    generator = VexyliconGenerator()

    # Test with invalid payload
    with pytest.raises(InvalidSVGError):
        generator.generate(payload_svg="<not valid xml>")


def test_opacity_calculation():
    """Test opacity calculation for different modes."""
    params = VexyliconParams(steps=4, opacity_progression=OpacityProgression.LINEAR)
    generator = VexyliconGenerator(params=params)

    opacities = generator._calculate_opacities()
    assert len(opacities) == 4
    assert all(0 < op <= 1 for op in opacities)

    # Test that opacities increase (for linear mode)
    assert opacities == sorted(opacities)
