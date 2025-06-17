#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["fire", "pillow"]
# ///
# this_file: icon_blender.py
"""
Image Quarter Slicer CLI Tool
Slices an image into 4 equal quarters
"""

import fire
from PIL import Image
import os


def slice_image(input_image: str):
    """
    Slice an image into 4 quarters.

    Args:
        input_image: Path to input PNG image

    Output files:
        - {base}-00.png: Top left quarter
        - {base}-10.png: Top right quarter
        - {base}-01.png: Bottom left quarter
        - {base}-11.png: Bottom right quarter

    """
    # Load the image
    img = Image.open(input_image)
    width, height = img.size

    # Calculate quarter dimensions
    half_width = width // 2
    half_height = height // 2

    # Get base filename without extension
    base_path = os.path.splitext(input_image)[0]

    # Slice and save quarters
    # Top left (00)
    top_left = img.crop((0, 0, half_width, half_height))
    top_left.save(f"{base_path}-00.png")

    # Top right (10)
    top_right = img.crop((half_width, 0, width, half_height))
    top_right.save(f"{base_path}-10.png")

    # Bottom left (01)
    bottom_left = img.crop((0, half_height, half_width, height))
    bottom_left.save(f"{base_path}-01.png")

    # Bottom right (11)
    bottom_right = img.crop((half_width, half_height, width, height))
    bottom_right.save(f"{base_path}-11.png")

    print(f"Successfully sliced {input_image} into 4 quarters:")
    print(f"  - {base_path}-00.png (top left)")
    print(f"  - {base_path}-10.png (top right)")
    print(f"  - {base_path}-01.png (bottom left)")
    print(f"  - {base_path}-11.png (bottom right)")


if __name__ == "__main__":
    fire.Fire(slice_image)
