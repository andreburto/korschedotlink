---
applyTo: 'static/*'
description: 'Static files for the Kirsche API server.'
---

# Rules for Static Files

1. All static files should be placed in the directory specified by the `STATIC_DIR` environment variable.
2. `index.html` should be a simple HTML file that serves as the homepage for the API server. It should reference `src/server.py` for the API endpoints and include basic instructions for using the API. The `terraform/index.html` file can be used as a style reference for the design of `static/index.html`.
3. Static files can include CSS, JavaScript, images, and any other assets needed for the frontend of the API server.

# File index.html

1. There should be four sections in the `index.html` file: a header, a menu, a main content area, and a footer in the main content area for the prompt input and buttons.
2. The header and menu should be in a 200px wide sidebar on the left side of the page, and the main content area should take up the remaining space on the right.
3. The header should include the title "Kirsche API Server"
4. The menu should use the `/images` endpoint to display a list of available Kirsche images. Each image should use the `GET /images/{image_name}/thumbnail` endpoint to display a thumbnail, and clicking on the thumbnail should open the full image using the `GET /images/{image_name}` endpoint in a lightbox or new tab. When user scrolls to the bottom of the menu, it should automatically load more images using pagination with the `page` and `limit` query parameters of the `/images` endpoint.
5. The header and menu should be visually distinct, with the header at the top of the sidebar and the menu below it. They should collapse so only the main content area is visible.
6. The footer area should have a text area that is always visible, where users can input a prompt. Below the text area, there should be three buttons: "Generate Random Prompt", "Enhance Prompt with Gemini", and "Submit Prompt". The "Generate Random Prompt" button should call the `POST /prompt/random` endpoint and display the generated prompt in the text area. The "Enhance Prompt with Gemini" button should call the `POST /prompt/enhance` endpoint with the current text in the text area as the prompt to be enhanced, and then update the text area with the enhanced prompt returned from the API. The "Submit Prompt" button should call the `POST /prompt/submit` endpoint with the current text in the text area as the prompt to be submitted. All of this should be aligned to the bottom of the main content area, so it is always visible even when scrolling through content that may appear above it.
7. When the "Submit Prompt" button is clicked, the response from the `POST /prompt/submit` endpoint should be displayed in the main content area. This section should show the generated image based on the submitted prompt, along with the prompt used and a timestamp of when the image was generated above the image. Each new submission should add a new entry to this section, allowing users to see a history of their submitted prompts and generated images. New entries should appear at the bottom of the main content area, pushing older entries up and off screen.
