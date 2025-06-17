# Vexylicon Test Data

This directory contains test files and examples for the Vexylicon glass effect generator.

## Files

- **payload.svg** - A book icon SVG that serves as the payload/content to be masked
- **example.py** - Python script that demonstrates how to use Vexylicon to generate glass effects
- **test.html** - Interactive HTML demo showing the glass effect with various colorful backgrounds

## Generated Files (after running example.py)

- **glass_with_payload.svg** - Glass effect with the book icon payload
- **glass_plain.svg** - Glass effect without any payload
- **glass_payload_low.svg** - Low quality (8 steps) version
- **glass_payload_medium.svg** - Medium quality (16 steps) version  
- **glass_payload_high.svg** - High quality (24 steps) version
- **glass_payload_ultra.svg** - Ultra quality (32 steps) version

## Usage

1. Run the example script to generate the glass effect SVGs:
   ```bash
   python example.py
   ```

2. Open `test.html` in a web browser to see the interactive demo

## How it Works

The demo shows how the glass effect creates a liquid-glass appearance:

1. **Colorful backgrounds** are defined using CSS gradients and patterns
2. **Clipping** is applied to mask the backgrounds to the icon shape
3. **Glass effect SVG** is overlaid on top with `mix-blend-mode: screen`
4. **Theme support** allows switching between light and dark modes

The result is a sophisticated glass-morphism effect that works with any background.