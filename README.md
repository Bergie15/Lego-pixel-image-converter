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
```

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
