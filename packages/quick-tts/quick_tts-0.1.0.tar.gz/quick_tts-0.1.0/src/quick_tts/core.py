"""
Core text-to-speech functionality using OpenAI's API.
"""

import os
from pathlib import Path
from typing import Union, Optional

try:
    from openai import OpenAI
except ImportError as exc:
    raise ImportError("openai package missing. Run 'pip install --upgrade openai'.") from exc


def text_to_speech(
    text: str,
    output_file: Union[str, Path] = "speech.mp3",
    model: str = "tts-1-hd",
    voice: str = "alloy",
    api_key: Optional[str] = None,
) -> str:
    """
    Convert text to speech using OpenAI's Text-to-Speech API.
    
    Args:
        text: The text to convert to speech
        output_file: Path to save the audio file (default: "speech.mp3")
        model: OpenAI TTS model to use ("tts-1" or "tts-1-hd", default: "tts-1-hd")
        voice: Voice to use ("alloy", "echo", "fable", "onyx", "nova", "shimmer", default: "alloy")
        api_key: OpenAI API key (optional, uses OPENAI_API_KEY env var if not provided)
    
    Returns:
        str: Path to the generated audio file
        
    Raises:
        ValueError: If API key is not provided or found in environment
        Exception: If OpenAI API call fails
    """
    if not text.strip():
        raise ValueError("Text cannot be empty")
    
    # Get API key from parameter or environment
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
            "or pass api_key parameter."
        )
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Convert output_file to Path object
    output_path = Path(output_file)
    
    try:
        # Generate speech
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        
        # Save to file
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        return str(output_path.absolute())
        
    except Exception as exc:
        raise Exception(f"Failed to generate speech: {exc}") from exc
