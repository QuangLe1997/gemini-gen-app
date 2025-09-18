# Gemini Image Generator

A Python application that generates images using Google Gemini AI. Supports both text-to-image generation and image transformation based on prompts. Available as both command-line interface and GUI.

## Features

- Generate images from text prompts
- Transform existing images with text descriptions
- Support for multiple Gemini models including latest Gemini 2.5 Flash Image
- Multiple interfaces: Command-line, GUI, and Python API
- Model selection and information display
- Environment variable support for API key
- Image preview in GUI

## Available Models

- **gemini-2.5-flash-image-preview** (Recommended) - Latest "Nano Banana" model with advanced editing capabilities
- **gemini-2.0-flash-preview-image-generation** - Previous generation (deprecated Sept 26, 2025)

## Requirements

- Python 3.7+
- google-genai library
- Pillow (PIL)
- tkinter (for GUI, usually included with Python)

## Installation

1. Install required packages:
```bash
pip install google-genai Pillow
```

2. Set up your Gemini API key:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or pass it as a parameter when using the application.

## Usage

### GUI Interface (Recommended for beginners)

Launch the graphical user interface:
```bash
python run_ui.py
```

The GUI provides:
- Easy API key input
- Model selection with information
- File browsing for input/output images
- Text area for prompts
- Image preview
- Progress tracking

### Command Line Interface

#### List available models:
```bash
python gemini_image_generator.py --list-models
```

#### Generate image from text prompt only:
```bash
python gemini_image_generator.py "A beautiful sunset over mountains"
```

#### Transform an existing image:
```bash
python gemini_image_generator.py "Transform this into a cyberpunk style" -i input_image.jpg -o cyberpunk_result.png
```

#### Specify model and API key:
```bash
python gemini_image_generator.py "A robot playing guitar" --model gemini-2.5-flash-image-preview --api-key YOUR_API_KEY -o robot_guitar.png
```

### Python API

```python
from gemini_image_generator import GeminiImageGenerator

# Initialize with API key and model
generator = GeminiImageGenerator(
    api_key="your-api-key",
    model="gemini-2.5-flash-image-preview"
)

# List available models
GeminiImageGenerator.list_available_models()

# Generate image from text
output_path = generator.generate_image_from_prompt(
    "A dragon flying over a castle", 
    "dragon_castle.png"
)

# Transform existing image
output_path = generator.generate_image_with_input(
    "input.jpg",
    "Make this image look like a painting",
    "painted_output.png"
)
```

## Command Line Options

- `prompt` - Text description of desired image (required)
- `-i, --input` - Input image path for transformation (optional)
- `-o, --output` - Output image path (default: generated_image.png)
- `--api-key` - Gemini API key (or use GEMINI_API_KEY env var)
- `--model` - Model to use (default: gemini-2.5-flash-image-preview)
- `--list-models` - Show available models and exit

## Error Handling

The application includes comprehensive error handling for:
- Missing or invalid API key
- Invalid image files
- Unsupported models
- Network errors
- API response errors

## File Structure

- `gemini_image_generator.py` - Main script with CLI and API
- `ui.py` - GUI interface
- `run_ui.py` - Quick launcher for GUI
- `test_gemini.py` - Test script for API validation
- `example_usage.py` - Usage examples
- `requirements.txt` - Package dependencies
- `README.md` - This documentation

## Quick Start

1. Get a Gemini API key from Google AI Studio
2. Set the environment variable: `export GEMINI_API_KEY="your-key"`
3. Run the GUI: `python run_ui.py`
4. Enter your prompt and click "Generate Image"

## Tips

- Use descriptive prompts for better results
- The Gemini 2.5 Flash Image model provides the best quality and features
- For image transformation, provide clear instructions on what to change
- Output images are typically 1024x1024 pixels