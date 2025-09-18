#!/usr/bin/env python3
"""
Example usage of Gemini Image Generator
"""

import os
from gemini_image_generator import GeminiImageGenerator

def example_text_to_image():
    """Example: Generate image from text prompt only"""
    print("=== Text to Image Example ===")
    
    # Make sure to set your API key
    # os.environ['GEMINI_API_KEY'] = 'your-api-key-here'
    
    generator = GeminiImageGenerator()
    
    prompt = "A beautiful sunset over a mountain lake with a small wooden dock, photorealistic style"
    output_path = "sunset_lake.png"
    
    try:
        result = generator.generate_image_from_prompt(prompt, output_path)
        print(f"Generated image: {result}")
    except Exception as e:
        print(f"Error: {e}")

def example_image_with_prompt():
    """Example: Generate image based on input image + prompt"""
    print("=== Image + Prompt Example ===")
    
    generator = GeminiImageGenerator()
    
    # You need to provide an input image path
    input_image = "input_image.jpg"  # Replace with actual image path
    prompt = "Transform this image into a cyberpunk style with neon lights and futuristic elements"
    output_path = "cyberpunk_transformation.png"
    
    try:
        if os.path.exists(input_image):
            result = generator.generate_image_with_input(input_image, prompt, output_path)
            print(f"Generated image: {result}")
        else:
            print(f"Input image not found: {input_image}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Set your Gemini API key here or as environment variable
    # os.environ['GEMINI_API_KEY'] = 'your-api-key-here'
    
    print("Gemini Image Generator Examples")
    print("Make sure to set GEMINI_API_KEY environment variable first!")
    
    # Uncomment the examples you want to run:
    # example_text_to_image()
    # example_image_with_prompt()