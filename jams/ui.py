import gradio as gr


def launch_server():
    with gr.Blocks() as root:
        gr.Markdown(
            "Hello World!\n\n"
            "This is a sample application that demonstrates the use of the Job Applications Memo UI."
        )

    root.launch()
