# Run Gemini Chat
import base64
import json
import logging
import markdown2
import os
import requests
import subprocess
import time

# Google Cloud authentication
from google import genai
from google.genai import types as genai_types
from google.auth import default
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials as OAuth2Credentials

# Google Cloud services
from google.api_core.exceptions import GoogleAPICallError, PermissionDenied
from google.cloud import aiplatform, billing, resourcemanager_v3
from google.cloud.resourcemanager_v3 import types

# Vertex AI
import vertexai
from pyasn1_modules.rfc3279 import characteristic_two_field
from vertexai.generative_models import GenerativeModel, Part, SafetySetting

# IPython and Jupyter
from IPython.display import HTML, clear_output, display, Markdown
import ipywidgets as widgets

# Code highlighting
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

def get_gemini_chat():
    
    llm_project_id = "schare-gemini"

    # Define model options and their corresponding locations
    model_options = {
        "Gemini 2.0 Flash": {
            "model_name": "gemini-2.0-flash-001",
            "locations": ["us-east5","us-central1"]
        }
    }

    # System instructions
    system_instructions = """You are an advanced AI coding expert with extensive knowledge across multiple programming languages, frameworks, and software development practices. Your task is to provide high-quality, professional-grade assistance based on the given context and user's latest message.

    Instructions:
    1. Code Presentation:
      - Always present code within triple backtick blocks (```), specifying the language at the start.
      - Each language should have its own code block and avoid mixing languages. For example, instead of a single html app do a code block for html, css, and js separately. 
    2. Comprehensive Analysis:
      - Analyze the provided code files and chat history thoroughly before responding.
      - Consider architectural implications, potential optimizations, and best practices in your solutions.
    3. Advanced Problem-Solving:
      - Break down complex tasks into logical, manageable steps.
      - Provide algorithmic insights and time/space complexity analysis where relevant.
    4. Detailed Explanations:
      - Offer in-depth explanations using both inline comments and separate markdown sections.
      - Elucidate your reasoning, especially for architectural decisions or non-obvious optimizations.
    5. Best Practices and Optimizations:
      - Proactively suggest improvements, refactoring opportunities, and performance optimizations.
      - Incorporate modern development practices, design patterns, and industry standards in your solutions.
    6. Clarity and Precision:
      - If the user's request is ambiguous, ask targeted questions to clarify requirements before proceeding.
      - Anticipate potential issues or edge cases in your solutions and address them preemptively.
    7. Full File Requests:
       - If the user asks for a full file, return the entire file with any suggested upgrades or fixes.
       - Ensure that the returned file maintains the current logic and structure, only implementing necessary changes.
       - Present the full file in a single code block, preserving all original comments and formatting.
       - After the code block, provide a summary of the changes made and the rationale behind them.

    Provide a comprehensive, expert-level response that addresses the user's latest message while leveraging the full context provided. Your solution should reflect the depth and breadth of knowledge expected from a senior software engineer or technical lead."""

    # Custom CSS for styling
    custom_css = """
    <style>
        .output-container {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
            background-color: #f9f9f9;
        }
        .code-block {
            background-color: #f6f8fa;
            border-radius: 3px;
            padding: 10px;
            font-family: monospace;
            white-space: pre-wrap;
            overflow-x: auto;
        }
        .user-question {
            font-style: italic;
            color: #555;
            margin-bottom: 10px;
        }
        .model-info {
            font-weight: bold;
            color: #0066cc;
            margin-bottom: 10px;
        }
        .markdown-body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji';
            font-size: 16px;
            line-height: 1.5;
            word-wrap: break-word;
        }
        .markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4, .markdown-body h5, .markdown-body h6 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }
        .markdown-body code {
            padding: 0.2em 0.4em;
            margin: 0;
            font-size: 85%;
            background-color: rgba(175, 184, 193, 0.2);
            border-radius: 6px;
        }
        .markdown-body pre {
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            background-color: #f6f8fa;
            border-radius: 6px;
        }
        .markdown-body pre code {
            display: inline;
            max-width: auto;
            padding: 0;
            margin: 0;
            overflow: visible;
            line-height: inherit;
            word-wrap: normal;
            background-color: transparent;
            border: 0;
        }
    </style>
    """

    # Function to format code with syntax highlighting
    def format_code(code, language=None):
        try:
            if language:
                lexer = get_lexer_by_name(language, stripall=True)
            else:
                lexer = guess_lexer(code)
            formatter = HtmlFormatter(style="friendly", linenos=False, cssclass="code-block")
            return highlight(code, lexer, formatter)
        except ClassNotFound:
            # If language detection fails, return plain text
            return f'<pre class="code-block">{code}</pre>'

    # Function to process and format the AI response
    def process_ai_response(response):
        parts = response.split("```")
        formatted_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                # This is not a code block, render it as markdown
                html_content = markdown2.markdown(part, extras=["fenced-code-blocks", "tables"])
                formatted_parts.append(f'<div class="markdown-body">{html_content}</div>')
            else:
                # This is a code block
                lines = part.split("\n")
                if len(lines) > 1:
                    language = lines[0].strip()
                    code = "\n".join(lines[1:])
                    formatted_parts.append(format_code(code, language))
                else:
                    formatted_parts.append(format_code(part))
        return "".join(formatted_parts)

    # Create dropdowns
    chat_model_dropdown = widgets.Dropdown(
        options=list(model_options.keys()),
        description='Select Model:',
        style={'description_width': 'initial'}
    )

    chat_location_dropdown = widgets.Dropdown(
        description='Select Location:',
        style={'description_width': 'initial'}
    )

    # Function to update location dropdown based on selected model
    def update_locations(*args):
        model = chat_model_dropdown.value
        chat_location_dropdown.options = model_options[model]['locations']
        chat_location_dropdown.value = model_options[model]['locations'][0]

    # Attach the update function to the model dropdown
    chat_model_dropdown.observe(update_locations, names='value')

    # Initialize the location dropdown
    update_locations()

    # Generation configurations
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 0.7,
        "top_p": 0.95,
    }

    safety_settings = [
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE
        ),
    ]

    # Function to generate content using Gemini 1.5
    def generate_gemini_1_5(user_input):
        access_token = get_access_token()
        
        credentials = OAuth2Credentials(
            token=access_token,
            refresh_token=None,
            token_uri=None,
            client_id=None,
            client_secret=None,
            scopes=None
        )

        # Initialize Vertex AI with credentials
        vertexai.init(
            project=llm_project_id, 
            location=chat_location_dropdown.value,
            credentials=credentials
        )
        
        model = GenerativeModel(model_options[chat_model_dropdown.value]['model_name'])

        # Combine system instructions and user input
        combined_input = f"""Instructions for AI Assistant:
    {system_instructions}

    User Question:
    {user_input}

    AI Assistant: Certainly! I'll provide a comprehensive, expert-level response to your question while following the given instructions. Let's begin:

    """

        responses = model.generate_content(
            [combined_input],
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=True,
        )

        full_response = ""
        for response in responses:
            full_response += response.text
        return full_response

    # Function to generate content using Gemini 2.0
    def generate_gemini_2_0(user_input):
        access_token = get_access_token()
        
        credentials = OAuth2Credentials(
            token=access_token,
            refresh_token=None,
            token_uri=None,
            client_id=None,
            client_secret=None,
            scopes=None
        )

        # Initialize Vertex AI with credentials
        vertexai.init(
            project=llm_project_id, 
            location=chat_location_dropdown.value,
            credentials=credentials
        )
        
        model = GenerativeModel(model_options[chat_model_dropdown.value]['model_name'])

        # Combine system instructions and user input
        combined_input = f"""Instructions for AI Assistant:
    {system_instructions}

    User Question:
    {user_input}

    AI Assistant: Certainly! I'll provide a comprehensive, expert-level response to your question while following the given instructions. Let's begin:

    """

        responses = model.generate_content(
            [combined_input],
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=True,
        )

        full_response = ""
        for response in responses:
            full_response += response.text
        return full_response

    def get_access_token():
        # Run the gcloud command and capture output
        cmd = "gcloud auth print-access-token --impersonate-service-account=gemini-only@schare-gemini.iam.gserviceaccount.com"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)

        # Return the token (stripped of whitespace)
        return result.stdout.strip()

    # Update the run_generation function to handle errors
    def run_generation(b):
        with chat_output_area:
            chat_output_area.clear_output(wait=True)
            display(HTML(custom_css))
            display(HTML(f"""
            <div class="output-container">
                <div class="model-info">Generating with {chat_model_dropdown.value} in {chat_location_dropdown.value}</div>
                <div class="user-question">User Question: {chat_user_input.value}</div>
            </div>
            """))

            try:
                if chat_model_dropdown.value == "Gemini 1.5 Flash":
                    response = generate_gemini_1_5(chat_user_input.value)
                elif chat_model_dropdown.value == "Gemini 2.0 Flash":
                    response = generate_gemini_2_0(chat_user_input.value)
                else:
                    response = generate_claude(chat_user_input.value)

                formatted_response = process_ai_response(response)
                display(HTML(f"""
                <div class="output-container">
                    <h3>AI Response:</h3>
                    {formatted_response}
                </div>
                """))
            except Exception as e:
                logging.exception("An error occurred during generation")
                display(HTML(f"""
                <div class="output-container error">
                    <h3>Error:</h3>
                    <p>An error occurred during generation: {str(e)}</p>
                </div>
                """))

    # Create a text area for user input
    chat_user_input = widgets.Textarea(
        value='',
        placeholder='Type your coding question here...',
        description='Question:',
        disabled=False,
        layout=widgets.Layout(width='100%', height='150px')
    )

    # Create an output widget
    chat_output_area = widgets.Output()

    # Create a button to trigger generation
    chat_generate_button = widgets.Button(description="Generate")
    chat_generate_button.on_click(run_generation)

    return chat_model_dropdown, chat_location_dropdown, chat_user_input, chat_generate_button, chat_output_area

