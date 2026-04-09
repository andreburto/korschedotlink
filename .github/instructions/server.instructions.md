---
applyTo: 'src/server.py'
description: 'Simple API server to handle managing Kirsche images.'
---

# Kirsche API Server

## Rules

1. Use the `aiohttp` for asynchronous operations.
2. Use `async` and `await` for all I/O operations to ensure non-blocking behavior.
3. Pillow should be used for image processing tasks, such as resizing and format conversion.
4. Follow PEP 8 style guidelines for Python code.
5. Include docstrings for all functions and classes to explain their purpose and usage.
6. Handle errors gracefully and return appropriate HTTP status codes and messages for different error scenarios.
7. Ensure that the server can handle multiple concurrent requests efficiently.
8. Use environment variables for configuration settings.

## Endpoints

1. `GET /`: redirects to `index.html` in the static directory. This will serve the homepage for the API server, which should include instructions for using the API and a list of available endpoints.
2. `GET /static/{filename}`: Serve static files from a designated `static` directory. The response should include the appropriate content type based on the file extension. If the requested file does not exist, return a 404 error.
3. `GET /images`: Retrieve a list of all available Kirsche images in the IMAGE_DIR directory. The response should be paginated JSON that includes the image name. This endpoint should support query parameters for pagination, such as `page` and `limit`, to control the number of results returned in each response.
4. `GET /images/{image_name}`: Retrieve a specific Kirsche image by name. The response should be the image file itself, with the appropriate content type.
5. `GET /images/{image_name}/thumbnail`: Retrieve a thumbnail of a specific Kirsche image by name. The response should be the thumbnail image file itself, with the appropriate content type. Thumbnails should be generated on-the-fly if they do not already exist, and cached for future requests in the THUMBNAIL_DIR directory. Thumbnail dimensions should be 128 pixels based on which is greater: width or height. Create the directory if it does not exist. If the original image is smaller than the thumbnail dimensions, return the original image as the thumbnail without resizing.
6. `POST /prompt/random`: Generate a random prompt using the `generate_prompt()` function and return it as a JSON response. The response should include the generated prompt in a field named `prompt`.
7. `POST /prompt/enhance`: Enhance a given prompt using the `enhance_prompt_with_gemini(prompt, model, api_key)` function. The request should include a JSON body with a field named `prompt` containing the prompt to be enhanced. The response should include the enhanced prompt in a field named `enhanced_prompt`. Use environment variables to configure the Gemini model and API key for this endpoint. The default Gemini model should be `korsche_sync.DEFAULT_GEMINI_PROMPT_MODEL` if not specified in the environment variables.
8. `POST /prompt/submit`: Submit a prompt to generate a Kirsche image in two steps: (1) geneate a file name with `f"{IMAGE_DIR}/{generate_filename()}` and (2) call `generate_image(prompt, file_path)`. The request should include a JSON body with a field named `prompt` containing the prompt to be submitted. The response should include the generated image in a field named `image_url`, which is the URL where the generated image can be accessed via the `GET /images/{image_name}` endpoint. The server should handle the image generation process, save the generated image to the IMAGE_DIR directory, and return the appropriate URL for accessing the image.

# Environment Variables

1. `GEMINI_API_KEY`: The API key for accessing the Gemini service, used for enhancing prompts in the `/promot/enhance` endpoint.
2. `GEMINI_PROMPT_MODEL`: The specific Gemini model to use for enhancing prompts in the `/promot/enhance` endpoint. If not set, it should default to `korsche_sync.DEFAULT_GEMINI_PROMPT_MODEL`.
3. `IMAGE_DIR`: The directory where Kirsche images are stored. This should be used for retrieving images in the `/images` and `/images/{image_name}` endpoints.
4. `THUMBNAIL_DIR`: The directory where generated thumbnail images are stored. This should be used for caching thumbnails generated in the `/images/{image_name}/thumbnail` endpoint.
5. `STATIC_DIR`: The directory where static files are stored for the `/static/{filename}` endpoint.
6. `HOST`: The host address for the server to listen on. Default should be 0.0.0.0 if not specified.
7. `PORT`: The port number for the server to listen on. Default should be 7777 if not specified.