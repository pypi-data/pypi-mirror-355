import gradio as gr
from gradio_spreadsheetcomponent import SpreadsheetComponent
from dotenv import load_dotenv
import os
import pandas as pd

def answer_question(file, question):
    if not file or not question:
        return "Please upload a file and enter a question."
    
    # Load the spreadsheet data
    df = pd.read_excel(file.name)
    
    # Create a SpreadsheetComponent instance
    spreadsheet = SpreadsheetComponent(value=df)
    
    # Use the component to answer the question
    return spreadsheet.answer_question(question)

with gr.Blocks() as demo:
    gr.Markdown("# Spreadsheet Question Answering")
    
    with gr.Row():
        file_input = gr.File(label="Upload Spreadsheet", file_types=[".xlsx"])
        question_input = gr.Textbox(label="Ask a Question")
    
    answer_output = gr.Textbox(label="Answer", interactive=False, lines=4)
    
    submit_button = gr.Button("Submit")
    submit_button.click(answer_question, inputs=[file_input, question_input], outputs=answer_output)

    
if __name__ == "__main__":
    demo.launch()
