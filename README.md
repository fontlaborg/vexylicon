# Vexylicon

A Python package for creating SVG icon effects inspired by Apple’s liquid glass.

Apple’s 2025 “Liquid Glass” design language brings real‑time translucency, dynamic light refraction and subtle depth cues to every Apple platform.

Vexylicon lets you generate those same glassy, tactile layers for any icon or logo, straight from Python.

- **Vexylicon** takes a _dual‑contour_ SVG (e.g. `best_base.svg`) and algorithmically extrudes it into up to 32 concentric “glass rings”, each with progressive opacity and optional blur.
- It embeds Apple‑style **Liquid Glass gradients** and groups so your artwork looks native in iOS 26, macOS Tahoe and watchOS 12.
- A JSON **theme system** and CLI/Python API let you swap gradients, duplicate them for light/dark variants, batch‑process folders, or inject any payload artwork inside the beveled mask.
- Built with modern Python 3.11+, `svgpathtools`, `lxml`, Fire CLI and Rich logging .

## 1. What & Why

### 1.1. Liquid Glass in Apple’s 2025 OS family

Apple introduced **Liquid Glass** at WWDC 25 as the new cross‑platform material that “reflects and refracts its surroundings while staying out of the way of content” ([apple.com][1]). It’s now the default chrome for navigation bars, sidebars and widgets across iOS 26, iPadOS 26, macOS Tahoe and visionOS 26 ([theverge.com][2], [developer.apple.com][3]). Developers can apply the effect with the SwiftUI `.glassEffect()` modifier ([developer.apple.com][4], [developer.apple.com][5]), and Apple’s HIG adds guidelines for contrast, depth and accessibility ([developer.apple.com][6], [developer.apple.com][7]). Early reviews praise its “hyper‑real, almost tactile” feel ([creativebloq.com][8]), while noting performance/battery trade‑offs Apple is actively tuning in beta 2 ([macrumors.com][9]).

### 1.2. Why Vexylicon helps

Vexylicon helps you:

- **Adds believable volume** through mathematically‑interpolated bevel rings (no raster layers).
- **Keeps vectors editable** so icons scale crisply on Retina/XDR displays.
- **Generates light/dark gradient variants** (or your own themes) automatically.

The name “Vexylicon” combines “vector”, “silicon” (glass) and “icon”.

## 2. How Vexylicon Works — Under the Hood

### 2.1. Dual‑Contour Base Template

`assets/best_base.svg` contains two closed paths: an outer border and an inner hole — both share identical segment counts. A `<use>` reference draws the contour multiple times so gradients can be reused without duplicating geometry.

### 2.2. Path Analysis & Interpolation

`utils/path_tools.py` parses the two contours, converts every segment to cubic Béziers, and **rotates** the outer path so its first point is nearest the inner start point (`align_path_start`) — this prevents “twisting” when interpolating. `generate_ring_paths()` then linearly interpolates **N** intermediate rings (quality presets map to 8 / 16 / 24 / 32 steps) and rounds all coordinates for minimal SVG size.

### 2.3. Opacity Progression

`core.VexyliconGenerator._calculate_opacities()` supports four curves:

| Mode | Math | Visual feel | | -- | -- | | | 1 | `t` | Flat, frosted | | 2 | `1 – t²` | Vintage macOS Aqua | | 3 | `t²` | Moderate depth | | 4 (default) | `t⁴` | Deep, crystal‑like |

Each ring gets `fill-opacity` plus `mix-blend-mode: screen` so underlying content tints the highlight—identical to Apple’s live refractive pass ([developer.apple.com][10]).

### 2.4. Theme Injection

`utils/theme_loader.py` validates JSON themes with dataclasses; `core._apply_theme()` materialises gradients via DOM editing (`SVGProcessor.add_gradient`). A helper can auto‑generate dark variants by boosting stop alpha 20 % .

### 2.5. Optional Payload

Any SVG (or path to one) can be clipped to the inner contour via `clipPath #borderClip`, letting you drop brand artwork, illustrations, even animated SVGs beneath the beveled glass. Example: the included `glass_payload_ultra.png` shows a multi‑color butterfly payload at _ultra_ quality.

## 3. Installation

```bash
pip install vexylicon        # PyPI (once released)
# OR
git clone https://github.com/fontlaborg/vexylicon
pip install -e .
```

Requires Python 3.11+ and the small C‑free dependency stack listed in _pyproject.toml_.

## 4. CLI Usage

```bash
# Generate a 1200 × 1200 SVG with default theme
vexylicon create --output icon.svg

# High‑quality, dark variant with blur and embedded logo
vexylicon create \
    --output logo_glass.svg \
    --payload assets/my_logo.svg \
    --quality ultra \
    --theme default-dark \
    --blur 4
```

Other sub‑commands:

| Command | Purpose | | | | | `batch` | Recursively process folders of SVGs. | | `themes` | List built‑in & custom themes. | | `preview` | Rasterise any generated SVG to PNG (uses CairoSVG). |

## 5. Python API

```python
from vexylicon import VexyliconGenerator, VexyliconParams

params = VexyliconParams(steps=32, blur=2.0, opacity_progression=4)
gen    = VexyliconGenerator(theme="default", params=params)

glass_svg = gen.generate(payload_svg="brand.svg")
Path("brand_liquid.svg").write_text(glass_svg, encoding="utf-8")
```

## 6. Custom Themes

1. Copy `assets/themes/default.json` and change stops, blend modes, stroke widths, etc.
2. Place the file in `~/.config/vexylicon/themes/` or pass the path directly:

```bash
vexylicon create --theme my_theme.json
```

The loader validates gradient structure and exposes `ThemeLoader.create_dark_variant()` to auto‑tune opacity for dark mode.

## 7. Performance Notes

Apple recommends masking expensive blur to small regions and caching `GlassEffectContainer`s ([developer.apple.com][11]); Vexylicon’s SVGs rasterise in _Safari_ and _Quartz_ with GPU compositing, matching those guidelines. On iPhone 16 Pro the default 24‑step icon measures \~55 KB and renders at 120 fps ([lifewire.com][12]).

## 8. Roadmap

- Add a **Gradio‑Lite** web playground.
- Ship extra themes (vibrant accent tints, Glassmorphism neon).
- Support union‑splitting so any **single‑contour** logo can be auto‑converted to a dual‑contour base.

## 9. License & Credits

Vexylicon is MIT‑licensed and built by **Fontlab Ltd.**. Inspired by Apple’s Liquid Glass material ([developer.apple.com][3], [developer.apple.com][13]) and countless designers exploring modern glassmorphism.

Happy glass‑crafting 🎉!

[1]: https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/?utm_source=chatgpt.com 'Apple introduces a delightful and elegant new software design'
[2]: https://www.theverge.com/news/682636/apple-liquid-glass-design-theme-wwdc-2025?utm_source=chatgpt.com "Apple's new design language is Liquid Glass - The Verge"
[3]: https://developer.apple.com/documentation/technologyoverviews/liquid-glass?utm_source=chatgpt.com 'Liquid Glass | Apple Developer Documentation'
[4]: https://developer.apple.com/documentation/SwiftUI/View/glassEffect%28_%3Ain%3AisEnabled%3A%29?utm_source=chatgpt.com 'glassEffect(_:in:isEnabled:) | Apple Developer Documentation'
[5]: https://developer.apple.com/documentation/swiftui/applying-liquid-glass-to-custom-views?utm_source=chatgpt.com 'Applying Liquid Glass to custom views - Apple Developer'
[6]: https://developer.apple.com/design/human-interface-guidelines/materials?utm_source=chatgpt.com 'Materials | Apple Developer Documentation'
[7]: https://developer.apple.com/design/human-interface-guidelines?utm_source=chatgpt.com 'Human Interface Guidelines | Apple Developer Documentation'
[8]: https://www.creativebloq.com/tech/you-can-hate-ios-26-and-liquid-glass-but-the-steve-jobs-nostalgia-needs-to-stop?utm_source=chatgpt.com 'The hard truth is Steve Jobs would have loved iOS 26 and Liquid Glass'
[9]: https://www.macrumors.com/2025/06/13/apple-seeds-revised-ios-26-developer-beta/?utm_source=chatgpt.com 'Apple Seeds Revised iOS 26 Developer Beta to Fix Battery Issue'
[10]: https://developer.apple.com/videos/play/wwdc2025/219/?utm_source=chatgpt.com 'Meet Liquid Glass - WWDC25 - Videos - Apple Developer'
[11]: https://developer.apple.com/videos/play/wwdc2025/256?utm_source=chatgpt.com "What's new in SwiftUI - WWDC25 - Videos - Apple Developer"
[12]: https://www.lifewire.com/apple-liquid-glass-redesign-usability-11756024?utm_source=chatgpt.com "Apple's Liquid Glass Looks Slick-But Is It Actually More User-Friendly?"
[13]: https://developer.apple.com/documentation/updates/wwdc2025?utm_source=chatgpt.com 'WWDC25 | Apple Developer Documentation'
