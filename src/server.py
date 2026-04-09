#!/usr/bin/env python3
"""
Kirsche API Server

Simple API server to handle managing Kirsche images and prompts.
"""

import asyncio
import json
import mimetypes
import os
import sys

from aiohttp import web
from pathlib import Path
from PIL import Image

# Import from korsche_sync module
from korsche_sync import (
    generate_prompt,
    enhance_prompt_with_gemini,
    generate_filename,
    generate_image,
    DEFAULT_GEMINI_PROMPT_MODEL,
    DEFAULT_GEMINI_IMAGE_MODEL
)


# ==============================================================================
# Configuration
# ==============================================================================
def get_config():
    """
    Load configuration from environment variables.
    
    Returns:
        dict: Configuration dictionary
    """
    return {
        'host': os.getenv('HOST', '0.0.0.0'),
        'port': int(os.getenv('PORT', '8080')),
        'image_dir': os.getenv('IMAGE_DIR', 'images'),
        'thumbnail_dir': os.getenv('THUMBNAIL_DIR', 'thumbnails'),
        'static_dir': os.getenv('STATIC_DIR', 'static'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY', ''),
        'gemini_prompt_model': os.getenv('GEMINI_PROMPT_MODEL', DEFAULT_GEMINI_PROMPT_MODEL),
        'gemini_image_model': os.getenv('GEMINI_IMAGE_MODEL', DEFAULT_GEMINI_IMAGE_MODEL),
    }


# ==============================================================================
# Helper Functions
# ==============================================================================
def get_image_files(image_dir):
    """
    Get all image files from the specified directory.
    
    Args:
        image_dir (str): Path to the image directory
        
    Returns:
        list: List of image filenames
    """
    image_dir_path = Path(image_dir)
    if not image_dir_path.exists():
        return []
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    image_files = []
    
    for file_path in image_dir_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(file_path.name)
    
    return sorted(image_files)


async def generate_thumbnail(image_path, thumbnail_path, max_dimension=128):
    """
    Generate a thumbnail for an image.
    
    Args:
        image_path (Path): Path to the original image
        thumbnail_path (Path): Path where the thumbnail should be saved
        max_dimension (int): Maximum dimension (width or height) for the thumbnail
        
    Returns:
        Path: Path to the generated thumbnail
    """
    # Ensure thumbnail directory exists
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Open the image
    with Image.open(image_path) as img:
        # Check if image is smaller than thumbnail dimensions
        if img.width <= max_dimension and img.height <= max_dimension:
            # Just copy the original image as thumbnail
            img.save(thumbnail_path)
            return thumbnail_path
        
        # Calculate new dimensions maintaining aspect ratio
        if img.width > img.height:
            new_width = max_dimension
            new_height = int((max_dimension / img.width) * img.height)
        else:
            new_height = max_dimension
            new_width = int((max_dimension / img.height) * img.width)
        
        # Resize and save thumbnail
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        img_resized.save(thumbnail_path)
    
    return thumbnail_path


# ==============================================================================
# Request Handlers
# ==============================================================================
async def handle_root(request):
    """
    Handle GET / - Serve the index.html file from the static directory.
    
    Args:
        request: aiohttp request object
        
    Returns:
        web.Response: HTML response or error
    """
    config = request.app['config']
    static_dir = Path(config['static_dir'])
    index_path = static_dir / 'index.html'
    
    # Check if index.html exists
    if not index_path.exists() or not index_path.is_file():
        return web.Response(text='index.html not found', status=404)
    
    # Read and return the file
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return web.Response(text=content, content_type='text/html')
    except Exception as e:
        return web.Response(text=f'Error reading index.html: {str(e)}', status=500)


async def handle_static(request):
    """
    Handle GET /static/{filename} - Serve static files.
    
    Args:
        request: aiohttp request object
        
    Returns:
        web.Response: File response or 404 error
    """
    filename = request.match_info['filename']
    config = request.app['config']
    static_dir = Path(config['static_dir'])
    file_path = static_dir / filename
    
    # Security check: ensure the file is within the static directory
    try:
        file_path = file_path.resolve()
        static_dir = static_dir.resolve()
        if not str(file_path).startswith(str(static_dir)):
            return web.Response(text='Forbidden', status=403)
    except Exception:
        return web.Response(text='Bad Request', status=400)
    
    if not file_path.exists() or not file_path.is_file():
        return web.Response(text='File not found', status=404)
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    if content_type is None:
        content_type = 'application/octet-stream'
    
    # Read and return the file
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        return web.Response(body=content, content_type=content_type)
    except Exception as e:
        return web.Response(text=f'Error reading file: {str(e)}', status=500)


async def handle_list_images(request):
    """
    Handle GET /images - Retrieve a paginated list of images.
    
    Args:
        request: aiohttp request object
        
    Returns:
        web.Response: JSON response with paginated image list
    """
    config = request.app['config']
    image_dir = config['image_dir']
    
    # Get pagination parameters
    try:
        page = int(request.query.get('page', 1))
        limit = int(request.query.get('limit', 10))
        
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10
        if limit > 100:  # Max limit to prevent abuse
            limit = 100
    except ValueError:
        return web.Response(
            text=json.dumps({'error': 'Invalid pagination parameters'}),
            status=400,
            content_type='application/json'
        )
    
    # Get all image files
    all_images = get_image_files(image_dir)
    total_images = len(all_images)
    
    # Calculate pagination
    start_index = (page - 1) * limit
    end_index = start_index + limit
    
    # Get the page of images
    page_images = all_images[start_index:end_index]
    
    # Build response
    response_data = {
        'images': [{'name': img} for img in page_images],
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total_images,
            'total_pages': (total_images + limit - 1) // limit
        }
    }
    
    return web.Response(
        text=json.dumps(response_data),
        content_type='application/json'
    )


async def handle_get_image(request):
    """
    Handle GET /images/{image_name} - Retrieve a specific image.
    
    Args:
        request: aiohttp request object
        
    Returns:
        web.Response: Image file response or 404 error
    """
    image_name = request.match_info['image_name']
    config = request.app['config']
    image_dir = Path(config['image_dir'])
    image_path = image_dir / image_name
    
    # Security check
    try:
        image_path = image_path.resolve()
        image_dir = image_dir.resolve()
        if not str(image_path).startswith(str(image_dir)):
            return web.Response(text='Forbidden', status=403)
    except Exception:
        return web.Response(text='Bad Request', status=400)
    
    if not image_path.exists() or not image_path.is_file():
        return web.Response(text='Image not found', status=404)
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(str(image_path))
    if content_type is None:
        content_type = 'application/octet-stream'
    
    # Read and return the image
    try:
        with open(image_path, 'rb') as f:
            content = f.read()
        return web.Response(body=content, content_type=content_type)
    except Exception as e:
        return web.Response(text=f'Error reading image: {str(e)}', status=500)


async def handle_get_thumbnail(request):
    """
    Handle GET /images/{image_name}/thumbnail - Retrieve or generate a thumbnail.
    
    Args:
        request: aiohttp request object
        
    Returns:
        web.Response: Thumbnail image response or error
    """
    image_name = request.match_info['image_name']
    config = request.app['config']
    image_dir = Path(config['image_dir'])
    thumbnail_dir = Path(config['thumbnail_dir'])
    
    image_path = image_dir / image_name
    thumbnail_path = thumbnail_dir / image_name
    
    # Security check for image path
    try:
        image_path = image_path.resolve()
        image_dir = image_dir.resolve()
        if not str(image_path).startswith(str(image_dir)):
            return web.Response(text='Forbidden', status=403)
    except Exception:
        return web.Response(text='Bad Request', status=400)
    
    # Check if original image exists
    if not image_path.exists() or not image_path.is_file():
        return web.Response(text='Image not found', status=404)
    
    # Check if thumbnail already exists
    if not thumbnail_path.exists():
        try:
            # Generate thumbnail
            await generate_thumbnail(image_path, thumbnail_path)
        except Exception as e:
            return web.Response(
                text=f'Error generating thumbnail: {str(e)}',
                status=500
            )
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(str(thumbnail_path))
    if content_type is None:
        content_type = 'application/octet-stream'
    
    # Read and return the thumbnail
    try:
        with open(thumbnail_path, 'rb') as f:
            content = f.read()
        return web.Response(body=content, content_type=content_type)
    except Exception as e:
        return web.Response(
            text=f'Error reading thumbnail: {str(e)}',
            status=500
        )


async def handle_random_prompt(request):
    """
    Handle POST /prompt/random - Generate a random prompt.
    
    Args:
        request: aiohttp request object
        
    Returns:
        web.Response: JSON response with generated prompt
    """
    try:
        prompt = generate_prompt()
        response_data = {'prompt': prompt}
        return web.Response(
            text=json.dumps(response_data),
            content_type='application/json'
        )
    except Exception as e:
        return web.Response(
            text=json.dumps({'error': f'Error generating prompt: {str(e)}'}),
            status=500,
            content_type='application/json'
        )


async def handle_enhance_prompt(request):
    """
    Handle POST /prompt/enhance - Enhance a prompt using Gemini.
    
    Args:
        request: aiohttp request object
        
    Returns:
        web.Response: JSON response with enhanced prompt
    """
    config = request.app['config']
    
    # Check if API key is configured
    if not config['gemini_api_key']:
        return web.Response(
            text=json.dumps({'error': 'GEMINI_API_KEY not configured'}),
            status=500,
            content_type='application/json'
        )
    
    # Parse request body
    try:
        body = await request.json()
        prompt = body.get('prompt')
        
        if not prompt:
            return web.Response(
                text=json.dumps({'error': 'Missing "prompt" field in request body'}),
                status=400,
                content_type='application/json'
            )
    except json.JSONDecodeError:
        return web.Response(
            text=json.dumps({'error': 'Invalid JSON in request body'}),
            status=400,
            content_type='application/json'
        )
    
    # Enhance the prompt
    try:
        enhanced_prompt = enhance_prompt_with_gemini(
            prompt,
            model=config['gemini_prompt_model'],
            api_key=config['gemini_api_key']
        )
        
        response_data = {'enhanced_prompt': enhanced_prompt}
        return web.Response(
            text=json.dumps(response_data),
            content_type='application/json'
        )
    except Exception as e:
        return web.Response(
            text=json.dumps({'error': f'Error enhancing prompt: {str(e)}'}),
            status=500,
            content_type='application/json'
        )


async def handle_submit_prompt(request):
    """
    Handle POST /prompt/submit - Generate a Kirsche image from a prompt.
    
    Args:
        request: aiohttp request object
        
    Returns:
        web.Response: JSON response with image URL
    """
    config = request.app['config']
    
    # Check if API key is configured
    if not config['gemini_api_key']:
        return web.Response(
            text=json.dumps({'error': 'GEMINI_API_KEY not configured'}),
            status=500,
            content_type='application/json'
        )
    
    # Parse request body
    try:
        body = await request.json()
        prompt = body.get('prompt')
        
        if not prompt:
            return web.Response(
                text=json.dumps({'error': 'Missing "prompt" field in request body'}),
                status=400,
                content_type='application/json'
            )
    except json.JSONDecodeError:
        return web.Response(
            text=json.dumps({'error': 'Invalid JSON in request body'}),
            status=400,
            content_type='application/json'
        )
    
    # Generate the image
    try:
        # Generate filename
        filename = generate_filename()
        file_path = os.path.join(config['image_dir'], filename)
        
        # Ensure image directory exists
        os.makedirs(config['image_dir'], exist_ok=True)
        
        # Generate and save the image
        generate_image(
            prompt=prompt,
            save_file=file_path,
            api_key=config['gemini_api_key']
        )
        
        # Build the image URL
        image_url = f"/images/{filename}"
        
        response_data = {'image_url': image_url, 'prompt': prompt}
        return web.Response(
            text=json.dumps(response_data),
            content_type='application/json'
        )
    except Exception as e:
        return web.Response(
            text=json.dumps({'error': f'Error generating image: {str(e)}'}),
            status=500,
            content_type='application/json'
        )


# ==============================================================================
# Application Setup
# ==============================================================================
def create_app(config):
    """
    Create and configure the aiohttp application.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        web.Application: Configured aiohttp application
    """
    app = web.Application()
    app['config'] = config
    
    # Add routes
    app.router.add_get('/', handle_root)
    app.router.add_get('/static/{filename}', handle_static)
    app.router.add_get('/images', handle_list_images)
    app.router.add_get('/images/{image_name}', handle_get_image)
    app.router.add_get('/images/{image_name}/thumbnail', handle_get_thumbnail)
    app.router.add_post('/prompt/random', handle_random_prompt)
    app.router.add_post('/prompt/enhance', handle_enhance_prompt)
    app.router.add_post('/prompt/submit', handle_submit_prompt)
    
    return app


# ==============================================================================
# Main Entry Point
# ==============================================================================
def main():
    """
    Main entry point for the server.
    """
    config = get_config()
    
    print(f"Starting Kirsche API Server...")
    print(f"Host: {config['host']}")
    print(f"Port: {config['port']}")
    print(f"Image Directory: {config['image_dir']}")
    print(f"Thumbnail Directory: {config['thumbnail_dir']}")
    print(f"Static Directory: {config['static_dir']}")
    print(f"Gemini Model: {config['gemini_prompt_model']}")
    
    app = create_app(config)
    web.run_app(app, host=config['host'], port=config['port'])


if __name__ == '__main__':
    main()
