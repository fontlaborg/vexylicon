import gradio as gr
from vexylicon.webui import generate_svg

with gr.Blocks(theme=gr.themes.Base()) as demo:
    gr.Markdown("### Vexylicon – glass‑morphism icons")
    payload = gr.File(label="Payload SVG (optional)", type="binary")
    steps = gr.Slider(4, 32, value=24, step=4, label="Bevel steps")
    quality = gr.Dropdown(["low","medium","high","ultra"], label="Quality", value=None)
    theme = gr.Dropdown(["default"], label="Theme")
    btn = gr.Button("Generate")
    out_html = gr.HTML(label="Preview")
    out_file = gr.File(label="Download SVG")

    def _run(payload, steps, quality, theme):
        svg = generate_svg(payload, steps, quality, theme)
        return gr.update(value=svg), (svg, "icon.svg")

    btn.click(_run, [payload, steps, quality, theme], [out_html, out_file])

if __name__ == "__main__":
    demo.launch()