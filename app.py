"""
app.py — Gradio web interface for the UMD Dining Unofficial Guide
Run with: python app.py
Then open: http://localhost:7860
"""

import gradio as gr
from query import ask


def handle_query(question):
    if not question.strip():
        return "Please enter a question.", ""
    try:
        result = ask(question)
        answer = result["answer"]
        sources = "\n".join(f"• {s}" for s in result["sources"])
        return answer, sources
    except Exception as e:
        return f"Error: {str(e)}", ""


examples = [
    ["Have students reported vegetarian food being mislabeled at UMD dining halls?"],
    ["What allergen-free options does UMD dining offer for students with food allergies?"],
    ["Which UMD dining hall gets the most crowded during peak hours?"],
    ["Have there been any food safety or health incidents at UMD dining?"],
    ["What do students say about vegan food options at UMD dining halls?"],
]

with gr.Blocks(title="UMD Dining Unofficial Guide") as demo:
    gr.Markdown("""
    # 🍽️ UMD Dining Unofficial Guide
    **Ask anything about UMD dining halls** — food quality, vegan/vegetarian options, allergens, crowding, food safety, and more.

    Answers are grounded in real student reviews, Diamondback articles, and UMD Dining Services documentation.
    """)

    with gr.Row():
        with gr.Column():
            question_input = gr.Textbox(
                label="Your Question",
                placeholder="e.g. Is the food at Yahentamitsi good for vegetarians?",
                lines=2
            )
            submit_btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        with gr.Column():
            answer_output = gr.Textbox(
                label="Answer",
                lines=8,
                interactive=False
            )
        with gr.Column():
            sources_output = gr.Textbox(
                label="Retrieved From",
                lines=8,
                interactive=False
            )

    gr.Examples(
        examples=examples,
        inputs=question_input,
        label="Example Questions"
    )

    submit_btn.click(fn=handle_query, inputs=question_input, outputs=[answer_output, sources_output])
    question_input.submit(fn=handle_query, inputs=question_input, outputs=[answer_output, sources_output])

if __name__ == "__main__":
    demo.launch()