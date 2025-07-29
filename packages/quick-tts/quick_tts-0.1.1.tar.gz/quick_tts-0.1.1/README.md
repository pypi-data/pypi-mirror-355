# quick-tts

Convert text to speech using OpenAI's Text-to-Speech API. A simple, effective Python package that works as both a library and command-line tool.

## Installation

```bash
pip install quick-tts
```

## Usage

### As a Library

```python
from quick_tts import text_to_speech

# Basic usage
text_to_speech("Hello, world!", "hello.mp3")

# With custom options
text_to_speech(
    text="Good morning!",
    output_file="morning.wav",
    model="tts-1-hd",
    voice="nova"
)
```

### As a Command-Line Tool

```bash
# Basic usage
quick-tts "Hello, world!" -o hello.mp3

# Read from file
quick-tts -f input.txt -o output.mp3

# Custom voice and model
quick-tts "Welcome!" --voice nova --model tts-1-hd -o welcome.mp3

# See all options
quick-tts --help
```

## Configuration

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY=sk-your-api-key-here
```

Or pass it directly:

```python
text_to_speech("Hello!", "hello.mp3", api_key="sk-your-api-key")
```

## API Reference

### `text_to_speech(text, output_file="speech.mp3", model="tts-1-hd", voice="alloy", api_key=None)`

Convert text to speech using OpenAI's API.

**Parameters:**
- `text` (str): The text to convert to speech
- `output_file` (str|Path): Path to save the audio file (default: "speech.mp3")
- `model` (str): OpenAI TTS model ("tts-1" or "tts-1-hd", default: "tts-1-hd")
- `voice` (str): Voice to use ("alloy", "echo", "fable", "onyx", "nova", "shimmer", default: "alloy")
- `api_key` (str, optional): OpenAI API key (uses OPENAI_API_KEY env var if not provided)

**Returns:**
- `str`: Absolute path to the generated audio file

## Supported Voices

- **alloy** - Balanced, versatile voice
- **echo** - Clear, professional tone
- **fable** - Warm, storytelling quality
- **onyx** - Deep, authoritative voice
- **nova** - Bright, engaging tone
- **shimmer** - Soft, pleasant voice

## Models

- **tts-1** - Standard quality, faster generation
- **tts-1-hd** - High definition quality, more detailed audio

## Requirements

- Python 3.8+
- OpenAI API key
- `openai>=1.86.0`

## License

MIT License - see LICENSE file for details.

## Contributing

Issues and pull requests welcome at [GitHub](https://github.com/diogoseca/quick-tts).
