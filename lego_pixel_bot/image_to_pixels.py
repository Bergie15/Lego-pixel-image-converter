from PIL import Image

try:
    from .colors import LEGO_COLORS, EMOJI
except Exception:
    from colors import LEGO_COLORS, EMOJI

def closest_color(pixel):
    """Find the LEGO color closest to a given RGB pixel."""
    return min(
        LEGO_COLORS,
        key=lambda c: sum((pixel[i]-LEGO_COLORS[c][i])**2 for i in range(3))
    )


def image_to_pixel_map(path, size=None, exact_colors=False, color_count=None):
    """
    Convert an image to a pixel map.

    Args:
        path (str): Path to image.
        size (int or None): If int, resize image to size x size.
                            If None, keep original image resolution.
        exact_colors (bool): Preserve original RGB values when True.
        color_count (int or None): Quantize to this many colors before mapping.
    Returns:
        list of lists: RGB tuples or LEGO color codes.
    """
    img = Image.open(path).convert("RGB")
    if size:
        img = img.resize((size, size))

    if exact_colors and color_count and color_count > 1:
        quantized = img.quantize(colors=color_count, method=Image.MEDIANCUT)
        img = quantized.convert("RGB")

    width, height = img.size
    pixels = img.load()

    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            pixel = pixels[x, y]
            if exact_colors:
                row.append(pixel)
            else:
                row.append(closest_color(pixel))
        grid.append(row)
    return grid


def visualize_grid(grid):
    """Print a visual representation of the LEGO grid using emojis."""
    for row in grid:
        print(' '.join(EMOJI[c] for c in row))


def save_pixel_map_py(grid, path="lego_pixel_map.py"):
    """Save the pixel map as a Python file containing `pixel_map`.

    This is handy for exporting to SPIKE MicroPython or other scripts.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write("pixel_map = [\n")
        for row in grid:
            f.write(f" {row},\n")
        f.write("]\n")

