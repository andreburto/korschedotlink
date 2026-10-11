# Korsche.Link

You ever have a dumb idea, and thanks to a combination of existing code, LLMs, and even worse ideas, it turns into a web site?

Good. Me neither.

Check out https://korsche.link then.

## Random frame prompts

Install the Python dependencies with `pip install -r src/requirements.txt`
and set the `GEMINI_API_KEY` and `XAI_API_KEY` environment variables. Then run:

```bash
python src/frame.py
```

The script selects a random comic-era style and a short setting description,
asks Gemini to describe a person's activity in that setting, and then asks
for a viewpoint of that scene. It prints the completed prompt:

```text
style: Marvel house 2000s

setting: a rooftop garden overlooking a busy city at sunset

scene: A gardener waters the herbs while the city lights begin to glow.

pov: An observer at the garden doorway sees the gardener from the side.
```

The script then sends that prompt and the reference image selected by
`get_reference_image()` to Grok to create a picture of Kirsche. The result
is saved as a PNG in the repository's `images/` directory (relative to the
script, regardless of the working directory), and its path is printed.
Filenames use `frame_{YYMMDDHHmmss}_{uuid}.png`, for example
`frame_261010154150_12345678-1234-4234-8234-123456789abc.png`.

Generation uses two Gemini text requests and one Grok image request.
Missing credentials, API errors, invalid images, and empty responses raise
errors rather than silently falling back.