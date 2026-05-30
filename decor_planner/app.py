import os
import tempfile
import uuid
from collections import Counter

from flask import Flask, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

try:
    from .colors import EMOJI, PALETTE_COLORS
    from .image_to_pixels import image_to_pixel_map
except Exception:
    from colors import EMOJI, PALETTE_COLORS
    from image_to_pixels import image_to_pixel_map

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IMAGES_DIR = os.path.join(tempfile.gettempdir(), "decor_planner_uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}

SIZE_PRESETS = [
    {"key": "compact", "label": "Compact / entry", "size": 8, "hint": "Smallest, cheapest woodworking art."},
    {"key": "small", "label": "Small / budget", "size": 16, "hint": "Great for coasters, plaques, and simple signs."},
    {"key": "medium", "label": "Medium / balanced", "size": 24, "hint": "Good detail without too much extra work."},
    {"key": "large", "label": "Large / feature", "size": 32, "hint": "Great for wall panels or feature pieces."},
    {"key": "premium", "label": "Premium / detailed", "size": 48, "hint": "Higher detail for larger, more expensive art."},
    {"key": "epic", "label": "Epic / high-detail", "size": 48, "hint": "Max single-sheet 48×96 in plywood; assemble for larger pieces."},
]
PRESET_MAP = {preset["key"]: preset for preset in SIZE_PRESETS}

PLYWOOD_SUGGESTIONS = {
    "compact": "~8×8 in finished (use 12×12 in stock plywood)",
    "small": "~16×16 in finished (use 12×24 or 24×24 plywood)",
    "medium": "~24×24 in finished (use 24×24 or 24×48 plywood)",
    "large": "~32×32 in finished (use 24×48 or larger plywood)",
    "premium": "~48×48 in finished (use 48×96 or assemble from multiple sheets)",
    "epic": "~48×48 in finished (use 48×96 plywood; assemble for larger)",
}

PLYWOOD_DIMENSIONS = {
    "compact": 8,
    "small": 16,
    "medium": 24,
    "large": 32,
    "premium": 48,
    "epic": 48,
}


app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["UPLOAD_FOLDER"] = IMAGES_DIR
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_directories():
    os.makedirs(IMAGES_DIR, exist_ok=True)


@app.route("/output/<path:filename>")
def output_file(filename):
    return send_from_directory(IMAGES_DIR, os.path.basename(filename))


@app.route("/", methods=["GET", "POST"])
def index():
    ensure_directories()
    result = None
    error = None
    size_value = str(PRESET_MAP["medium"]["size"])
    selected_preset = "medium"

    selected_color_count = "8"
    current_image = None
    selected_canvas = str(PLYWOOD_DIMENSIONS.get("medium", 24))

    if request.method == "POST":
        upload_file = request.files.get("upload_image")
        selected_preset = request.form.get("size_preset", "custom")
        size_value = request.form.get("size", size_value)
        selected_color_count = request.form.get("color_count", selected_color_count)
        selected_canvas = request.form.get("canvas_inches", selected_canvas)
        current_image = request.form.get("current_image")

        if selected_preset in PRESET_MAP:
            size_value = str(PRESET_MAP[selected_preset]["size"])
            if not request.form.get("canvas_inches"):
                selected_canvas = str(PLYWOOD_DIMENSIONS.get(selected_preset, PRESET_MAP[selected_preset]["size"]))

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
                if current_image:
                    old_path = os.path.join(IMAGES_DIR, os.path.basename(current_image))
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass
                filename = secure_filename(upload_file.filename)
                unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
                image_path = os.path.join(IMAGES_DIR, unique_name)
                upload_file.save(image_path)
                current_image = unique_name
            else:
                error = "Please upload a supported image file (png, jpg, jpeg, gif, bmp)."
        else:
            if current_image:
                safe_name = os.path.basename(current_image)
                candidate = os.path.join(IMAGES_DIR, safe_name)
                if os.path.exists(candidate):
                    image_path = candidate
                else:
                    error = "Previously uploaded image not found; please upload again."
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

            colors = []
            counts = Counter(code for row in pixel_map for code in row)
            for code, count in counts.most_common():
                if isinstance(code, tuple):
                    rgb = code
                    label = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
                    emoji = ""
                else:
                    rgb = PALETTE_COLORS.get(code, (0, 0, 0))
                    label = code
                    emoji = EMOJI.get(code, "")
                colors.append({
                    "label": label,
                    "rgb": rgb,
                    "hex": f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}",
                    "count": count,
                    "emoji": emoji,
                })

            try:
                canvas_inches = float(selected_canvas)
            except (ValueError, TypeError):
                canvas_inches = float(PLYWOOD_DIMENSIONS.get(selected_preset, size))
            grid_size = len(pixel_map)
            peg_spacing = round(canvas_inches / grid_size, 3) if grid_size else 0

            result = {
                "pixel_grid": [list(row) for row in pixel_map],
                "colors": colors,
                "color_count": len(colors),
                "reduced_colors": color_count,
                "plywood_inches": canvas_inches,
                "peg_spacing": peg_spacing,
            }
            if image_path:
                current_image = os.path.basename(image_path)

    return render_template(
        "index.html",
        result=result,
        error=error,
        selected_size=size_value,
        selected_color_count=selected_color_count,
        selected_preset=selected_preset,
        selected_canvas=selected_canvas,
        size_presets=SIZE_PRESETS,
        PALETTE_COLORS=PALETTE_COLORS,
        preset_hint=(PRESET_MAP[selected_preset]["hint"] if selected_preset in PRESET_MAP else ""),
        preset_plywood=(PLYWOOD_SUGGESTIONS.get(selected_preset, "") if selected_preset else ""),
        current_image=current_image,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
