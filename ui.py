#!/usr/bin/env python3
"""
Gemini Image Generator UI
A simple GUI interface for generating images using Google Gemini AI.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import threading
from pathlib import Path

try:
    from gemini_image_generator import GeminiImageGenerator
except ImportError:
    print("Error: Could not import GeminiImageGenerator")
    sys.exit(1)


class GeminiImageGeneratorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini Image Generator")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Variables
        self.api_key_var = tk.StringVar(value=os.getenv('GEMINI_API_KEY', ''))
        self.model_var = tk.StringVar(value="gemini-2.5-flash-image-preview")
        self.input_image_path = tk.StringVar()
        self.output_path = tk.StringVar(value="generated_image.png")
        self.prompt_text = tk.StringVar()
        
        self.generator = None
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Title
        title_label = ttk.Label(main_frame, text="Gemini Image Generator", 
                               font=('TkDefaultFont', 16, 'bold'))
        title_label.grid(row=row, column=0, columnspan=3, pady=(0, 20))
        row += 1
        
        # API Key section
        ttk.Label(main_frame, text="API Key:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.api_key_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, 
                                      show="*", width=50)
        self.api_key_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        row += 1
        
        # Model selection
        ttk.Label(main_frame, text="Model:").grid(row=row, column=0, sticky=tk.W, pady=5)
        model_frame = ttk.Frame(main_frame)
        model_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, 
                                       state="readonly", width=40)
        self.model_combo['values'] = list(GeminiImageGenerator.AVAILABLE_MODELS.keys())
        self.model_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(model_frame, text="Info", command=self.show_model_info).grid(
            row=0, column=1, padx=(5, 0))
        model_frame.columnconfigure(0, weight=1)
        row += 1
        
        # Input image section
        ttk.Label(main_frame, text="Input Image:").grid(row=row, column=0, sticky=tk.W, pady=5)
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_image_path, width=40)
        self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(input_frame, text="Browse", command=self.browse_input_image).grid(
            row=0, column=1, padx=(5, 0))
        ttk.Button(input_frame, text="Clear", command=self.clear_input_image).grid(
            row=0, column=2, padx=(5, 0))
        input_frame.columnconfigure(0, weight=1)
        row += 1
        
        # Prompt section
        ttk.Label(main_frame, text="Prompt:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)
        
        # Create frame for prompt text and scrollbar
        prompt_frame = ttk.Frame(main_frame)
        prompt_frame.grid(row=row, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=(5, 0))
        prompt_frame.columnconfigure(0, weight=1)
        prompt_frame.rowconfigure(0, weight=1)
        
        self.prompt_text_widget = scrolledtext.ScrolledText(prompt_frame, height=4, width=50, wrap=tk.WORD)
        self.prompt_text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        row += 1
        
        # Output path section
        ttk.Label(main_frame, text="Output Path:").grid(row=row, column=0, sticky=tk.W, pady=5)
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path, width=40)
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(output_frame, text="Browse", command=self.browse_output_path).grid(
            row=0, column=1, padx=(5, 0))
        output_frame.columnconfigure(0, weight=1)
        row += 1
        
        # Generate button
        self.generate_btn = ttk.Button(main_frame, text="Generate Image", 
                                      command=self.generate_image)
        self.generate_btn.grid(row=row, column=0, columnspan=2, pady=20)
        row += 1
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready")
        self.status_label.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        # Image preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="Generated Image Preview", padding="5")
        preview_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.preview_label = ttk.Label(preview_frame, text="No image generated yet")
        self.preview_label.grid(row=0, column=0)
        
        # Configure grid weights for expansion
        main_frame.rowconfigure(row, weight=1)
        
    def browse_input_image(self):
        """Browse for input image file"""
        file_path = filedialog.askopenfilename(
            title="Select Input Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.input_image_path.set(file_path)
    
    def clear_input_image(self):
        """Clear input image path"""
        self.input_image_path.set("")
    
    def browse_output_path(self):
        """Browse for output file path"""
        file_path = filedialog.asksaveasfilename(
            title="Save Generated Image As",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.output_path.set(file_path)
    
    def show_model_info(self):
        """Show information about available models"""
        info_window = tk.Toplevel(self.root)
        info_window.title("Model Information")
        info_window.geometry("600x400")
        
        text_widget = scrolledtext.ScrolledText(info_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        info_text = "Available Gemini Image Generation Models:\n"
        info_text += "=" * 50 + "\n\n"
        
        for model_id, info in GeminiImageGenerator.AVAILABLE_MODELS.items():
            info_text += f"Model ID: {model_id}\n"
            info_text += f"Name: {info['name']}\n"
            info_text += f"Status: {info['status']}\n"
            info_text += f"Description: {info['description']}\n"
            info_text += f"Features: {', '.join(info['features'])}\n"
            info_text += "\n" + "-" * 40 + "\n\n"
        
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def show_preview(self, image_path):
        """Show preview of generated image"""
        try:
            # Load and resize image for preview
            image = Image.open(image_path)
            image.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Update preview label
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # Keep a reference
            
        except Exception as e:
            self.preview_label.config(text=f"Error loading preview: {str(e)}", image="")
            self.preview_label.image = None
    
    def generate_image_thread(self):
        """Generate image in separate thread"""
        try:
            # Get values
            api_key = self.api_key_var.get().strip()
            model = self.model_var.get()
            input_path = self.input_image_path.get().strip()
            output_path = self.output_path.get().strip()
            prompt = self.prompt_text_widget.get(1.0, tk.END).strip()
            
            # Validate inputs
            if not api_key:
                raise ValueError("API key is required")
            if not prompt:
                raise ValueError("Prompt is required")
            if not output_path:
                raise ValueError("Output path is required")
            
            # Initialize generator
            self.update_status("Initializing generator...")
            self.generator = GeminiImageGenerator(api_key=api_key, model=model)
            
            # Generate image
            if input_path and os.path.exists(input_path):
                self.update_status("Generating image with input...")
                result_path = self.generator.generate_image_with_input(
                    input_path, prompt, output_path
                )
            else:
                self.update_status("Generating image from prompt...")
                result_path = self.generator.generate_image_from_prompt(
                    prompt, output_path
                )
            
            # Show preview
            self.root.after(0, lambda: self.show_preview(result_path))
            self.update_status(f"Success! Image saved to: {result_path}")
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate image: {str(e)}")
        finally:
            # Re-enable button and stop progress
            self.root.after(0, self.generation_finished)
    
    def generation_finished(self):
        """Called when generation is finished"""
        self.progress.stop()
        self.generate_btn.config(state=tk.NORMAL)
    
    def generate_image(self):
        """Start image generation"""
        # Disable button and start progress
        self.generate_btn.config(state=tk.DISABLED)
        self.progress.start()
        
        # Start generation in separate thread
        thread = threading.Thread(target=self.generate_image_thread)
        thread.daemon = True
        thread.start()


def main():
    root = tk.Tk()
    app = GeminiImageGeneratorUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()