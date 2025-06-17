#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["vexylicon"]
# ///
# this_file: testdata/example.py
"""Example script showing how to use Vexylicon with a payload SVG.

This script demonstrates:
1. Loading a payload SVG (book icon)
2. Generating a glass effect with the payload
3. Saving the output for use in HTML demos
"""

import sys
from pathlib import Path

# Add parent directory to path to import vexylicon
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vexylicon import VexyliconGenerator, VexyliconParams


def main():
    """    """
    # Create generator with default theme
    generator = VexyliconGenerator(theme="default")

    # Path to payload SVG (book icon)
    payload_path = Path(__file__).parent / "payload.svg"

    # Generate glass effect with payload
    print("Generating glass effect with payload SVG...")
    svg_output = generator.generate(payload_svg=payload_path)

    # Save output
    output_path = Path(__file__).parent / "glass_with_payload.svg"
    with open(output_path, "w") as f:
        f.write(svg_output)

    print(f"✓ Generated glass effect saved to: {output_path}")

    # Also generate a version without payload for comparison
    print("\nGenerating glass effect without payload...")
    svg_plain = generator.generate()

    plain_path = Path(__file__).parent / "glass_plain.svg"
    with open(plain_path, "w") as f:
        f.write(svg_plain)

    print(f"✓ Plain glass effect saved to: {plain_path}")

    # Generate with different step counts for quality comparison
    print("\nGenerating quality variants...")
    qualities = {"low": 8, "medium": 16, "high": 24, "ultra": 32}

    for quality_name, steps in qualities.items():
        params = VexyliconParams(steps=steps)
        gen = VexyliconGenerator(theme="default", params=params)
        svg_quality = gen.generate(payload_svg=payload_path)

        quality_path = Path(__file__).parent / f"glass_payload_{quality_name}.svg"
        with open(quality_path, "w") as f:
            f.write(svg_quality)

        print(f"✓ {quality_name.capitalize()} quality ({steps} steps) saved to: {quality_path}")

    print("\n✅ All examples generated successfully!")
    print("\nTo view in browser, open test.html")


if __name__ == "__main__":
    main()
