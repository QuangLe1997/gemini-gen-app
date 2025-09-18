#!/usr/bin/env python3
"""
Gemini Image Generator Web API
A simple Flask web API with HTML interface for generating images using Google Gemini AI.
"""

import os
import sys
import uuid
import base64
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import threading
import time

try:
    from gemini_image_generator import GeminiImageGenerator
except ImportError:
    print("Error: Could not import GeminiImageGenerator")
    sys.exit(1)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

# Store active generation tasks
active_tasks = {}

class GenerationTask:
    def __init__(self, task_id):
        self.task_id = task_id
        self.status = "pending"
        self.progress = 0
        self.message = "Task created"
        self.result_path = None
        self.error = None

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Serve the main HTML interface"""
    return render_template('index.html')

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available Gemini models"""
    try:
        models = GeminiImageGenerator.AVAILABLE_MODELS
        return jsonify({
            'success': True,
            'models': models
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate', methods=['POST'])
def generate_image():
    """Generate image from prompt and optional input image"""
    try:
        # Get data from JSON or form
        if request.is_json:
            data = request.get_json()
            api_key = data.get('api_key')
            model = data.get('model', 'gemini-2.5-flash-image-preview')
            prompt = data.get('prompt')
        else:
            api_key = request.form.get('api_key')
            model = request.form.get('model', 'gemini-2.5-flash-image-preview')
            prompt = request.form.get('prompt')
        
        # Validate required fields
        if not api_key:
            return jsonify({'success': False, 'error': 'API key is required'}), 400
        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt is required'}), 400
        
        # Handle file upload
        input_file_path = None
        if 'input_image' in request.files:
            file = request.files['input_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                input_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(input_file_path)
        
        # Create task
        task_id = str(uuid.uuid4())
        task = GenerationTask(task_id)
        active_tasks[task_id] = task
        
        # Start generation in background
        thread = threading.Thread(
            target=generate_image_background,
            args=(task, api_key, model, prompt, input_file_path)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Generation started'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_image_background(task, api_key, model, prompt, input_file_path):
    """Background task for image generation"""
    try:
        task.status = "initializing"
        task.progress = 10
        task.message = "Initializing generator..."
        
        # Initialize generator
        generator = GeminiImageGenerator(api_key=api_key, model=model)
        
        task.status = "generating"
        task.progress = 30
        task.message = "Generating image..."
        
        # Generate unique output filename
        output_filename = f"generated_{task.task_id}.png"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Generate image
        if input_file_path and os.path.exists(input_file_path):
            task.message = "Generating image with input..."
            result_path = generator.generate_image_with_input(
                input_file_path, prompt, output_path
            )
        else:
            task.message = "Generating image from prompt..."
            result_path = generator.generate_image_from_prompt(
                prompt, output_path
            )
        
        task.status = "completed"
        task.progress = 100
        task.message = "Image generated successfully!"
        task.result_path = result_path
        
        # Clean up input file
        if input_file_path and os.path.exists(input_file_path):
            os.remove(input_file_path)
            
    except Exception as e:
        task.status = "error"
        task.error = str(e)
        task.message = f"Error: {str(e)}"
        
        # Clean up input file on error
        if input_file_path and os.path.exists(input_file_path):
            os.remove(input_file_path)

@app.route('/api/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get status of generation task"""
    if task_id not in active_tasks:
        return jsonify({
            'success': False,
            'error': 'Task not found'
        }), 404
    
    task = active_tasks[task_id]
    
    response = {
        'success': True,
        'task_id': task_id,
        'status': task.status,
        'progress': task.progress,
        'message': task.message
    }
    
    if task.status == "completed" and task.result_path:
        response['download_url'] = f"/api/download/{task_id}"
        response['preview_url'] = f"/api/preview/{task_id}"
    elif task.status == "error":
        response['error'] = task.error
    
    return jsonify(response)

@app.route('/api/download/<task_id>')
def download_image(task_id):
    """Download generated image"""
    if task_id not in active_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = active_tasks[task_id]
    if task.status != "completed" or not task.result_path:
        return jsonify({'error': 'Image not ready'}), 400
    
    if not os.path.exists(task.result_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(task.result_path, as_attachment=True)

@app.route('/api/preview/<task_id>')
def preview_image(task_id):
    """Preview generated image"""
    if task_id not in active_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = active_tasks[task_id]
    if task.status != "completed" or not task.result_path:
        return jsonify({'error': 'Image not ready'}), 400
    
    if not os.path.exists(task.result_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(task.result_path)

@app.route('/api/cleanup/<task_id>', methods=['DELETE'])
def cleanup_task(task_id):
    """Clean up task and associated files"""
    if task_id not in active_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = active_tasks[task_id]
    
    # Remove output file
    if task.result_path and os.path.exists(task.result_path):
        os.remove(task.result_path)
    
    # Remove task from active tasks
    del active_tasks[task_id]
    
    return jsonify({'success': True, 'message': 'Task cleaned up'})

def cleanup_old_tasks():
    """Periodic cleanup of old tasks"""
    current_time = time.time()
    to_remove = []
    
    for task_id, task in active_tasks.items():
        # Remove tasks older than 1 hour
        if hasattr(task, 'created_at'):
            if current_time - task.created_at > 3600:  # 1 hour
                to_remove.append(task_id)
        
        # Clean up completed/error tasks older than 10 minutes
        if task.status in ["completed", "error"]:
            if not hasattr(task, 'finished_at'):
                task.finished_at = current_time
            elif current_time - task.finished_at > 600:  # 10 minutes
                to_remove.append(task_id)
    
    for task_id in to_remove:
        if task_id in active_tasks:
            task = active_tasks[task_id]
            if task.result_path and os.path.exists(task.result_path):
                os.remove(task.result_path)
            del active_tasks[task_id]

# Start cleanup thread
cleanup_thread = threading.Thread(target=lambda: [time.sleep(300), cleanup_old_tasks()])
cleanup_thread.daemon = True
cleanup_thread.start()

if __name__ == '__main__':
    print("Starting Gemini Image Generator Web API...")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)