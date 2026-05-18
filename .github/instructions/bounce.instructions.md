---
applyTo: 'bounce/**'
description: 'Kirsche Cube screensver'
---

# Kirsche Cube Screensaver

This is a single `index.html` file that uses the `kirsche_cube.png` image to create a screensaver effect. The cube will bounce around the screen, changing direction when it hits the edges. The initial position of the cube is at the top-left quarter of the screen, and it will start moving randomly in one of the four diagonal directions (up-right, up-left, down-right, down-left). The cube will continue to bounce indefinitely, creating a dynamic and visually appealing screensaver.

The image is 192x184 pixels. It should be placed in a div tag with the id `cube-container`. The cube will be positioned absolutely within this container, allowing it to move freely around the screen.

Keep everything in a single `index.html` file for simplicity, and ensure that the necessary CSS and JavaScript are included within the same file to achieve the desired bouncing effect.

The background of the screensaver should be #deedee to provide a soft and pleasant backdrop for the bouncing cube. The cube itself should have no shadow or border. Keep the design minimalistic and clean, focusing on the movement of the cube against the subtle background color.

If the div ever enters a corner, post "Munya!" in the console log.
