#!/usr/bin/env python3
"""
Quick launcher for Gemini Image Generator UI
"""

import sys
import os

# Add current directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ui import main
    main()
except ImportError as e:
    print(f"Error importing UI: {e}")
    print("Make sure all required packages are installed:")
    print("pip install google-genai Pillow tkinter")
    sys.exit(1)
except Exception as e:
    print(f"Error running UI: {e}")
    sys.exit(1)