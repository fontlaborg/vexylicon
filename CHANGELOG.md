# Changelog

All notable changes to Vexylicon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Theme-aware gradient generation with automatic light/dark variants
- CSS media queries for `prefers-color-scheme` support
- Proper duplication of gradients with `-light` and `-dark` suffixes
- Dark mode opacity adjustment (+20% for better visibility)

### Fixed
- Ruff configuration already using correct `exclude` key (not `extend-exclude`)

### TODO
- Adopt Loguru for structured logging
- Improve payload masking for HTML/SVG backgrounds
- Gradio-lite web interface for browser-based usage
- Comprehensive test suite with >90% coverage
- PyPI package publication

## [0.1.0] - 2025-01-18

### Added
- Initial package structure with modern Python packaging (pyproject.toml)
- Core `VexyliconGenerator` class for creating liquid-glass effects
- Theme system with JSON-based theme definitions
- SVG manipulation using lxml (no string manipulation)
- Path interpolation utilities extracted from icon_blender.py
- Fire-based CLI with commands:
  - `create`: Generate single SVG with glass effect
  - `batch`: Process multiple SVGs
  - `themes`: List available themes
  - `preview`: Generate PNG preview (requires cairosvg)
- Support for payload injection with clipPath masking
- Configurable opacity progression modes (linear, exponential, etc.)
- Quality presets (low=8, medium=16, high=24, ultra=32 steps)
- Comprehensive error handling with custom exceptions
- Type hints throughout the codebase
- Basic test structure

### Technical Stack
- **Core**: Python 3.11+
- **SVG Processing**: lxml, svgpathtools
- **CLI**: Fire
- **Validation**: Pydantic
- **UI**: Rich (terminal output)
- **Assets**: importlib.resources

### Known Issues
- Payload injection works but may need refinement for complex SVGs

### Migration Notes
- Consolidated icon_blender.py (glass mode only) and icon_masker.py functionality
- Removed non-glass modes from icon_blender
- Standardized on best_base.svg as the canonical base template
- Theme colors and gradients now defined in JSON rather than hardcoded