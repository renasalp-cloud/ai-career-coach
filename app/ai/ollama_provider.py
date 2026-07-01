"""Utilities for generating text with a local Ollama model."""

from __future__ import annotations

from ollama import Client

MODEL_NAME = "qwen2.5:7b"


def generate(prompt: str) -> str:
    """Generate text for a prompt using the configured Ollama model.

    Args:
        prompt: The input prompt to send to the model.

    Returns:
        The generated text.

    Raises:
        RuntimeError: If Ollama text generation fails.
    """
    try:
        client = Client()
        response = client.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={
                "temperature": 0.1,
            },
        )
        
        return response.response.strip()
    except Exception as exc:
        raise RuntimeError("Failed to generate text with Ollama.") from exc