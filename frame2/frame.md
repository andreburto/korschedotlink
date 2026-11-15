# Frame

## About

This is Golang application that does this following:

1. Downloads a list of files from `https://korsche.link/frame/index.json`
2. Randomly picks an image from the following url pattern: `https://korsche.link/frame/{image_file}`. You will have to remove "frame/" from the list values.
3. Displays the image, resizing it to fit in the display area. If the image is wider than tall, use the width as the deciding factor for the resize ratio. If taller, use the height. Resize the image at a fixed ratio.
4. Randomly cycle through the images based on the `delay` value in a local `settings.json` file. If there's no such file, create it using default values
5. Display the next image in the `index.json` file if the >>> button is pressed. If it's the last image, start at the first. Reset the `delay` countdown.
6. Display the previous image in the `index.json` file if the <<< button is pressed. If it's the the first image, go to the last. Reset the `delay` countdown.
7. Display a random image from `index.json` and reset the `delay` countdown when the RND button is pressed.
8. Display a dialog when the image is clicked. The dialog contains the URL of the picture being displayed and has two buttons: "Copy to clipboard", which copies the URL to the native operating system clipboard, and "Close", which closes the dialog. The dialog must not interrupt the `delay` timer.

The app should compile to a binary and run on modern desktops.

## Default values

The descriptions in parentheses are not to be in the settings file, but are the metrics.

* delay: 30000 (ms)
* app_width: 800 (pixels)
* app_height: 600 (pixels)

## Libraries to use

* modernc.org/tk9.0

## Design

The app should use this layout:

```
+-----------------+
|                 |
|   [ display ]   |
|                 |
+-----------------+
|[<<<] [RND] [>>>]|
+-----------------+
```

## Tools

In addition to the above, create these files:

* `README.md` that explains how the app works.
* `build.bat` builds the app on Windows as a gui app, not console.
* `build.sh` builds the app on Mac and Linhux as a gui app, not console.