# PLAN — Vexylicon v0.2 Roadmap

> Purpose: provide every detail a junior dev needs to implement the next iteration.

---

## 1. Code‑quality & Infrastructure

### 1.1. 1.1 Ruff configuration bug‑fix  
*Problem*  
CI fails because Ruff ≥ 0.3 removed the `extend-exclude` key. :contentReference[oaicite:5]{index=5}  

*Steps*  
1. In **pyproject.toml** `[tool.ruff]` replace  
   ```toml
   extend-exclude = [".git", ".venv", "venv", "dist", "build"]
````

with:

```toml
exclude = [".git", ".venv", "venv", "dist", "build"]
```

or, if inheritance is needed: `extend = "../pyproject.toml"`.
2\. Run `uv pip install -U ruff` and `ruff check` locally until clean.

### 1.2. 1.2 Structured logging with Loguru

Loguru allows JSON/colour logs without boilerplate. ([betterstack.com][1], [github.com][2])

*Implementation*

```python
from loguru import logger
logger.remove()               # drop default
logger.add("vexylicon.log", serialize=True, rotation="1 week")
```

Replace every `logging` import with `loguru`. Keep `.cli` colourful via `rich`.

---

## 2. SVG Engine Enhancements

### 2.1. 2.1 Theme‑aware masks

Current code merely creates empty `.theme-light/.theme-dark` `<g>` groups.
*Goal*: duplicate each gradient twice — `<id>-light`, `<id>-dark` — tuned for contrasting backgrounds, then reference via CSS variables.

*Algorithm*

1. Iterate over `theme.gradients.items()`.
2. For each gradient, produce a deep copy with suffixes and tweak stop opacities (`* 0.9` for light, `* 1.2` for dark).
3. Add a `<style>` block with:

   ```css
   [data-theme="light"] .use-dark { display:none; }
   [data-theme="dark"]  .use-light { display:none; }
   @media (prefers-color-scheme: dark) { ... }  /* MDN pattern */ :contentReference[oaicite:7]{index=7}
   ```
4. Tag every `<use>` with `class="use-light"` or `use-dark`.

### 2.2. 2.2 Payload masking & HTML backdrops

Use existing `innerClip` to mask arbitrary content:

#### 2.2.1. 2.2.1 Pure HTML background

```html
<div id="html-bg" style="clip-path: url(#innerClip);">
  <!-- CSS / image pattern here -->
</div>
<svg ... id="glass-overlay">…</svg>
```

– `clip-path` works on HTML if defined with `path('...')` or by referencing SVG `<clipPath>` ID. ([dev.to][3], [stackoverflow.com][4], [sarasoueidan.com][5])

#### 2.2.2. 2.2.2 Inline with `<foreignObject>`

Inside the base SVG:

```xml
<foreignObject clip-path="url(#innerClip)" width="100%" height="100%">
   <div xmlns="http://www.w3.org/1999/xhtml" class="payload-html">…</div>
</foreignObject>
```

Layer order: HTML/bg → clipped glass group → border.

*Blend effect*: keep `mix-blend-mode: screen` for steps (MDN) ([developer.mozilla.org][6]).

---

## 3. Gradio Lite Integration

### 3.1. 3.1 Why Lite?

Runs Python via Pyodide in the browser; zero backend. ([gradio.app][7])

### 3.2. 3.2 File layout

```
docs/
└── index.html   # shipped via GitHub Pages
```

### 3.3. 3.3 index.html skeleton

````html
<!DOCTYPE html><html><head>
  <script src="https://cdn.jsdelivr.net/npm/@gradio/lite@latest/dist/lite.js"></script> <!-- :contentReference[oaicite:11]{index=11} -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@gradio/lite@latest/dist/lite.css">
</head><body>
<gradio-lite>
```python
from vexylicon import VexyliconGenerator, VexyliconParams

def make_glass(payload_svg: str | None, steps: int, theme: str):
    gen = VexyliconGenerator(theme=theme,
                             params=VexyliconParams(steps=steps))
    return gen.generate(payload_svg=payload_svg)

import gradio as gr
demo = gr.Interface(
    fn=make_glass,
    inputs=[
        gr.File(label="Payload SVG", file_types=[".svg"], optional=True),
        gr.Slider(8, 32, value=24, step=2, label="Steps"),
        gr.Dropdown(["default", "default-dark"], value="default", label="Theme")
    ],
    outputs=gr.Code(label="Generated SVG", language="xml"),
)
demo
```</gradio-lite>
</body></html>
````

### 3.4. 3.4 Dev instructions

1. `uv pip install gradio` — **only** a dev dependency; production uses CDN.
2. Run `python -m http.server -d docs` and open `localhost:8000` to test.

---

## 4. Testing Strategy

| Layer                | Tool                        | Notes                                            |
| -------------------- | --------------------------- | ------------------------------------------------ |
| Path math            | `pytest` units              | Validate `generate_ring_paths` against fixtures. |
| SVGProcessor DOM ops | `pytest` units              | Parse‐mutate‐serialize round‑trip.               |
| CLI                  | `pytest` w/ `click.testing` | Smoke test commands.                             |
| Gradio Lite          | Playwright                  | Snapshot render.                                 |

Aim for **≥ 90 %** coverage, enforced in CI (`--cov-fail-under=90`).

---

## 5. Documentation & CI

* **README**: add Asciinema GIF of CLI and screenshot of Gradio demo.
* **GitHub Actions** already lint & test on 3 Python versions; extend to build `docs` artefact after tests.
* Publish demo automatically to **gh‑pages** branch on push to `main`.

---

## 6. Timeline

| Week | Deliverable                      |
| ---- | -------------------------------- |
| 1    | Ruff fix + Loguru refactor       |
| 2    | Theme‑aware gradients & CSS      |
| 3    | Payload masking enhancements     |
| 4    | Gradio Lite MVP & docs           |
| 5    | Full test suite + CI badges      |
| 6    | Code freeze, version bump to 0.2 |

---

## 7. References

1. Gradio Lite overview ([gradio.app][7])
2. Gradio Lite CDN docs ([gradio.app][8])
3. SVG clipPath tutorial ([dev.to][3])
4. Advanced clipping article ([sarasoueidan.com][5])
5. StackOverflow clip‑mask Q\&A ([stackoverflow.com][4])
6. CSS `mix-blend-mode` spec ([developer.mozilla.org][6])
7. CSS `prefers-color-scheme` MDN ([developer.mozilla.org][9])
8. Theme toggle article ([whitep4nth3r.com][10])
9. Ruff configuration docs ([docs.astral.sh][11])
10. Ruff settings docs ([docs.astral.sh][12])
11. Loguru guide ([betterstack.com][1])
12. Loguru GitHub README ([github.com][2])
13. Glass‑effect walkthrough ([css-tricks.com][13])
14. Gradio Quick‑start (contextual) ([gradio.app][14])
15. Existing TODO for context&#x20;

```

---

**Next step**: commit these files, then begin with the Ruff fix so CI turns green.


::contentReference[oaicite:27]{index=27}
```

[1]: https://betterstack.com/community/guides/logging/loguru/?utm_source=chatgpt.com "A Complete Guide to Logging in Python with Loguru - Better Stack"
[2]: https://github.com/Delgan/loguru?utm_source=chatgpt.com "Delgan/loguru: Python logging made (stupidly) simple - GitHub"
[3]: https://dev.to/alvarosabu/the-magic-of-svg-clip-path-1lf0?utm_source=chatgpt.com "The Magic of SVG Clip-path - DEV Community"
[4]: https://stackoverflow.com/questions/76106935/how-would-i-go-about-clipping-or-masking-an-element-by-the-shape-of-an-svg?utm_source=chatgpt.com "How would I go about clipping or masking an element by the shape ..."
[5]: https://www.sarasoueidan.com/blog/css-svg-clipping/?utm_source=chatgpt.com "Clipping in CSS and SVG — The clip-path Property and <clipPath ..."
[6]: https://developer.mozilla.org/en-US/docs/Web/CSS/mix-blend-mode?utm_source=chatgpt.com "mix-blend-mode - CSS - MDN Web Docs"
[7]: https://www.gradio.app/guides/gradio-lite?utm_source=chatgpt.com "Gradio Lite"
[8]: https://www.gradio.app/main/docs/js/lite?utm_source=chatgpt.com "Gradio lite JS Docs"
[9]: https://developer.mozilla.org/en-US/docs/Web/CSS/%40media/prefers-color-scheme?utm_source=chatgpt.com "prefers-color-scheme - CSS - MDN Web Docs - Mozilla"
[10]: https://whitep4nth3r.com/blog/best-light-dark-mode-theme-toggle-javascript/?utm_source=chatgpt.com "The best light/dark mode theme toggle in JavaScript"
[11]: https://docs.astral.sh/ruff/configuration/?utm_source=chatgpt.com "Configuring Ruff - Astral Docs"
[12]: https://docs.astral.sh/ruff/settings/?utm_source=chatgpt.com "Settings | Ruff - Astral Docs"
[13]: https://css-tricks.com/making-a-realistic-glass-effect-with-svg/?utm_source=chatgpt.com "Making a Realistic Glass Effect with SVG - CSS-Tricks"
[14]: https://www.gradio.app/guides/quickstart?utm_source=chatgpt.com "Quickstart - Gradio"