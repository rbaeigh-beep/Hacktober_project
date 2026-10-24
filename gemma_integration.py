import os
from dotenv import load_dotenv
from google import genai

# Load environment variables from your local hidden .env file
load_dotenv()

def ask_gemma(prompt_text):
    """
    A reusable function that accepts a prompt string 
    and returns Gemma 4's text response.
    """
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model="gemma-4-e2b-instruct", 
            contents=prompt_text
        )
        return response.text
    except Exception as e:
        return f" Gemma Error: {e}"
