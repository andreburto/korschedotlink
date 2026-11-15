# Gorsche

Gorsche is a small cross-platform desktop slideshow that displays the images
published at [korsche.link/frame](https://korsche.link/frame/index.json). It
is a Go application built with [`modernc.org/tk9.0`](https://pkg.go.dev/modernc.org/tk9.0),
a CGo-free Tcl/Tk GUI toolkit, so it compiles to a single native binary with
no external Tcl/Tk installation required.

## Overview

On startup, Gorsche:

1. Downloads the list of available images from
   `https://korsche.link/frame/index.json`.
2. Picks a random image from that list and downloads it from
   `https://korsche.link/frame/{image_file}`.
3. Resizes the image to fit the display area, preserving its aspect ratio
   (the ratio is driven by width for wider-than-tall images, and by height
   for taller-than-wide images).
4. Automatically cycles to the next image after a configurable delay.

A `<<<` / `RND` / `>>>` button bar lets you step backward, jump to a random
image, or step forward at any time; doing so resets the automatic cycling
countdown.

```
+-----------------+
|                 |
|   [ display ]   |
|                 |
+-----------------+
|[<<<] [RND] [>>>]|
+-----------------+
```

## Installation

Gorsche requires Go 1.26 or newer (the toolchain directive in `go.mod` will
fetch it automatically if you have a newer `go` command available).

Build it with one of the provided scripts, run from inside this directory:

* Windows: `build.bat` (builds `gorsche.exe` as a GUI app, with no console
  window)
* macOS/Linux: `build.sh` (builds the `gorsche` binary)

Or build it directly with `go build .`.

## Usage

Run the resulting binary. The window opens already showing a random image
and begins cycling automatically.

* `<<<` — show the previous image (wraps to the last image from the first).
* `RND` — show a random image.
* `>>>` — show the next image (wraps to the first image from the last).
* Click the image — open a dialog showing the URL of the displayed picture.
  Its `Copy to clipboard` button copies the URL to the system clipboard and
  its `Close` button dismisses the dialog. The automatic cycling timer keeps
  running while the dialog is open.

### Settings

Gorsche reads `settings.json` from the same directory as the executable. If
the file does not exist, it is created with these defaults:

| Key          | Default | Description                              |
| ------------ | ------- | ----------------------------------------- |
| `delay`      | `30000` | Milliseconds between automatic image changes |
| `app_width`  | `800`   | Window width in pixels                   |
| `app_height` | `600`   | Window height in pixels                  |

Edit `settings.json` and restart Gorsche to apply new values.

## Contributing

This is a small, self-contained Go module living in this directory
(`frame2/`). To work on it:

1. Make your changes to the `.go` files.
2. Run `go build .` and `go vet ./...` from this directory to verify the
   change compiles cleanly.
3. If you add or update dependencies, run `go mod tidy`.
