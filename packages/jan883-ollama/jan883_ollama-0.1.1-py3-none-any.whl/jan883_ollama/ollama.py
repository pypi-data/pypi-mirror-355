import requests
import json
from typing import Union
from enum import Enum


# %%
class OutputFormat(Enum):
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain text"
    JSON = "json"

def ask_ollama(
    user_prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
    model: str = "gemma3:4b",
    output_format: OutputFormat = OutputFormat.PLAIN_TEXT,
    temp: float = 0,
    max_tokens: int = 0,
) -> Union[str, bool]:
    """
    Asynchronously send a prompt to an Ollama LLM model and return the response in the specified format.

    Args:
        user_prompt (str): The user's prompt to send to the model.
        system_prompt (str): The system prompt to guide the model's behavior.
        model (str): The name of the Ollama model to use.
        output_format (OutputFormat): The required output format (MARKDOWN, PLAIN_TEXT, JSON).
        temp (float): The temperature for sampling (creativity).
        max_tokens (int): The maximum number of tokens to generate.

    Returns:
        str: The model's response in the specified format, or False if an error occurs.
    """
    # Combine system prompt and output format instruction
    format_instruction = {
        OutputFormat.MARKDOWN: "Respond in valid Markdown.",
        OutputFormat.PLAIN_TEXT: "Respond in plain text only.",
        OutputFormat.JSON: "Respond in valid JSON format."
    }[output_format]

    full_system_prompt = f"{system_prompt}\n{format_instruction}"

    url = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "system": full_system_prompt,
        "prompt": user_prompt,
        "max_tokens": max_tokens,
        "stream": False,
        "options": {
            "temperature": temp,
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except requests.RequestException as e:
        print("Error:", e)
        return False
