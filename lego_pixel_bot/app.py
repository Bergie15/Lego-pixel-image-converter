import glob
import os
import uuid
from collections import Counter

from flask import Flask, redirect, render_template, request, send_from_directory, url_for
from PIL import Image
from werkzeug.utils import secure_filename

try:
    from .colors import EMOJI, LEGO_COLORS
    from .export_spike import export
    from .image_to_pixels import image_to_pixel_map
    from .main import create_bitdepth_assets
except Exception:
    from colors import EMOJI, LEGO_COLORS
    from export_spike import export
    from image_to_pixels import image_to_pixel_map
    from main import create_bitdepth_assets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
IMAGES_DIR = os.path.join(REPO_ROOT, "images")
ASSETS_DIR = os.path.join(REPO_ROOT, "assets")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}

SIZE_PRESETS = [
    {"key": "compact", "label": "Compact / entry", "size": 8, "hint": "Smallest, cheapest woodworking art."},
    {"key": "small", "label": "Small / budget", "size": 16, "hint": "Great for coasters, plaques, and simple signs."},
    {"key": "medium", "label": "Medium / balanced", "size": 24, "hint": "Good detail without too much extra work."},
    {"key": "large", "label": "Large / feature", "size": 32, "hint": "Great for wall panels or feature pieces."},
    {"key": "premium", "label": "Premium / detailed", "size": 48, "hint": "Higher detail for larger, more expensive art."},
    {"key": "epic", "label": "Epic / high-detail", "size": 64, "hint": "Best for big, detailed woodworking pieces."},
    {"key": "8bit", "label": "8-bit / NES-style", "size": 16, "hint": "Classic low-detail game art like early Mario."},
    {"key": "16bit", "label": "16-bit / SNES-style", "size": 32, "hint": "Retro pixel art with more colors and detail."},
    {"key": "32bit", "label": "32-bit / arcade", "size": 48, "hint": "Higher-resolution pixel art for stronger detail."},
    {"key": "64bit", "label": "64-bit / modern pixel", "size": 64, "hint": "Detailed pixel art suitable for larger game-style pieces."},
]
PRESET_MAP = {preset["key"]: preset for preset in SIZE_PRESETS}

PLYWOOD_SUGGESTIONS = {
    "compact": "~8×8 in finished (use 12×12 in stock plywood)",
    "small": "~16×16 in finished (use 12×24 or 24×24 plywood)",
    "medium": "~24×24 in finished (use 24×24 or 24×48 plywood)",
    "large": "~32×32 in finished (use 24×48 or larger plywood)",
    "premium": "~48×48 in finished (use 48×96 or assemble from multiple sheets)",
    "epic": "~64×64 in finished (assemble from multiple 48×96 sheets)",
    "8bit": "~16×16 in finished (use 24×24 or 24×48 plywood)",
    "16bit": "~32×32 in finished (use 24×48 or 48×48 plywood)",
    "32bit": "~48×48 in finished (use 48×96 plywood)",
    "64bit": "~64×64 in finished (large - assemble from multiple sheets)",
}

PLYWOOD_DIMENSIONS = {
    "compact": 8,
    "small": 16,
    "medium": 24,
    "large": 32,
    "premium": 48,
    "epic": 64,
    "8bit": 16,
    "16bit": 32,
    "32bit": 48,
    "64bit": 64,
}


app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["UPLOAD_FOLDER"] = IMAGES_DIR
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_directories():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)




def save_colors(pixel_map):
    counts = Counter(code for row in pixel_map for code in row)
    output_path = os.path.join(REPO_ROOT, "colors_used.txt")
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("code,count,R,G,B,emoji\n")
        for code, count in counts.most_common():
            if isinstance(code, tuple):
                rgb = code
                code_label = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
                emoji = ""
            else:
                rgb = LEGO_COLORS.get(code, (0, 0, 0))
                code_label = code
                emoji = EMOJI.get(code, "")
            fh.write(f"{code_label},{count},{rgb[0]},{rgb[1]},{rgb[2]},{emoji}\n")
    return output_path, counts


def asset_list():
    ensure_directories()
    return sorted(os.path.basename(path) for path in glob.glob(os.path.join(ASSETS_DIR, "*")))


@app.route("/output/<path:filename>")
def output_file(filename):
    return send_from_directory(REPO_ROOT, filename)


@app.route("/assets/<path:filename>")
def asset_file(filename):
    return send_from_directory(ASSETS_DIR, filename)


@app.route("/", methods=["GET", "POST"])
def index():
    ensure_directories()
    result = None
    error = None
    size_value = str(PRESET_MAP["medium"]["size"])
    selected_preset = "medium"

    selected_color_count = "8"

    if request.method == "POST":
        upload_file = request.files.get("upload_image")
        selected_preset = request.form.get("size_preset", "custom")
        size_value = request.form.get("size", size_value)
        selected_color_count = request.form.get("color_count", selected_color_count)

        if selected_preset in PRESET_MAP:
            size_value = str(PRESET_MAP[selected_preset]["size"])

        try:
            size = int(size_value)
        except ValueError:
            size = 64
            size_value = "64"

        try:
            color_count = int(selected_color_count)
        except ValueError:
            color_count = 8
            selected_color_count = "8"
        if color_count < 2:
            color_count = 2
            selected_color_count = "2"

        image_path = None
        if upload_file and upload_file.filename:
            if allowed_file(upload_file.filename):
                filename = secure_filename(upload_file.filename)
                unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
                image_path = os.path.join(IMAGES_DIR, unique_name)
                upload_file.save(image_path)
            else:
                error = "Please upload a supported image file (png, jpg, jpeg, gif, bmp)."
        else:
            error = "Please upload an image file."

        if image_path and not error:
            size_arg = size if size > 0 else None
            pixel_map = image_to_pixel_map(
                image_path,
                size=size_arg,
                exact_colors=True,
                color_count=color_count,
            )
            save_colors(pixel_map)
            export(pixel_map, filename=os.path.join(REPO_ROOT, "spike_pixels.txt"))
            create_bitdepth_assets(image_path, size=size_arg, out_dir=ASSETS_DIR, scale=8)

            colors = []
            counts = Counter(code for row in pixel_map for code in row)
            for code, count in counts.most_common():
                if isinstance(code, tuple):
                    rgb = code
                    label = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
                    emoji = ""
                else:
                    rgb = LEGO_COLORS.get(code, (0, 0, 0))
                    label = code
                    emoji = EMOJI.get(code, "")
                colors.append({
                    "label": label,
                    "rgb": rgb,
                    "hex": f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}",
                    "count": count,
                    "emoji": emoji,
                })

            result = {
                "pixel_grid": [list(row) for row in pixel_map],
                "colors": colors,
                "color_count": len(colors),
                "reduced_colors": color_count,
                "plywood_inches": PLYWOOD_DIMENSIONS.get(selected_preset, size) if selected_preset in PLYWOOD_DIMENSIONS else size,
            }

    return render_template(
        "index.html",
        result=result,
        error=error,
        selected_size=size_value,
        selected_color_count=selected_color_count,
        selected_preset=selected_preset,
        size_presets=SIZE_PRESETS,
        LEGO_COLORS=LEGO_COLORS,
        preset_hint=(PRESET_MAP[selected_preset]["hint"] if selected_preset in PRESET_MAP else ""),
        preset_plywood=(PLYWOOD_SUGGESTIONS.get(selected_preset, "") if selected_preset else ""),
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
