#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["icon_blender.py", "rich", "fire"]
# ruff: noqa
# ///
# this_file: icon_masker.py
"""Build the theme-aware "liquid-glass" icon mask SVG and inject a payload_svg.

This script follows the high-level process described in SPEC.md.  It performs:
1. Calls `icon_blender.py` programmatically to generate the bevel steps.
2. Post-processes the SVG tree in-memory to add:
   • light/dark gradient tokens
   • `<clipPath>` for the inner window
   • `theme-light` / `theme-dark` groups containing `<use>` references
   • `<g id="payload_svg">` masked by the inner clip and populated with an
     external SVG artwork (optional).
3. Writes `mask-light.svg` *and* `mask-dark.svg` to the output directory.

Run:
    python icon_masker.py --payload_svg payload_svg.svg --outdir output

If `--payload_svg` is omitted the slot is left empty so that the caller can insert
artwork later via DOM manipulation.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path as FsPath
import xml.etree.ElementTree as ET

import fire
from rich import print

# Ensure we can import sibling cli
sys.path.append(str(FsPath(__file__).resolve().parent.parent))
import icon_blender  # noqa: E402

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)


def _ns(tag: str) -> str:
    """Return namespaced tag.

"""
    return f"{{{NS}}}{tag}"


def run_blender(src: FsPath, steps: int) -> ET.ElementTree:
    """Invoke icon_blender.main() and return parsed ElementTree of result.

"""
    with tempfile.NamedTemporaryFile("w+", suffix=".svg", delete=False) as tmp:
        tmp_path = FsPath(tmp.name)
    args = [
        "--input_svg",
        str(src),
        "--output_svg",
        str(tmp_path),
        "--steps",
        str(steps),
    ]
    print(f"[blue]• Generating bevel steps ({steps}) via icon_blender…")
    sys.argv = ["icon_blender"] + args  # icon_blender parses sys.argv
    icon_blender.main()
    tree = ET.parse(tmp_path)
    tmp_path.unlink(missing_ok=True)
    return tree


def duplicate_gradient(elem: ET.Element, suffix: str) -> ET.Element:
    """Return a *copy* of `elem` with its id suffixed.

"""
    new_elem = ET.fromstring(ET.tostring(elem, encoding="unicode"))
    gid = new_elem.get("id", "")
    new_elem.set("id", f"{gid}-{suffix}")
    return new_elem


def post_process(tree: ET.ElementTree, payload_svg: FsPath | None) -> ET.ElementTree:
    """"""
    root = tree.getroot()

    # 1. Collect <defs> (create if missing)
    defs = root.find(_ns("defs"))
    if defs is None:
        defs = ET.SubElement(root, _ns("defs"))

    # Rename existing gradients to *-light and duplicate for *-dark ---------
    for grad in list(defs):
        gid = grad.get("id")
        if not gid:
            continue
        if not gid.endswith("-dark"):
            dark_copy = duplicate_gradient(grad, "dark")
            defs.append(dark_copy)

        # ------------------------------------------------------------------
        # Dial in glass-like transparency for gradient1 & gradient3
        # ------------------------------------------------------------------
        if gid.startswith("gradient1"):
            opacities = ["0.85", "0.55", "0.15"]
        elif gid.startswith("gradient3"):
            opacities = ["0.35", "0.15"]
        else:
            opacities = []

        if opacities:
            for stop, op in zip(grad.findall(_ns("stop")), opacities):
                stop.set("stop-opacity", op)
            # Make the dark copy slightly more opaque
            if not gid.endswith("-dark"):
                for stop in dark_copy.findall(_ns("stop")):
                    stop.set(
                        "stop-opacity",
                        opacities[
                            min(
                                len(opacities) - 1,
                                dark_copy.findall(_ns("stop")).index(stop),
                            )
                        ],
                    )

    # 2. Insert clipPath ----------------------------------------------------
    inner = root.find(f".//{_ns('path')}[@id='inner']")
    if inner is None:
        raise SystemExit("[red]Could not locate path with id='inner'")

    clip = ET.Element(_ns("clipPath"), id="innerClip")
    clip_use = ET.SubElement(clip, _ns("use"))
    clip_use.set("href", "#inner")
    defs.append(clip)

    # 3. Build theme groups --------------------------------------------------
    outer_use = ET.Element(_ns("use"), href="#outer")
    bevel_use = ET.Element(_ns("use"), href="#bevelSteps")
    small_use = ET.Element(_ns("use"), href="#small")

    light_grp = ET.Element(_ns("g"), id="theme-light", attrib={"class": "theme-light"})
    dark_grp = ET.Element(_ns("g"), id="theme-dark", attrib={"class": "theme-dark"})

    # Gradient fills — originals for light, *-dark variants for dark theme
    outer_use_light = duplicate_gradient(outer_use, "copy")
    outer_use_light.set("fill", "url(#gradient1)")
    outer_use_dark = duplicate_gradient(outer_use, "copy2")
    outer_use_dark.set("fill", "url(#gradient1-dark)")

    small_use_light = duplicate_gradient(small_use, "copy3")
    small_use_light.set("fill", "url(#gradient2)")
    small_use_dark = duplicate_gradient(small_use, "copy4")
    small_use_dark.set("fill", "url(#gradient2-dark)")

    # Bevel uses gradient3
    bevel_use_light = duplicate_gradient(bevel_use, "copy5")
    bevel_use_light.set("fill", "url(#gradient3)")
    bevel_use_dark = duplicate_gradient(bevel_use, "copy6")
    bevel_use_dark.set("fill", "url(#gradient3-dark)")

    # Assemble groups
    light_grp.extend([outer_use_light, bevel_use_light, small_use_light])
    dark_grp.extend([outer_use_dark, bevel_use_dark, small_use_dark])

    # 4. payload_svg group -------------------------------------------------------
    payload_svg_grp = ET.Element(
        _ns("g"), id="payload_svg", attrib={"clip-path": "url(#innerClip)"}
    )

    # Insert payload_svg artwork if provided
    if payload_svg and payload_svg.exists():
        try:
            pay_tree = ET.parse(payload_svg)
            pay_root = pay_tree.getroot()
            # import children of payload_svg svg; ignore width/height attributes
            for child in list(pay_root):
                payload_svg_grp.append(child)
            print(f"[green]✓ Injected payload_svg from {payload_svg}")
        except ET.ParseError as exc:
            print(f"[yellow]⚠ Could not parse payload_svg SVG: {exc}")

    # 5. Hide original decorative layers to prevent double-drawing ----------
    # NOTE: We keep original decorative layers visible so that edge styling
    # renders correctly. If duplicate drawing becomes an issue we can move
    # originals into <defs> instead of hiding them.

    # 6. Append new groups at end of root -----------------------------------
    root.extend([light_grp, dark_grp, payload_svg_grp])

    return tree


def write_variants(tree: ET.ElementTree, outdir: FsPath):
    """"""
    outdir.mkdir(parents=True, exist_ok=True)
    light_path = outdir / "mask-light.svg"
    dark_path = outdir / "mask-dark.svg"

    tree.write(light_path, encoding="utf-8", xml_declaration=True)

    # Duplicate for dark, then simple string replacement for -light/-dark ids
    text = light_path.read_text(encoding="utf-8")
    text_dark = (  # noqa: E501
        text.replace("url(#gradient1)", "url(#gradient1-dark)")  # noqa: E501
        .replace("url(#gradient2)", "url(#gradient2-dark)")  # noqa: E501
        .replace("url(#gradient3)", "url(#gradient3-dark)")  # noqa: E501
        .replace("theme-light", "theme-dark")  # noqa: E501
    )
    dark_path.write_text(text_dark, encoding="utf-8")

    print(f"[bold green]✓ Wrote {light_path} & {dark_path}")


def build_mask(
    payload_svg: str | None = None,
    outdir: str = "output",
    steps: int = 24,
    mask_svg: str = "best_base.svg",
) -> None:
    """Build icon mask SVG with optional payload_svg.

    Args:
        payload_svg: Path to payload_svg SVG to inject
        outdir: Directory for outputs
        steps: Number of bevel interpolation steps
        mask_svg: Path to base mask SVG file

    """
    base_svg = FsPath(mask_svg)
    if not base_svg.exists():
        raise SystemExit(f"[red]{mask_svg} not found in workspace")

    payload_svg_path = FsPath(payload_svg) if payload_svg else None
    tree = run_blender(base_svg, steps)
    tree = post_process(tree, payload_svg_path)
    write_variants(tree, FsPath(outdir))


if __name__ == "__main__":
    fire.Fire(build_mask)
