#!/usr/bin/env python3
"""
Gemini Image Generator
A Python script that takes an input image and prompt to generate a new image using Google Gemini AI.
"""

import argparse
import os
import sys
import base64
from typing import Optional

from PIL import Image

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai library not installed. Run: pip install google-genai")
    sys.exit(1)


class GeminiImageGenerator:
    # Available models for image generation with pricing info
    AVAILABLE_MODELS = {
        "gemini-2.5-flash-image-preview": {
            "name": "Gemini 2.5 Flash Image (Nano Banana)",
            "description": "State-of-the-art image generation and editing model with superior capabilities",
            "features": ["Natural language editing", "Character consistency", "Image blending", "1024px resolution"],
            "status": "Latest (Recommended)",
            "pricing": {
                "input_cost_per_1k_chars": 0.00025,  # $0.000250 per 1K characters
                "output_cost_per_image": 0.002734375  # $0.002734375 per image (1024x1024)
            }
        },
        "gemini-2.0-flash-preview-image-generation": {
            "name": "Gemini 2.0 Flash Image",
            "description": "Previous generation image model",
            "features": ["Basic image generation", "Text-to-image"],
            "status": "Deprecated (Sept 26, 2025)",
            "pricing": {
                "input_cost_per_1k_chars": 0.00025,
                "output_cost_per_image": 0.002734375
            }
        }
    }

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash-image-preview"):
        """Initialize Gemini Image Generator
        
        Args:
            api_key: Gemini API key. If None, will try to get from GEMINI_API_KEY environment variable
            model: Model to use for image generation. Default is gemini-2.5-flash-image-preview
        """
        if not api_key:
            api_key = os.getenv('GEMINI_API_KEY')

        if not api_key:
            raise ValueError("API key is required. Set GEMINI_API_KEY environment variable or pass api_key parameter")

        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model '{model}' not supported. Available models: {list(self.AVAILABLE_MODELS.keys())}")

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.total_cost = 0.0

    @classmethod
    def list_available_models(cls):
        """List all available models with their information"""
        print("\nAvailable Gemini Image Generation Models:")
        print("=" * 50)
        for model_id, info in cls.AVAILABLE_MODELS.items():
            print(f"\nModel ID: {model_id}")
            print(f"Name: {info['name']}")
            print(f"Status: {info['status']}")
            print(f"Description: {info['description']}")
            print(f"Features: {', '.join(info['features'])}")
            pricing = info.get('pricing', {})
            if pricing:
                print(f"Input cost: ${pricing.get('input_cost_per_1k_chars', 0):.6f} per 1K characters")
                print(f"Output cost: ${pricing.get('output_cost_per_image', 0):.6f} per image")
        print("\n" + "=" * 50)

    def load_image(self, image_path: str) -> tuple[bytes, str]:
        """Load and convert image to bytes with proper MIME type detection
        
        Args:
            image_path: Path to input image
            
        Returns:
            Tuple of (image data as bytes, mime_type)
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Detect image format
        try:
            with Image.open(image_path) as img:
                format_map = {
                    'JPEG': 'image/jpeg',
                    'PNG': 'image/png', 
                    'GIF': 'image/gif',
                    'BMP': 'image/bmp',
                    'WEBP': 'image/webp'
                }
                mime_type = format_map.get(img.format, 'image/jpeg')  # Default to jpeg
        except Exception:
            mime_type = 'image/jpeg'  # Fallback

        with open(image_path, 'rb') as f:
            return f.read(), mime_type

    def calculate_cost(self, prompt: str, has_input_image: bool = False) -> dict:
        """Calculate the estimated cost for the request
        
        Args:
            prompt: Text prompt
            has_input_image: Whether request includes input image
            
        Returns:
            Dict with cost breakdown
        """
        pricing = self.AVAILABLE_MODELS[self.model]["pricing"]
        
        # Calculate input cost (text prompt)
        input_chars = len(prompt)
        input_cost = (input_chars / 1000) * pricing["input_cost_per_1k_chars"]
        
        # Output cost (generated image)
        output_cost = pricing["output_cost_per_image"]
        
        # Input image processing cost (if any) - same as output cost
        input_image_cost = pricing["output_cost_per_image"] if has_input_image else 0
        
        total = input_cost + output_cost + input_image_cost
        
        return {
            "input_text_cost": input_cost,
            "input_image_cost": input_image_cost, 
            "output_image_cost": output_cost,
            "total_cost": total,
            "input_chars": input_chars
        }

    def generate_image_from_prompt(self, prompt: str, output_path: str = "generated_image.png") -> str:
        """Generate image from text prompt only
        
        Args:
            prompt: Text description of desired image
            output_path: Path to save generated image
            
        Returns:
            Path to saved image
        """
        # Calculate and display cost
        cost_info = self.calculate_cost(prompt, has_input_image=False)
        print(f"\n💰 Cost Breakdown:")
        print(f"   Input text ({cost_info['input_chars']} chars): ${cost_info['input_text_cost']:.6f}")
        print(f"   Output image: ${cost_info['output_image_cost']:.6f}")
        print(f"   Total: ${cost_info['total_cost']:.6f}")
        self.total_cost += cost_info['total_cost']
        print(f"   Session total: ${self.total_cost:.6f}\n")

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt],
            )

            if not response:
                raise ValueError("No response received from Gemini API")
            
            if not response.candidates:
                raise ValueError("No candidates in response")

            # Extract image data from response
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Only process image parts with substantial data
                        if part.inline_data.mime_type.startswith('image/') and len(part.inline_data.data) > 1000:
                            # The data is already bytes, not base64 string
                            if isinstance(part.inline_data.data, bytes):
                                image_data = part.inline_data.data
                            else:
                                # Fallback: try base64 decode
                                try:
                                    image_data = base64.b64decode(part.inline_data.data)
                                except Exception:
                                    continue
                            
                            with open(output_path, 'wb') as f:
                                f.write(image_data)
                            print(f"Image generated and saved to: {output_path}")
                            return output_path

            raise ValueError("No image generated in response")

        except Exception as e:
            raise RuntimeError(f"Failed to generate image: {str(e)}")

    def generate_image_with_input(self, input_image_path: str, prompt: str,
                                  output_path: str = "generated_image.png") -> str:
        """Generate image based on input image and prompt
        
        Args:
            input_image_path: Path to input image
            prompt: Text description for image modification/generation
            output_path: Path to save generated image
            
        Returns:
            Path to saved image
        """
        # Calculate and display cost
        cost_info = self.calculate_cost(prompt, has_input_image=True)
        print(f"\n💰 Cost Breakdown:")
        print(f"   Input text ({cost_info['input_chars']} chars): ${cost_info['input_text_cost']:.6f}")
        print(f"   Input image processing: ${cost_info['input_image_cost']:.6f}")
        print(f"   Output image: ${cost_info['output_image_cost']:.6f}")
        print(f"   Total: ${cost_info['total_cost']:.6f}")
        self.total_cost += cost_info['total_cost']
        print(f"   Session total: ${self.total_cost:.6f}\n")

        try:
            # Load input image
            image_data, mime_type = self.load_image(input_image_path)

            # Create content with both image and text
            contents = [
                types.Part.from_bytes(data=image_data, mime_type=mime_type),
                prompt
            ]

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
            )

            if not response:
                raise ValueError("No response received from Gemini API")
            
            if not response.candidates:
                raise ValueError("No candidates in response")

            # Extract image data from response
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Only process image parts with substantial data
                        if part.inline_data.mime_type.startswith('image/') and len(part.inline_data.data) > 1000:
                            # The data is already bytes, not base64 string
                            if isinstance(part.inline_data.data, bytes):
                                image_data = part.inline_data.data
                            else:
                                # Fallback: try base64 decode
                                try:
                                    image_data = base64.b64decode(part.inline_data.data)
                                except Exception:
                                    continue
                            
                            with open(output_path, 'wb') as f:
                                f.write(image_data)
                            print(f"Image generated and saved to: {output_path}")
                            return output_path

            raise ValueError("No image generated in response")

        except Exception as e:
            raise RuntimeError(f"Failed to generate image: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Generate images using Google Gemini AI")
    parser.add_argument("prompt", help="Text prompt describing the desired image")
    parser.add_argument("-i", "--input", help="Input image path (optional)")
    parser.add_argument("-o", "--output", default="generated_image.png", help="Output image path")
    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--model", default="gemini-2.5-flash-image-preview", 
                       help="Model to use for image generation")
    parser.add_argument("--list-models", action="store_true", 
                       help="List available models and exit")

    args = parser.parse_args()
    
    # Handle list models command
    if args.list_models:
        GeminiImageGenerator.list_available_models()
        sys.exit(0)

    try:
        # Initialize generator
        generator = GeminiImageGenerator(api_key=args.api_key, model=args.model)

        # Generate image
        if args.input:
            print(f"Generating image based on input: {args.input}")
            print(f"Prompt: {args.prompt}")
            output_path = generator.generate_image_with_input(args.input, args.prompt, args.output)
        else:
            print(f"Generating image from prompt: {args.prompt}")
            output_path = generator.generate_image_from_prompt(args.prompt, args.output)

        print(f"Success! Generated image saved to: {output_path}")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
