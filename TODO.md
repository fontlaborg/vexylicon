# TODO

- [ ] **Fix Ruff configuration**  
      – Replace obsolete `extend-exclude` key with `exclude` or `extend` in `pyproject.toml` (see PLAN) :contentReference[oaicite:0]{index=0}
- [ ] **Adopt Loguru for structured logging** following recommended pattern and `serialize=True` option :contentReference[oaicite:1]{index=1}
- [ ] **Refactor theme‑aware mask generation** to duplicate gradients for `light`/`dark` variants and switch via CSS `prefers-color-scheme` and `data-theme` attributes :contentReference[oaicite:2]{index=2}
- [ ] **Improve payload masking**  
      – Clip arbitrary HTML/SVG backgrounds with the existing `innerClip` (`clipPath`) and overlay SVG with `mix-blend-mode: screen` :contentReference[oaicite:3]{index=3}
- [ ] **Gradio Lite demo**  
      – Add `docs/index.html` loading `@gradio/lite` from CDN; expose a single Python function that wraps `VexyliconGenerator` (see PLAN) :contentReference[oaicite:4]{index=4}
- [ ] **End‑to‑end tests** with PyTest & snapshot SVGs to reach ≥ 90 % coverage.
- [ ] **Continuous Integration enhancements**  
      – Add Ruff format & test steps already defined in `.github/workflows` to pre‑commit.  
- [ ] **Documentation**  
      – Update `README.md` with usage, Gradio Lite GIF, and dark/light screenshots.