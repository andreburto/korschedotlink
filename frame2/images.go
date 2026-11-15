package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	_ "image/gif"
	_ "image/jpeg"
	"image/png"
	"io"
	"net/http"
	"strings"

	"github.com/disintegration/imaging"
)

const (
	indexURL     = "https://korsche.link/frame/index.json"
	baseImageURL = "https://korsche.link/frame/"
)

// fetchIndex downloads and parses the list of available image file names.
func fetchIndex(client *http.Client) ([]string, error) {
	resp, err := client.Get(indexURL)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status %s", resp.Status)
	}

	var entries []string
	if err := json.NewDecoder(resp.Body).Decode(&entries); err != nil {
		return nil, fmt.Errorf("could not parse image list: %w", err)
	}
	if len(entries) == 0 {
		return nil, fmt.Errorf("the image list is empty")
	}
	return entries, nil
}

// imageURL builds the download URL for an index.json entry. Entries already
// include a "frame/" prefix, which must be removed before appending the
// remainder to baseImageURL (itself ending in "frame/"), otherwise the path
// segment would be duplicated.
func imageURL(entry string) string {
	file := strings.TrimPrefix(entry, "frame/")
	return baseImageURL + file
}

// fetchImage downloads the raw bytes of a single image.
func fetchImage(client *http.Client, entry string) ([]byte, error) {
	resp, err := client.Get(imageURL(entry))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status %s", resp.Status)
	}
	return io.ReadAll(resp.Body)
}

// resizeToFit decodes raw image bytes and scales them to fit within
// maxW x maxH while preserving the aspect ratio. The image's own orientation
// decides which dimension drives the ratio: a wider-than-tall image is
// scaled from its width, a taller-than-wide image from its height.
func resizeToFit(raw []byte, maxW, maxH int) ([]byte, error) {
	img, _, err := image.Decode(bytes.NewReader(raw))
	if err != nil {
		return nil, fmt.Errorf("could not decode image: %w", err)
	}

	bounds := img.Bounds()
	w, h := fitSize(bounds.Dx(), bounds.Dy(), maxW, maxH)
	resized := imaging.Resize(img, w, h, imaging.Lanczos)

	var buf bytes.Buffer
	if err := png.Encode(&buf, resized); err != nil {
		return nil, fmt.Errorf("could not encode resized image: %w", err)
	}
	return buf.Bytes(), nil
}

// fitSize computes the output dimensions for resizeToFit.
func fitSize(srcW, srcH, maxW, maxH int) (int, int) {
	if srcW <= 0 || srcH <= 0 || maxW <= 0 || maxH <= 0 {
		return maxW, maxH
	}

	var ratio float64
	if srcW >= srcH {
		ratio = float64(maxW) / float64(srcW)
	} else {
		ratio = float64(maxH) / float64(srcH)
	}

	w := int(float64(srcW)*ratio + 0.5)
	h := int(float64(srcH)*ratio + 0.5)
	if w < 1 {
		w = 1
	}
	if h < 1 {
		h = 1
	}
	return w, h
}
