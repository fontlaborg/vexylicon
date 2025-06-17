# Vexylicon

A Python package for creating sophisticated liquid-glass SVG icon effects with theme-aware capabilities.

## Project Status

🚧 **Alpha Release** - Core functionality working, theme system and web interface in development.

## Overview

Vexylicon transforms SVG icons into stunning glass-morphism designs with beveled edges. It takes a specially formatted base SVG with dual contours and generates smooth, progressive ring shapes that create a convincing 3D glass effect.

## Current Features

✅ **Working**
- Glass effect generation with configurable bevel steps
- Payload SVG injection with clipPath masking
- CLI with create, batch, themes, and preview commands
- Quality presets (low=8, medium=16, high=24, ultra=32 steps)
- Multiple opacity progression modes
- JSON-based theme system

⚠️ **In Development**
- Theme-aware light/dark mode switching
- Proper gradient duplication for themes
- Gradio-lite web interface

## Installation

From source (recommended during alpha):

```bash
git clone https://github.com/fontlaborg/vexylicon
cd vexylicon
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Quick Start

### Basic Usage

Generate a glass effect icon:

```bash
vexylicon create --output my-icon.svg
```

With custom payload SVG:

```bash
vexylicon create --output my-icon.svg --payload logo.svg --quality high
```

### Python API

```python
from vexylicon import VexyliconGenerator, VexyliconParams

# Basic usage
generator = VexyliconGenerator()
svg_output = generator.generate()

# With payload
svg_output = generator.generate(payload_svg="logo.svg")

# Custom parameters
params = VexyliconParams(steps=16, quality="medium")
generator = VexyliconGenerator(params=params)
```

## CLI Commands

### `create` - Generate a single icon

```bash
vexylicon create [OPTIONS]

Options:
  --output TEXT              Output file path (default: output.svg)
  --payload TEXT             Path to payload SVG to inject
  --steps INTEGER            Number of bevel steps (default: 24)
  --quality TEXT             Preset: low/medium/high/ultra
  --opacity-progression INT  Opacity mode 1-4 (default: 4)
  --format TEXT              Output format: svg or png
```

### `batch` - Process multiple SVGs

```bash
vexylicon batch INPUT_DIR OUTPUT_DIR [OPTIONS]
```

### `themes` - List available themes

```bash
vexylicon themes
```

### `preview` - Generate PNG preview (requires cairosvg)

```bash
vexylicon preview SVG_FILE [--output OUTPUT_PATH]
```

## How It Works

1. **Base SVG**: Uses `best_base.svg` as the template with dual contours
2. **Path Interpolation**: Generates intermediate rings between inner and outer contours
3. **Opacity Progression**: Applies mathematical opacity (linear to quartic)
4. **Glass Effect**: Uses `mix-blend-mode: screen` for transparency
5. **Payload Injection**: Optional SVG artwork clipped to inner shape

### Opacity Progression Modes

1. **Linear**: Even distribution
2. **Decreasing**: Reverse exponential
3. **Exponential**: Quadratic progression
4. **More Exponential**: Quartic progression (default, best glass effect)

## Architecture

```
vexylicon/
├── core.py              # VexyliconGenerator class
├── cli.py               # Fire-based CLI
├── utils/
│   ├── svg_processor.py # lxml-based SVG manipulation
│   ├── path_tools.py    # Path interpolation from icon_blender.py
│   └── theme_loader.py  # JSON theme validation
└── assets/
    ├── best_base.svg    # Base template
    └── themes/          # Theme definitions
```

## Known Limitations

- Theme switching CSS not fully implemented
- Light/dark gradient variants need proper duplication
- Complex SVG payloads may need manual adjustment
- Web interface pending (Gradio-lite planned)

## Development

### Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code quality
black src tests
ruff check src tests
mypy src
```

### Contributing

The project needs help with:
1. Completing theme-aware gradient generation
2. Building the Gradio-lite web interface
3. Writing comprehensive tests
4. Improving documentation

## Technical Stack

- **Python 3.11+** (required)
- **lxml** - Robust XML/SVG manipulation
- **svgpathtools** - Path interpolation
- **pydantic** - Theme validation
- **fire** - CLI framework
- **rich** - Terminal formatting

## Roadmap

See [TODO.md](TODO.md) for detailed plans:

1. Fix theme system (gradient duplication)
2. Add CSS for light/dark switching
3. Create Gradio-lite web interface
4. Achieve >90% test coverage
5. Publish to PyPI

## License

MIT License - see [LICENSE](LICENSE) file

## Author

Developed by Fontlab Ltd.

## Acknowledgments

Based on the original `icon_blender.py` and `icon_masker.py` scripts, refactored into a modern Python package.