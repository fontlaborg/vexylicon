# Vexylicon

Vexylicon is a Python package that empowers you to create stunning SVG icon effects inspired by Apple’s modern "liquid glass" design language. If you've admired the translucent, subtly three-dimensional icons on recent Apple platforms, Vexylicon helps you achieve that same polished look for your own SVG icons and logos.

## What it Does

Vexylicon algorithmically generates these sophisticated visual effects:

*   **Beveled Glass Layers:** It takes a specially prepared dual-contour SVG (an SVG with an outer shape and an inner hole) and extrudes it into a series of concentric "glass rings." These rings build up to create a believable sense of depth and volume.
*   **Apple-Inspired Gradients:** The generated icons automatically incorporate gradients similar to those used in Apple's Liquid Glass style, ensuring your artwork feels native on platforms like iOS, macOS, and watchOS.
*   **Theme Customization:** A flexible JSON-based theme system allows you to define your own color schemes and gradient styles. Vexylicon can also automatically generate light and dark variants of themes.
*   **Payload Injection:** You can embed your existing logos, symbols, or any other SVG artwork inside the beveled glass mask, seamlessly integrating them into the effect.
*   **Vector Quality:** All effects are generated as vector graphics, meaning your icons will scale crisply to any size without loss of quality, perfect for Retina/XDR displays.
*   **Optional Blur:** Add a subtle blur to the glass rings for a softer, more diffused appearance.

## Who It's For

*   **Designers:** Quickly apply a modern, sophisticated glass effect to your icon designs without manual vector manipulation.
*   **Developers:** Programmatically generate icons that match the latest UI trends, especially for applications targeting Apple ecosystems.
*   **Anyone wanting to elevate their SVG icons:** If you want to add a touch of elegance and depth to your digital assets, Vexylicon provides a powerful tool to do so.

## Why It's Useful

*   **Adds Visual Appeal:** Creates icons with a tactile, hyper-realistic feel that stands out.
*   **Maintains Scalability:** Unlike raster effects, your icons remain sharp and editable vectors.
*   **Automates Variants:** Easily generate light and dark mode versions of your icons from a single theme definition.
*   **Consistent Styling:** Achieve a uniform and professional look across your icon set.
*   **Saves Time:** Automates a complex visual effect that would be time-consuming to create manually.

## Installation

Vexylicon requires **Python 3.11+**.

You can install Vexylicon using pip:

```bash
# Once released on PyPI (check project status for availability)
pip install vexylicon
```

Alternatively, you can install it directly from the source for the latest version:

```bash
git clone https://github.com/fontlaborg/vexylicon.git
cd vexylicon
pip install -e .
```
Vexylicon has a small dependency stack, primarily `lxml` for SVG processing and `python-fire` for the CLI. For PNG export, `cairosvg` is required.

## How to Use (Command Line Interface - CLI)

The `vexylicon` command-line tool is the easiest way to get started.

**1. Basic Usage:**
To generate a glass effect icon from the default base SVG (included with the package) and save it as `output.svg`:
```bash
vexylicon create --output my_icon.svg
```

**2. Common Options:**
You can customize the output with various options:
```bash
vexylicon create \
    --output logo_glass.svg \
    --payload path/to/your_logo.svg \
    --quality ultra \
    --theme default-dark \
    --blur 2.0
```
*   `--output <filename>`: Specifies the output file name.
*   `--payload <path_to_svg>`: Path to an SVG file you want to embed within the glass effect.
*   `--quality <level>`: Sets the number of bevel steps. Options: `low` (8), `medium` (16), `high` (24), `ultra` (32).
*   `--theme <name_or_path>`: Specifies the theme. Use a built-in theme name (e.g., `default`, `dark`) or a path to a custom theme JSON file.
*   `--steps <number>`: Manually set the number of bevel steps, overriding `--quality`.
*   `--blur <value>`: Applies a Gaussian blur effect to the bevel steps (e.g., `1.0`, `2.5`).

**3. Other CLI Commands:**
*   `vexylicon batch <input_dir> <output_dir> [options]`: Process multiple SVG files from an input directory and save them to an output directory.
*   `vexylicon themes`: List available built-in and custom themes.
*   `vexylicon preview <input_svg> [output_png]`: Generate a PNG preview of a Vexylicon SVG (requires `cairosvg`).
*   `vexylicon shape2base <input_svg> [output_base_svg]`: A utility to help convert a simple, flat SVG shape into the dual-contour base template required by Vexylicon.

## How to Use (Python API)

For more control or integration into your Python projects, use the Vexylicon API:

```python
from pathlib import Path
from vexylicon import VexyliconGenerator, VexyliconParams
from vexylicon.core import OpacityProgression # For opacity_progression enum

# 1. Configure parameters for the generation
params = VexyliconParams(
    steps=32,  # Corresponds to 'ultra' quality
    blur=2.0,
    opacity_progression=OpacityProgression.MORE_EXPONENTIAL, # Default, deep crystal-like
    # opacity_start=0.9, # Default
    # opacity_end=0.05   # Default
)

# 2. Initialize the generator with a theme and parameters
#    Themes can be names of built-in themes or a path to a custom theme JSON file.
generator = VexyliconGenerator(theme="default", params=params)

# 3. Generate the SVG
#    You can provide a path to an SVG file to be used as a payload.
payload_svg_path = "path/to/your_brand_logo.svg" # Optional
# payload_svg_path = None # If no payload

try:
    glass_svg_content = generator.generate(payload_svg=payload_svg_path)

    # 4. Save the output
    output_file = Path("brand_liquid_icon.svg")
    output_file.write_text(glass_svg_content, encoding="utf-8")
    print(f"Successfully generated {output_file}")

except Exception as e:
    print(f"An error occurred: {e}")

```

## How Vexylicon Works: A Technical Deep Dive

This section describes the internal workings of Vexylicon, its architecture, and key algorithms.

### Core Architecture

Vexylicon's functionality is primarily organized into a core generation engine, a command-line interface, and several utility modules:

*   **`src/vexylicon/core.py`**: Contains `VexyliconGenerator`, the main class responsible for orchestrating the SVG effect generation. It takes parameters and a theme, processes a base SVG, and outputs the final glass-effect SVG.
*   **`src/vexylicon/cli.py`**: Implements the command-line interface using `python-fire`. It parses arguments and calls `VexyliconGenerator` and other utilities.
*   **`src/vexylicon/utils/`**:
    *   **`svg_processor.py`**: Provides the `SVGProcessor` class, which is a wrapper around `lxml` for robust and safe manipulation of SVG XML documents. **Crucially, Vexylicon avoids direct string manipulation of SVG content, relying on `lxml`'s DOM capabilities.**
    *   **`path_tools.py`**: Includes functions for SVG path data manipulation, such as `parse_dual_contour_path` (to separate the two paths from a compound path string) and `generate_ring_paths` (to interpolate intermediate paths between the outer and inner contours). It also handles path alignment to prevent twisting during interpolation.
    *   **`theme_loader.py`**: Defines `ThemeLoader` for loading and validating theme JSON files. It uses Pydantic for data validation and can discover themes from predefined user directories or load them from a direct path.
    *   **`base_builder.py`**: Contains `BaseSVGBuilder`, a utility to help create the necessary dual-contour base SVG from a simpler single-path SVG.
*   **`src/vexylicon/assets/`**:
    *   `best_base.svg`: The canonical dual-contour SVG template. This file is crucial as it defines the expected input structure for the glass effect generation, including named elements like `#mainShape`, `#borderShape`, and gradient placeholders.
    *   `themes/default.json`: An example theme file showcasing the JSON structure for defining colors and gradients.

### Generation Process (`VexyliconGenerator.generate`)

1.  **Initialization**: The `VexyliconGenerator` is initialized with `VexyliconParams` (controlling steps, blur, opacity) and a `Theme` object (loaded by `ThemeLoader`). It also loads the content of `assets/best_base.svg`.

2.  **Base SVG Parsing**: An `SVGProcessor` instance is created with the `base_svg_content`.

3.  **Bevel Step Generation (`_generate_bevel_steps`)**:
    *   The main dual-contour path data is extracted from the `#mainShape` element (or the first `<path>` if not found by ID) in the base SVG.
    *   `parse_dual_contour_path` separates this into an `outer_contour` and an `inner_contour`.
    *   `generate_ring_paths` interpolates `N` intermediate paths (where `N` is `params.steps`) between the `outer_contour` and `inner_contour`. This function ensures paths are aligned (e.g., by rotating the outer path so its start point is nearest the inner start point) to prevent twisting. All path segments are typically converted to cubic Béziers for smooth interpolation.
    *   A group element `<g id="bevelSteps">` is created.
    *   Opacity values for each ring are calculated by `_calculate_opacities` based on the `params.opacity_progression` mode (Linear, Decreasing, Exponential, More Exponential).
    *   For each interpolated ring path:
        *   A new `<path>` element is created.
        *   It's assigned an `id` (e.g., `bevelStep-i`).
        *   `fill` is set to `url(#edgeGlow)` (or another themeable gradient).
        *   `fill-opacity` is set to the calculated opacity for that ring.
        *   `mix-blend-mode` is set to `screen` to achieve the characteristic glass highlight effect.
        *   If `params.blur > 0`, an SVG blur filter (`<feGaussianBlur>`) is defined in `<defs>` (if not already present for that blur value) and applied to the path via the `filter` attribute.
        *   The new path is appended to the `bevelSteps` group.
    *   The `bevelSteps` group is appended to the SVG root.
    *   A similar process is applied for the `#smallShape` if present, creating `#smallBevelSteps` typically using a `#cornerHighlight` gradient.

4.  **Theme Application (`_apply_theme`)**:
    *   Gradients defined in the loaded `Theme` object (e.g., `edgeGlow`, `cornerHighlight`) are added to the SVG's `<defs>` section by `SVGProcessor.add_gradient`.
    *   Theme colors (e.g., for canvas background, border) are applied to corresponding elements if they exist (e.g., `#canvas`, `#border`).

5.  **Theme-Aware Grouping (`_create_theme_groups`)**: This step primarily ensures that necessary structures like clip paths are correctly defined. For example, a `<clipPath id="borderClip">` using `#borderShape` is created/verified in `<defs>`. This clip path is essential for the payload injection.

6.  **Payload Injection (`_inject_payload`)**:
    *   If a `payload_svg` is provided (as a path or string):
        *   It's parsed into a new `SVGProcessor` instance.
        *   A `<g id="payload">` element is created in the main SVG.
        *   This group is assigned `clip-path="url(#borderClip)"` to confine the payload within the inner boundary of the glass effect.
        *   The content (excluding `<defs>`) from the `payload_svg`'s root is imported into this `payload` group.
        *   The `payload` group is inserted into the main SVG, typically before the `#back` element or appended to the root.

7.  **Output**: The `SVGProcessor` serializes the modified `lxml` tree back into an SVG string.

### Key Technical Choices & Constraints

*   **lxml for SVG Manipulation**: All SVG modifications are done via the `lxml` library. This ensures correctness and avoids common pitfalls of string-based XML manipulation.
*   **`svgpathtools` for Path Math**: While `lxml` handles the XML structure, `svgpathtools` (or similar path mathematics libraries, possibly vendored or used carefully) is likely involved in `path_tools.py` for operations like path parsing, length calculations, and interpolation of Bézier curves.
*   **Dual-Contour Requirement**: The core algorithm relies on a base SVG that has two defined contours (an outer boundary and an inner hole) with compatible path structures for interpolation. The `shape2base` command helps create these.
*   **Python 3.11+**: The codebase utilizes features and typing syntax available in Python 3.11 or newer.
*   **Minimal Dependencies**: The project aims to keep its dependency list small: `lxml`, `fire`, `pydantic`, `rich`. `svgpathtools` is a key component for path operations. `cairosvg` is an optional extra for PNG output.

## Coding and Contribution Guidelines

We welcome contributions to Vexylicon! Please adhere to the following guidelines. These are largely derived from the project's `CLAUDE.md` and `AGENT.md` files.

### Code Quality & Style

*   **Dependency Management**: Use `uv pip` for managing Python environments and dependencies.
*   **Type Hinting**: All public functions and methods must have full type hints.
*   **Docstrings**: Use NumPy style for docstrings.
*   **Formatting**: Code must be formatted with `black`.
*   **Linting**: Code must pass `ruff check --fix`.
*   **Testing**: Aim for >90% test coverage. Write tests for new features and bug fixes.
*   **Python Version**: Ensure compatibility with Python 3.11 and newer.
*   **File Path Comments**: Include a comment like `# this_file: src/vexylicon/utils/svg_processor.py` at the top of each Python file.

### SVG Processing Rules

*   **Always use `lxml`**: For any reading, modification, or writing of SVG files.
*   **Never use string replacement**: For SVG content manipulation. This is error-prone.
*   **Preserve Namespaces and Attributes**: Be mindful of existing SVG structure.
*   **Coordinate Precision**: Round floating-point coordinates in SVG output to a reasonable number of decimal places (e.g., 2 or 3) to keep file sizes manageable without sacrificing visual quality.

### Error Handling

*   Use the defined custom exceptions where appropriate: `VexyliconError`, `InvalidSVGError`, `ThemeValidationError`.
*   Provide clear and actionable error messages.

### Development Workflow

1.  **Understand the Task**: Before coding, thoroughly read the existing code, relevant issues, `PLAN.md`, and `TODO.md`. Ensure you understand the dual-contour SVG format.
2.  **Branching**: Create a new branch for your feature or bug fix.
3.  **Incremental Development**: Work in small, testable increments.
4.  **Testing**: Write tests as you develop. Run `pytest` frequently.
5.  **Documentation**: Update docstrings, `README.md` (if applicable), and `CHANGELOG.md` for any user-facing changes or significant internal modifications. Keep `TODO.md` current if you identify further tasks.
6.  **Pre-commit Checks**: Before committing, run:
    ```bash
    black src tests
    ruff check --fix src tests
    pytest
    mypy src
    ```
7.  **Commit Messages**: Write clear and concise commit messages.
8.  **Pull Request**: Submit a pull request to the main repository. Describe your changes and link any relevant issues.

### Reporting Bugs

*   Please report bugs via GitHub Issues.
*   Include:
    *   Vexylicon version (e.g., from `pip show vexylicon`, or commit hash if from source).
    *   Python version.
    *   Operating system.
    *   Steps to reproduce the bug.
    *   Expected behavior.
    *   Actual behavior (including any error messages or incorrect output SVGs).
    *   Input files (base SVG, payload SVG, theme JSON if custom) if relevant and shareable.

### Suggesting Features

*   Feature requests are also welcome via GitHub Issues.
*   Provide a clear description of the proposed feature and why it would be useful.

## Roadmap Highlights

The following are some of the planned enhancements for Vexylicon:

*   **Gradio-Lite Web Playground:** An interactive web interface for trying out Vexylicon directly in the browser.
*   **Additional Themes:** Shipping more built-in themes, including vibrant accent tints and Glassmorphism neon styles.
*   **Single-Contour Conversion:** Enhanced `shape2base` or new tools to automatically convert single-contour logos/icons into the required dual-contour base by intelligently creating an inner path.

## License

Vexylicon is open-source software licensed under the **MIT License**.
It is created and maintained by **Fontlab Ltd.**

---

Inspired by Apple’s Liquid Glass material and the broader design community exploring glassmorphism.

Happy glass-crafting! 🎉
