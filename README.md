# Lego pixel image converter

A small, opinionated toolkit to convert an input image into a LEGO-colour pixel map, preview it as blocky pixel-art, and generate a set of game-targeted asset images across multiple bit-depths.

This repository provides:

- A CLI entrypoint: `lego_pixel_bot/main.py` which discovers an input image, converts it to a grid of LEGO colour codes, prints an emoji preview to the console, simulates a virtual builder, and exports a SPIKE-compatible pixel map.
- A pixel-mapping module (`lego_pixel_bot/image_to_pixels.py`) exposing a simple API you can call from other scripts.
- A compact LEGO colour palette mapping (`lego_pixel_bot/colors.py`) and emoji lookup for a readable console preview.
- A multi-target asset generator that writes palette-quantized and channel-reduced images (1/2/4/8-bit palettes, RGB565 16-bit emulation, 24/32-bit, and best-effort 48/64-bit outputs).

The project is intended to be easy to run locally and useful for creating small pixel-art textures or LEGO build plans from any image.

## Quick start (PowerShell)

1. Create and activate a virtual environment in the repo root (recommended):

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. (Optional) Install numpy if you want true 16-bit-per-channel (48/64-bit) outputs. If you skip this step the script will create 48/64-bit fallback PNGs using 8-bit channels:

```powershell
.venv\Scripts\python.exe -m pip install numpy
```

3. Place an image into the `images/` folder (or pass a path on the CLI) and run:

```powershell
.venv\Scripts\python.exe .\lego_pixel_bot\main.py            # uses first image in images/ by default
.venv\Scripts\python.exe .\lego_pixel_bot\main.py mypic.png  # pass a path instead
```

CLI flags:

- `image` (positional, optional): path to the image to convert. If omitted the script uses the first image in `images/`.
- `--size N` (default 64): resize the image to N x N before conversion. Use `--size 0` or leave unset to skip resizing (not recommended for large inputs).
- `--scale S` (default 8): scale factor for the saved blocky preview PNG (`lego_preview.png`) and generated assets (each logical LEGO pixel becomes SxS pixels in the outputs).

Example:

````powershell
.venv\Scripts\python.exe .\lego_pixel_bot\main.py --size 64 --scale 8
## What the tool does (high level)

- Converts an input image into a N×N pixel grid (default 64×64). Each pixel is quantized to the project's LEGO colour bins.
- Prints an emoji preview to the console (human-friendly quick check).
- Writes a blocky nearest-neighbour preview PNG to the repo root: `lego_preview.png`.
- Generates a set of game-style asset images (palette-quantized and channel-constrained) into `assets/`.
- Writes a color usage CSV `colors_used.txt` to the repo root containing counts and RGBs for every code used.
- Runs a simple virtual build plan (console output) and runs `export_spike.export()` to save a SPIKE-ready pixel_map (see `export_spike.py`).

The generated artifact names and what they mean are explained below.
### Generated assets (files and explanation)

The main script writes multiple asset images into `assets/`. Typical output names and their meanings:

- `lego_preview.png` — nearest-neighbour scaled preview saved in the repo root. Each logical LEGO pixel becomes `--scale`×`--scale` pixels so the preview looks like blocky pixel art.
- `assets/asset_1bit.png` — 1-bit paletted PNG (2 colours using the image quantizer).
- `assets/asset_2bit.png` — 2-bit paletted PNG (4 colours).
- `assets/asset_4bit.png` — 4-bit paletted PNG (16 colours).
- `assets/asset_8bit.png` — 8-bit paletted PNG (up to 256 colours).
- `assets/asset_16bit_rgb565.png` — RGB565 emulation: the image is reduced to 5/6/5 bit components (R,G,B) and expanded back to 8-bit per channel for saving as a PNG. Useful for platforms that expect RGB565 visuals.
- `assets/asset_24bit_rgb888.png` — full 24-bit RGB image.
- `assets/asset_32bit_rgba8888.png` — 32-bit RGBA image with opaque alpha.
- `assets/asset_48bit_rgb16.png` (when numpy present) — 16 bits-per-channel RGB image created using uint16 arrays (true 48-bit). If numpy is missing a fallback file named `asset_48bit_fallback.png` will be written instead.
- `assets/asset_64bit_rgba16.png` (when numpy present) — 16 bits-per-channel RGBA image (true 64-bit). If numpy is missing a fallback file named `asset_64bit_fallback.png` will be written instead.

Note: the script scales each asset by the `--scale` factor when saving so the files are easier to inspect.
## Internals and public API

The repository is small and intentionally simple. Key modules and what they provide:

- `lego_pixel_bot/image_to_pixels.py`
	- image_to_pixel_map(path, size=None): Load an image, optionally resize it to `size x size` (nearest neighbour) and map each pixel to the nearest LEGO colour bin. Returns a list-of-lists grid where each entry is one of the single-letter codes (e.g. `R`, `U`, `Y`, `G`, `W`, `B`).
	- visualize_grid(grid): Print an emoji preview (already used by `main.py`).
	- save_pixel_map_py(grid, path): Dump the pixel map into a small Python file as a variable for later import/use.

- `lego_pixel_bot/colors.py`
	- `LEGO_COLORS`: mapping from single-letter code to RGB tuple (e.g. `{"R": (180,0,0), ...}`)
	- `EMOJI`: mapping from the same single-letter codes to a small emoji useful for console previews.

- `lego_pixel_bot/planner.py`
	- A lightweight planner that simulates picking bricks and placing them to match the pixel map. It prints a sequence of steps to the console and demonstrates how a build order / bin mapping could be implemented. This module intentionally does not control hardware.

- `lego_pixel_bot/export_spike.py`
	- Small exporter that saves a SPIKE-friendly representation of the pixel map. Check that file for exact export format — the `main.py` script calls `export(pixel_map)` after the virtual build simulation.
## colors_used.txt

After a successful run `main.py` writes `colors_used.txt` to the repository root. It is a small CSV with the following columns:

- `code` — the single-letter colour code used in the pixel map.
- `count` — how many pixels in the final map used that code.
- `R,G,B` — the RGB value for the code.
- `emoji` — the console emoji used for preview.

This file is useful to tally bricks or check which colours dominate the image.
## Troubleshooting

- No image found: The script searches for the first image in the `images/` folder (repo-root) if you don't pass an image path. Create `images/` and add a file or pass a path as the first CLI argument.
- Pillow missing / import error: install it via `pip install -r requirements.txt`.
- 48/64-bit assets not created as `rgb16`/`rgba16`: install `numpy` into the venv and re-run (the script will write real uint16 PNGs instead of 8-bit fallback images).
- Bad characters in `colors_used.txt` when viewed in older editors: the file contains emoji; open with a UTF-8 capable editor.

If something else fails, paste the console output and I can help debug.
## Next steps / improvements

Suggested enhancements you can add or I can help with:

- `--no-assets` CLI flag to skip asset generation for faster previews.
- Commit the generated `lego_preview.png` or sample assets into a `examples/` folder for demos.
- Add small unit tests for `image_to_pixel_map` and a CI workflow to validate the tool on push.
- Extend `colors.py` to support a fuller LEGO colour set and add a brick-count CSV generator to estimate part counts.

Contributions welcome — open a PR with improvements or file issues for bugs and feature requests.

---

If you'd like, I can also create a short `USAGE.md` with screenshots of `lego_preview.png` and a sample `colors_used.txt` so it's easier to see what the outputs look like.

Enjoy building!
# Lego-pixel-image-converter

A small utility that converts an image into a LEGO color pixel map, prints a preview, simulates a virtual build, and exports a SPIKE-ready pixel map.

## Prerequisites

- Python 3.8+ installed and available on PATH.
- Place the image you want to convert into the `images/` folder in the repository root (or pass a path as the first argument when running the script). The code will automatically pick the first image it finds in `images/`.

## Setup and run (Windows PowerShell)

Open PowerShell in the repository root (the folder that contains `README.md` and the `lego_pixel_bot` folder), then run:

```powershell
# Create and activate a virtual environment
python -m venv .venv
# Activate the venv in PowerShell
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install pillow

# (Optional) save installed packages for later
pip freeze > requirements.txt

# Run the program from the repository root
python .\lego_pixel_bot\main.py

Examples:

# Use the first image found in the `images/` folder (default size 8x8)
python .\lego_pixel_bot\main.py

# Convert a specific image at 16x16 resolution
python .\lego_pixel_bot\main.py .\images\your-photo.jpg --size 16
````

Notes:

- The project uses Pillow for image processing. If you see "ModuleNotFoundError: No module named 'PIL'", ensure your virtual environment is active and run `pip install pillow`.
- By default the program resizes the target image to 8×8 before mapping pixels; change the `size` argument in `lego_pixel_bot/main.py` to alter the output resolution.
- You can also `cd lego_pixel_bot` and run `python .\main.py` from that directory; both approaches work because the script imports local modules.

## What the program does

- Maps each pixel of the given image to the nearest LEGO color.
- Prints an emoji preview to the console.
- Simulates a virtual build with `planner.build`.
- Exports a SPIKE-ready pixel map via `export_spike.export`.

## Next steps / extras

- I can add a `requirements.txt` and a short usage example to the repo if you'd like.
