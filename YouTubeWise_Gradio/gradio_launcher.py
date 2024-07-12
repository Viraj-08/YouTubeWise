import gradio as gr
from utils import embed_youtube_video, summarize_video, chat


def main():
    try:
        # Create a Gradio block
        gradio_block = gr.Blocks()

        with gradio_block:
            # Add a Markdown title
            gr.Markdown("""# 📹 YouTubeWise - A YouTube Video Summarizer and Q&A Chatbot 💬 
                        ### Instructions:
                            1. Paste the URL of YouTube video in the text box.
                            2. Click on 'Summarize Video' to generate a summary of the video.
                            3. Once you have a summary, you can ask questions in the chat interface.""")

            # Create a row to hold the input fields and button
            with gr.Row():
                # Add a text box for the user to enter the YouTube video URL
                video_url = gr.Textbox(
                    placeholder="Enter YouTube Video URL",
                    label="YouTube URL",
                    max_lines=1,
                    min_width=1200,
                )
                # Add a submit button to trigger the summarization
                submit_btn = gr.Button("Summarize Video")

            # Create an accordion to display the embedded YouTube video
            with gr.Accordion("YouTube Video", open=False):
                # Add an HTML element to display the embedded YouTube video
                embed_video_html = gr.HTML()

            # Create an accordion to hold the video summary and Q&A sections
            with gr.Accordion("Video Summary"):
                # Add a Markdown element to display the video summary
                video_summary = gr.Markdown(label="Video Summary")

            with gr.Accordion("Q&A"):
                # Create a chat interface for the user to ask questions
                gr.ChatInterface(fn=chat, additional_inputs=[video_url])

            submit_btn.click(
                summarize_video,  # Function to call when the button is clicked
                inputs=[video_url],  # Input(s) for the function
                outputs=[video_summary],  # Output(s) of the function
            )

            submit_btn.click(
                embed_youtube_video, inputs=[video_url], outputs=[embed_video_html]
            )

        # Launch the Gradio interface
        gradio_block.launch(show_api=False, share=False)

    except Exception as e:
        print(f"An error occurred: {e}")


# Run the main function if this script is being executed directly (not imported)
if __name__ == "__main__":
    main()
