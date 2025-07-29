"""
quick-tts: Convert text to speech using OpenAI's Text-to-Speech API.

A simple, effective Python package for text-to-speech conversion using OpenAI's API.
Can be used as a library or command-line tool.
"""

from .core import text_to_speech

__version__ = "0.1.0"
__all__ = ["text_to_speech"]
