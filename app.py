#!/usr/bin/env python3
"""
Gemini Image Generator Web UI
Simple web interface for generating images using Google Gemini AI with cost tracking.
"""

import os
import base64
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from gemini_image_generator import GeminiImageGenerator

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global generator instance
generator = None

def init_generator():
    """Initialize the generator with API key"""
    global generator
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return False
    try:
        generator = GeminiImageGenerator(api_key=api_key)
        return True
    except Exception as e:
        print(f"Failed to initialize generator: {e}")
        return False

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/models')
def get_models():
    """Get available models with pricing info"""
    return jsonify(GeminiImageGenerator.AVAILABLE_MODELS)

@app.route('/api/generate', methods=['POST'])
def generate_image():
    """Generate image endpoint"""
    if not generator:
        if not init_generator():
            return jsonify({'error': 'Generator not initialized. Check GEMINI_API_KEY'}), 500
    
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        model = data.get('model', 'gemini-2.5-flash-image-preview')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Update model if different
        if generator.model != model:
            generator.model = model
        
        # Calculate cost
        cost_info = generator.calculate_cost(prompt, has_input_image=False)
        
        # Generate image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            output_path = generator.generate_image_from_prompt(prompt, tmp_file.name)
            
            # Read generated image and encode as base64
            with open(output_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Clean up temp file
            os.unlink(output_path)
        
        # Update session total
        generator.total_cost += cost_info['total_cost']
        
        return jsonify({
            'success': True,
            'image': f"data:image/png;base64,{image_data}",
            'cost_info': cost_info,
            'session_total': generator.total_cost
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_with_input', methods=['POST'])
def generate_with_input():
    """Generate image with input image endpoint"""
    if not generator:
        if not init_generator():
            return jsonify({'error': 'Generator not initialized. Check GEMINI_API_KEY'}), 500
    
    try:
        # Get form data
        prompt = request.form.get('prompt', '').strip()
        model = request.form.get('model', 'gemini-2.5-flash-image-preview')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Get uploaded file
        if 'image' not in request.files:
            return jsonify({'error': 'Input image is required'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Update model if different
        if generator.model != model:
            generator.model = model
        
        # Calculate cost
        cost_info = generator.calculate_cost(prompt, has_input_image=True)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as input_tmp:
            file.save(input_tmp.name)
            
            # Generate image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as output_tmp:
                output_path = generator.generate_image_with_input(
                    input_tmp.name, prompt, output_tmp.name
                )
                
                # Read generated image and encode as base64
                with open(output_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                # Clean up temp files
                os.unlink(input_tmp.name)
                os.unlink(output_path)
        
        # Update session total
        generator.total_cost += cost_info['total_cost']
        
        return jsonify({
            'success': True,
            'image': f"data:image/png;base64,{image_data}",
            'cost_info': cost_info,
            'session_total': generator.total_cost
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset_cost')
def reset_cost():
    """Reset session cost counter"""
    if generator:
        generator.total_cost = 0.0
        return jsonify({'success': True, 'session_total': 0.0})
    return jsonify({'error': 'Generator not initialized'}), 500

if __name__ == '__main__':
    print("🚀 Starting Gemini Image Generator Web UI...")
    print("💡 Make sure GEMINI_API_KEY environment variable is set")
    print("🌐 Open http://localhost:3001 in your browser")
    
    app.run(debug=True, host='127.0.0.1', port=3001)