#!/usr/bin/env python3
# this_file: src/vexylicon/cli.py
"""Command-line interface for Vexylicon.

This module provides a Fire-based CLI for creating liquid-glass
SVG effects from the command line.
"""

from __future__ import annotations

import sys
from pathlib import Path

import fire
from rich import print
from rich.console import Console
from rich.table import Table

from vexylicon import VexyliconGenerator, VexyliconParams
from vexylicon.core import OpacityProgression, VexyliconError
from vexylicon.utils import ThemeLoader

console = Console()


class VexyliconCLI:
    """Vexylicon command-line interface."""

    def create(
        self,
        output: str = "output.svg",
        payload: str | None = None,
        steps: int = 24,
        theme: str = "default",
        opacity_start: float = 0.9,
        opacity_end: float = 0.05,
        opacity_progression: int = 4,
        quality: str | None = None,
        format: str = "svg",
    ) -> None:
        """Create liquid-glass icon mask with optional payload.

        Args:
            output: Output file path
            payload: Path to payload SVG (optional)
            steps: Number of bevel steps
            theme: Theme name or path to theme JSON
            opacity_start: Starting opacity for bevel
            opacity_end: Ending opacity for bevel
            opacity_progression: Opacity progression mode (1-4)
            quality: Preset quality level (low/medium/high/ultra)
            format: Output format (svg or png - png requires cairosvg)
        """
        try:
            # Create parameters
            params = VexyliconParams(
                steps=steps,
                opacity_start=opacity_start,
                opacity_end=opacity_end,
                opacity_progression=OpacityProgression(opacity_progression),
                quality=quality,
            )

            # Create generator
            print(f"[blue]Creating liquid-glass effect with theme: {theme}")
            generator = VexyliconGenerator(theme=theme, params=params)

            # Generate SVG
            if payload:
                print(f"[blue]Injecting payload from: {payload}")

            svg_output = generator.generate(payload_svg=payload)

            # Handle output format
            output_path = Path(output)

            if format.lower() == "svg":
                output_path.write_text(svg_output, encoding="utf-8")
                print(f"[green]✓ Created SVG: {output_path}")

            elif format.lower() == "png":
                # Convert to PNG using cairosvg
                try:
                    import cairosvg

                    output_path = output_path.with_suffix(".png")
                    cairosvg.svg2png(
                        bytestring=svg_output.encode("utf-8"),
                        write_to=str(output_path),
                        output_width=1200,
                        output_height=1200,
                    )
                    print(f"[green]✓ Created PNG: {output_path}")
                except ImportError:
                    print("[red]Error: PNG output requires cairosvg. Install with: pip install cairosvg")
                    sys.exit(1)
            else:
                print(f"[red]Error: Unknown format '{format}'. Use 'svg' or 'png'.")
                sys.exit(1)

        except VexyliconError as e:
            print(f"[red]Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[red]Unexpected error: {e}")
            sys.exit(1)

    def batch(
        self,
        input_dir: str,
        output_dir: str,
        theme: str = "default",
        steps: int = 24,
        quality: str | None = None,
        recursive: bool = False,
    ) -> None:
        """Process multiple SVGs in batch mode.

        Args:
            input_dir: Directory containing input SVGs
            output_dir: Directory for output files
            theme: Theme to apply to all SVGs
            steps: Number of bevel steps
            quality: Preset quality level
            recursive: Process subdirectories recursively
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        if not input_path.exists():
            print(f"[red]Error: Input directory does not exist: {input_dir}")
            sys.exit(1)

        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)

        # Find SVG files
        pattern = "**/*.svg" if recursive else "*.svg"
        svg_files = list(input_path.glob(pattern))

        if not svg_files:
            print(f"[yellow]No SVG files found in {input_dir}")
            return

        print(f"[blue]Found {len(svg_files)} SVG files to process")

        # Create parameters
        params = VexyliconParams(steps=steps, quality=quality)
        generator = VexyliconGenerator(theme=theme, params=params)

        # Process each file
        success_count = 0
        for svg_file in svg_files:
            try:
                print(f"[blue]Processing: {svg_file.name}")

                # Generate output path
                rel_path = svg_file.relative_to(input_path)
                out_file = output_path / rel_path.with_stem(f"{rel_path.stem}_glass")
                out_file.parent.mkdir(parents=True, exist_ok=True)

                # Process file
                svg_output = generator.generate(payload_svg=svg_file)
                out_file.write_text(svg_output, encoding="utf-8")

                success_count += 1
                print(f"[green]✓ {svg_file.name} → {out_file.name}")

            except Exception as e:
                print(f"[red]✗ Failed to process {svg_file.name}: {e}")

        print(f"\n[green]Successfully processed {success_count}/{len(svg_files)} files")

    def themes(self) -> None:
        """List available themes."""
        loader = ThemeLoader()
        themes = loader.list_themes()

        if not themes:
            print("[yellow]No themes found")
            return

        table = Table(title="Available Themes")
        table.add_column("Theme Name", style="cyan")
        table.add_column("Description", style="white")

        # Add built-in themes
        descriptions = {
            "default": "Classic liquid-glass effect with white gradients",
            "dark": "Enhanced opacity variant for dark backgrounds",
        }

        for theme_name in sorted(themes):
            desc = descriptions.get(theme_name, "Custom theme")
            table.add_row(theme_name, desc)

        console.print(table)

    def preview(self, svg_file: str, output: str | None = None) -> None:
        """Generate a preview PNG of an SVG file.

        Args:
            svg_file: Path to SVG file
            output: Output PNG path (defaults to svg_file.png)
        """
        try:
            import cairosvg
        except ImportError:
            print("[red]Error: Preview requires cairosvg. Install with: pip install cairosvg")
            sys.exit(1)

        svg_path = Path(svg_file)
        if not svg_path.exists():
            print(f"[red]Error: File not found: {svg_file}")
            sys.exit(1)

        output_path = Path(output) if output else svg_path.with_suffix(".png")

        try:
            print(f"[blue]Generating preview of {svg_file}")
            cairosvg.svg2png(url=str(svg_path), write_to=str(output_path), output_width=1200, output_height=1200)
            print(f"[green]✓ Preview saved to: {output_path}")
        except Exception as e:
            print(f"[red]Error generating preview: {e}")
            sys.exit(1)


def main():
    """Main entry point for the CLI."""
    fire.Fire(VexyliconCLI)


if __name__ == "__main__":
    main()
