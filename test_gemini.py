#!/usr/bin/env python3
"""
Test script for Gemini Image Generator
"""

import os
from gemini_image_generator import GeminiImageGenerator

# Set API key
os.environ['GEMINI_API_KEY'] = "AIzaSyCZXhuko8FOVDZ2qFvhAvBM5irqMyBK7yY"

def test_simple_generation():
    """Test simple text-to-image generation"""
    print("Testing Gemini Image Generation...")
    
    try:
        # Initialize generator
        generator = GeminiImageGenerator()
        
        # Simple test prompt
        prompt = "A cute robot sitting in a garden with flowers, cartoon style"
        output_path = "test_robot.png"
        
        print(f"Generating image with prompt: {prompt}")
        result = generator.generate_image_from_prompt(prompt, output_path)
        print(f"✅ Success! Image saved to: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_simple_generation()
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")