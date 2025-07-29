"""
Command-line interface for quick-tts.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from .core import text_to_speech


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert text to speech using OpenAI's Text-to-Speech API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  quick-tts "Hello, world!" -o hello.mp3
  quick-tts -f input.txt -o output.wav --voice nova
  quick-tts "Good morning!" --model tts-1
        """.strip()
    )
    
    # Text input options (mutually exclusive)
    text_group = parser.add_mutually_exclusive_group(required=True)
    text_group.add_argument(
        "text",
        nargs="?",
        help="Text to convert to speech"
    )
    text_group.add_argument(
        "-f", "--file",
        type=str,
        help="Read text from file"
    )
    
    # Output options
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="speech.mp3",
        help="Output audio file path (default: speech.mp3)"
    )
    
    # TTS options
    parser.add_argument(
        "--model",
        choices=["tts-1", "tts-1-hd"],
        default="tts-1-hd",
        help="OpenAI TTS model (default: tts-1-hd)"
    )
    
    parser.add_argument(
        "--voice",
        choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        default="alloy",
        help="Voice to use (default: alloy)"
    )
    
    # API key option
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (overrides OPENAI_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    try:
        # Get text input
        if args.text:
            text = args.text
        elif args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File '{args.file}' not found.", file=sys.stderr)
                sys.exit(1)
            
            try:
                text = file_path.read_text(encoding="utf-8").strip()
            except Exception as e:
                print(f"Error reading file '{args.file}': {e}", file=sys.stderr)
                sys.exit(1)
                
            if not text:
                print(f"Error: File '{args.file}' is empty.", file=sys.stderr)
                sys.exit(1)
        
        # Convert text to speech
        output_path = text_to_speech(
            text=text,
            output_file=args.output,
            model=args.model,
            voice=args.voice,
            api_key=args.api_key
        )
        
        print(f"Speech generated successfully: {output_path}")
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
