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
- Performance optimizations for large batch processing
- Additional theme presets and customization options

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

## [1.3.0] - 2025-01-17

### Added
- **Blur effect support**: Added `--blur` parameter to CLI and core functionality
  - Applies Gaussian blur filters to bevel steps when `blur > 0`
  - Supports both CLI (`--blur 2.0`) and programmatic usage (`VexyliconParams(blur=2.0)`)
  - Blur filters are reused efficiently (one filter per blur value)
- **Corner highlight restoration**: Restored missing small shape processing from original icon_blender.py
  - Processes `<use id="small">` elements with `cornerHighlight` gradient
  - Creates separate `smallBevelSteps` group with 24 interpolated paths
  - Maintains proper opacity progression and blend modes
- **Enhanced HTML demo**: Improved `testdata/test.html` with proper SVG clipping
  - Background patterns now clip correctly to glass shape using SVG clipPath
  - Unique ID management prevents conflicts between multiple glass overlays
  - Theme switching functionality for light/dark modes
  - Proper glass overlay positioning and z-index management

### Fixed
- **Critical packaging issue**: Fixed missing source code in distribution packages
  - Removed overly restrictive `include` directive from `pyproject.toml`
  - All Python source files now properly included in tar.gz and wheel distributions
  - Package can be installed and imported correctly
- **Glass effect visual quality**: Restored original glass effect appearance
  - Fixed bevel step gradients to use `edgeGlow` instead of `baseFill`
  - Proper opacity handling for both `<use id="outer">` and `<path id="mainShape">`
  - Corner highlight now appears in bottom-right as in original implementation
- **Payload clipping**: Fixed payload SVG clipping to use outer border shape
  - Changed from `innerClip` to `borderClip` for proper payload masking
  - Payload now fills entire glass shape area instead of inner contour only
- **Theme system simplification**: Removed problematic light/dark duplication
  - Single gradient set instead of duplicated `-light`/`-dark` variants
  - Cleaner SVG output with significantly reduced file size
  - Theme colors now configurable via JSON without code duplication

### Changed
- **Build system improvements**: Enhanced `cleanup.sh` with release automation
  - Added version release workflow when version identifier provided
  - Automated git tagging, committing, and PyPI publishing
  - Improved repomix exclusions for cleaner documentation generation
- **Code quality**: Fixed linter warnings and improved code organization
  - Proper line length handling in core.py
  - Enhanced error handling and type annotations
  - Better separation of concerns between modules

### Technical Details
- Restored dual-contour processing for both main shape (edgeGlow) and small shape (cornerHighlight)
- SVG filter elements created dynamically for blur effects with proper reuse
- Enhanced clipPath handling with unique ID generation for multiple instances
- Improved opacity calculations with quartic progression (MORE_EXPONENTIAL mode)
- Better asset management with proper importlib.resources usage