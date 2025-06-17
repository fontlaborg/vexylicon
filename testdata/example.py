#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["vexylicon"]
# ///
# this_file: testdata/example.py
"""Example script showing how to use Vexylicon with a payload SVG.

This script demonstrates:
1. Loading a payload SVG (book icon)
2. Generating a glass effect with the payload
3. Generating quality variants (different step counts)
4. Generating blur variants (different blur effects)
5. Saving the output for use in HTML demos
"""

import sys
from pathlib import Path

# Add parent directory to path to import vexylicon
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vexylicon import VexyliconGenerator, VexyliconParams


def main() -> None:
    """Used in:
- old/good/icon_blender.py
- old/older/icon_masker.py
- old/older/imgquart.py
"""
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

    # Generate blur variants to demonstrate the blur effect
    print("\nGenerating blur variants...")
    blur_variants = {"no_blur": 0.0, "light_blur": 1.0, "medium_blur": 2.0, "heavy_blur": 3.5}

    for blur_name, blur_value in blur_variants.items():
        params = VexyliconParams(steps=16, blur=blur_value)
        gen = VexyliconGenerator(theme="default", params=params)
        svg_blur = gen.generate(payload_svg=payload_path)

        blur_path = Path(__file__).parent / f"glass_blur_{blur_name}.svg"
        with open(blur_path, "w") as f:
            f.write(svg_blur)

        blur_desc = f"blur={blur_value}" if blur_value > 0 else "no blur"
        print(f"✓ {blur_name.replace('_', ' ').title()} ({blur_desc}) saved to: {blur_path}")

    print("\n✅ All examples generated successfully!")
    print("\nTo view in browser, open test.html")


if __name__ == "__main__":
    main()
