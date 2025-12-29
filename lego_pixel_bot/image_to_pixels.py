from PIL import Image
from colors import LEGO_COLORS, EMOJI

def closest_color(pixel):
    """Find the LEGO color closest to a given RGB pixel."""
    return min(
        LEGO_COLORS,
        key=lambda c: sum((pixel[i]-LEGO_COLORS[c][i])**2 for i in range(3))
    )


def image_to_pixel_map(path, size=None):
    """
    Convert an image to a LEGO-ready pixel map.

    Args:
        path (str): Path to image.
        size (int or None): If int, resize image to size x size.
                            If None, keep original image resolution.
    Returns:
        list of lists: LEGO color codes.
    """
    img = Image.open(path).convert("RGB")
    if size:
        img = img.resize((size, size))
    width, height = img.size
    pixels = img.load()

    lego_grid = []
    for y in range(height):
        row = []
        for x in range(width):
            row.append(closest_color(pixels[x, y]))
        lego_grid.append(row)
    return lego_grid


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

