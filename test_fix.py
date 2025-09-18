#!/usr/bin/env python3
"""
Test script to verify the image generation fix
"""

import os
from gemini_image_generator import GeminiImageGenerator

def test_image_generation():
    """Test image generation to verify format fix"""
    print("Testing image generation fix...")
    
    # Check if API key is set
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Please set GEMINI_API_KEY environment variable to test")
        return
    
    try:
        generator = GeminiImageGenerator(api_key=api_key)
        
        prompt = "A simple test image of a red circle on white background"
        output_path = "outputs/test_fixed_image.png"
        
        print(f"Generating test image with prompt: {prompt}")
        result = generator.generate_image_from_prompt(prompt, output_path)
        
        # Check if file was created and is valid PNG
        if os.path.exists(result):
            import subprocess
            file_info = subprocess.run(['file', result], capture_output=True, text=True)
            print(f"Generated file info: {file_info.stdout.strip()}")
            
            if "PNG image data" in file_info.stdout:
                print("✅ SUCCESS: Image generated correctly as PNG format!")
            else:
                print("❌ FAILED: Image is not in correct PNG format")
        else:
            print("❌ FAILED: No image file was created")
            
    except Exception as e:
        print(f"❌ FAILED: Error during generation: {e}")

if __name__ == "__main__":
    test_image_generation()