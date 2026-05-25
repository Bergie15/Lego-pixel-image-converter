# Decor pixel image planner

Convert an input image into a simplified, blocky pixel map for woodworking decor.

Quick start

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Put an image in the `images/` folder (or pass a path) and run the CLI:

```bash
python ./decor_planner/main.py            # uses first image in images/ by default
python ./decor_planner/main.py mypic.png  # pass a path explicitly
```

Run the web UI:

```bash
python ./decor_planner/app.py
# open http://127.0.0.1:5000
```

Main outputs

- `decor_preview.png` — blocky preview saved in the repo root.
- `assets/` — generated bit-depth assets (paletted and reduced-channel images).
- `colors_used.txt` — CSV with color counts and RGB values.

Notes

- Install `numpy` to enable true 48/64-bit asset outputs; otherwise fallback PNGs are written.
- Edit `decor_planner/colors.py` to change palette colors.

If you'd like, I can also:

- rename symbols or files further (e.g. change `PALETTE_COLORS` to `COLORS`),
- remove any remaining style-specific terminology, or
- run a quick test to ensure the web UI and CLI still work in your environment.
